"use client";

import { useState, useRef, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Send, Bot, User, Loader2, ArrowLeft, MessageSquare, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { getConversation, getConversations, Message, Conversation } from "@/lib/api/chat";

export default function ChatPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const workspaceId = params.id as string;
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [currentConvId, setCurrentConvId] = useState<string | undefined>(undefined);
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch all conversations for sidebar
  const { data: conversations } = useQuery({
    queryKey: ["conversations", workspaceId],
    queryFn: () => getConversations(workspaceId),
  });

  // Fetch current conversation messages
  useQuery({
    queryKey: ["conversation", currentConvId],
    queryFn: () => getConversation(currentConvId!),
    enabled: !!currentConvId,
    onSuccess: (data) => {
      if (data.messages) {
        setMessages(data.messages);
      }
    }
  });

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const userMsg = input;
    setInput("");
    
    // Add user message to UI immediately
    const userMessageObj: Message = {
      id: Date.now().toString(),
      role: "user",
      content: userMsg,
      message_index: messages.length,
      created_at: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessageObj]);
    
    // Add empty AI message placeholder
    const aiMessageId = (Date.now() + 1).toString();
    setMessages(prev => [...prev, {
      id: aiMessageId,
      role: "assistant",
      content: "",
      message_index: prev.length,
      created_at: new Date().toISOString()
    }]);

    setIsStreaming(true);

    try {
      const token = localStorage.getItem("auth_token");
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          workspace_id: workspaceId,
          message: userMsg,
          conversation_id: currentConvId,
          model_name: "llama3"
        })
      });

      if (!response.ok) throw new Error("Stream failed");

      const reader = response.body?.getReader();
      const decoder = new TextDecoder("utf-8");
      
      let aiContent = "";
      
      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n\n");
          
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const dataStr = line.replace("data: ", "");
              try {
                const data = JSON.parse(dataStr);
                
                if (data.type === "metadata") {
                  if (!currentConvId) {
                    setCurrentConvId(data.conversation_id);
                    // Refresh sidebar
                    queryClient.invalidateQueries({ queryKey: ["conversations"] });
                  }
                } else if (data.type === "token") {
                  aiContent += data.content;
                  setMessages(prev => 
                    prev.map(m => m.id === aiMessageId ? { ...m, content: aiContent } : m)
                  );
                }
              } catch (e) {
                console.error("Failed to parse SSE", dataStr);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error(error);
      setMessages(prev => 
        prev.map(m => m.id === aiMessageId ? { ...m, content: "[Error generating response]" } : m)
      );
    } finally {
      setIsStreaming(false);
    }
  };

  const handleNewChat = () => {
    setCurrentConvId(undefined);
    setMessages([]);
  };

  const handleSelectChat = (id: string) => {
    if (id !== currentConvId) {
      setCurrentConvId(id);
      setMessages([]); // Cleared before query fetches new data
    }
  };

  return (
    <div className="flex h-[calc(100vh-6rem)] border rounded-xl overflow-hidden bg-background shadow-sm animate-fade-in -mx-2 lg:mx-0">
      
      {/* Sidebar: Conversation History */}
      <div className="w-64 border-r bg-muted/10 hidden md:flex flex-col">
        <div className="p-4 border-b bg-card">
           <Button onClick={handleNewChat} className="w-full gap-2" variant="outline">
             <Plus className="w-4 h-4" /> New Chat
           </Button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations?.map((conv) => (
            <button
              key={conv.id}
              onClick={() => handleSelectChat(conv.id)}
              className={`w-full text-left px-3 py-2 text-sm rounded-md truncate transition-colors flex items-center gap-2 ${currentConvId === conv.id ? "bg-primary/10 text-primary font-medium" : "hover:bg-muted text-muted-foreground"}`}
            >
              <MessageSquare className="w-3.5 h-3.5 shrink-0" />
              {conv.title || "New Conversation"}
            </button>
          ))}
          {conversations?.length === 0 && (
            <div className="p-4 text-xs text-center text-muted-foreground">
              No previous chats in this workspace.
            </div>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full bg-card relative">
        <div className="p-3 md:p-4 border-b flex items-center gap-3 bg-muted/20">
          <Button variant="ghost" size="icon" onClick={() => router.push("/workspaces")} className="shrink-0">
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="min-w-0">
            <h2 className="font-semibold text-base md:text-lg truncate">Knowledge Chat</h2>
            <p className="text-xs text-muted-foreground hidden sm:block">Ask questions about your workspace documents</p>
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 custom-scrollbar bg-background">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-muted-foreground opacity-50">
              <Bot className="w-16 h-16 mb-4" />
              <h3 className="text-xl font-medium">How can I help you today?</h3>
              <p className="text-sm mt-2 text-center max-w-sm">I can search through your uploaded documents and provide answers using context from your workspace.</p>
            </div>
          ) : (
            messages.map((msg, i) => (
              <div key={msg.id || i} className={`flex gap-3 md:gap-4 max-w-[90%] md:max-w-[80%] ${msg.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted border"}`}>
                  {msg.role === "user" ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
                </div>
                <Card className={`border-none shadow-sm ${msg.role === "user" ? "bg-primary text-primary-foreground rounded-tr-none" : "bg-muted/50 rounded-tl-none"}`}>
                  <CardContent className="p-3 md:p-4 text-sm leading-relaxed whitespace-pre-wrap">
                    {msg.content || (isStreaming && msg.role === "assistant" ? <span className="animate-pulse">...</span> : "")}
                  </CardContent>
                </Card>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
        
        <div className="p-3 md:p-4 bg-card border-t">
          <form onSubmit={handleSend} className="relative flex items-center">
            <Input 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about your documents..."
              className="pr-12 h-12 bg-background border-muted"
              disabled={isStreaming}
            />
            <Button 
              type="submit" 
              size="icon" 
              className="absolute right-1.5 h-9 w-9 rounded-md" 
              disabled={!input.trim() || isStreaming}
            >
              {isStreaming ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </Button>
          </form>
          <p className="text-[10px] text-center text-muted-foreground mt-2">
            AI can make mistakes. Consider verifying important information.
          </p>
        </div>
      </div>
    </div>
  );
}
