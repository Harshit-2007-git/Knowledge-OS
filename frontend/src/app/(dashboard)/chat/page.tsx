"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Send, Bot, User, Loader2, ArrowLeft, MessageSquare, Plus, FolderOpen, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getConversation, getConversations, Message } from "@/lib/api/chat";
import { getWorkspaces } from "@/lib/api/workspaces";

export default function ChatPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string | null>(null);
  const [selectedWorkspaceName, setSelectedWorkspaceName] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [currentConvId, setCurrentConvId] = useState<string | undefined>(undefined);
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch workspaces for picker
  const { data: workspaces, isLoading: loadingWorkspaces } = useQuery({
    queryKey: ["workspaces"],
    queryFn: getWorkspaces,
  });

  // Fetch conversations once workspace is selected
  const { data: conversations } = useQuery({
    queryKey: ["conversations", selectedWorkspaceId],
    queryFn: () => getConversations(selectedWorkspaceId!),
    enabled: !!selectedWorkspaceId,
  });

  // Fetch current conversation messages — disabled during streaming
  const { data: conversationData } = useQuery({
    queryKey: ["conversation", currentConvId],
    queryFn: () => getConversation(currentConvId!),
    enabled: !!currentConvId && !isStreaming,
  });

  const isStreamingRef = useRef(false);

  useEffect(() => {
    // Only load messages from server when NOT actively streaming
    if (!isStreamingRef.current && conversationData?.messages) {
      setMessages(conversationData.messages);
    }
  }, [conversationData]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  const handleSelectWorkspace = (id: string, name: string) => {
    setSelectedWorkspaceId(id);
    setSelectedWorkspaceName(name);
    setMessages([]);
    setCurrentConvId(undefined);
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming || !selectedWorkspaceId) return;

    const userMsg = input;
    setInput("");

    const userMessageObj: Message = {
      id: Date.now().toString(),
      role: "user",
      content: userMsg,
      message_index: messages.length,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessageObj]);

    const aiMessageId = (Date.now() + 1).toString();
    setMessages(prev => [...prev, {
      id: aiMessageId,
      role: "assistant",
      content: "",
      message_index: prev.length,
      created_at: new Date().toISOString()
    }]);

    setIsStreaming(true);
    isStreamingRef.current = true;

    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          workspace_id: selectedWorkspaceId,
          message: userMsg,
          conversation_id: currentConvId,
          model_name: "llama3"
        })
      });

      if (!response.ok) throw new Error(`Stream failed: ${response.status}`);

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
                if (data.type === "metadata" && !currentConvId) {
                  setCurrentConvId(data.conversation_id);
                  queryClient.invalidateQueries({ queryKey: ["conversations", selectedWorkspaceId] });
                } else if (data.type === "token") {
                  aiContent += data.content;
                  setMessages(prev =>
                    prev.map(m => m.id === aiMessageId ? { ...m, content: aiContent } : m)
                  );
                }
              } catch {
                // skip malformed SSE lines
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
      isStreamingRef.current = false;
      // Now safe to refresh from server
      if (currentConvId) {
        queryClient.invalidateQueries({ queryKey: ["conversation", currentConvId] });
      }
    }
  };

  const handleDeleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const token = localStorage.getItem("access_token");
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chat/conversations/${id}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${token}` }
    });
    if (currentConvId === id) {
      setCurrentConvId(undefined);
      setMessages([]);
    }
    queryClient.invalidateQueries({ queryKey: ["conversations", selectedWorkspaceId] });
  };
  if (!selectedWorkspaceId) {
    return (
      <div className="flex flex-col h-full max-w-5xl mx-auto animate-fade-in">
        <div className="pb-4">
          <h1 className="text-2xl font-bold tracking-tight">Chat with Knowledge</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Select a workspace to start asking questions about its documents.
          </p>
        </div>

        <div className="flex-1 bg-card/50 border rounded-xl p-8">
          {loadingWorkspaces ? (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
              <Loader2 className="w-8 h-8 animate-spin mb-4" />
              <p>Loading workspaces...</p>
            </div>
          ) : !workspaces || workspaces.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
              <FolderOpen className="w-16 h-16 mb-4 opacity-20" />
              <h3 className="text-lg font-medium text-foreground">No workspaces found</h3>
              <p className="text-sm mt-1 mb-4">Create a workspace and upload documents first.</p>
              <Button onClick={() => router.push("/workspaces")}>Go to Workspaces</Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {workspaces.map((ws: any) => (
                <Card
                  key={ws.id}
                  className="cursor-pointer hover:border-primary/50 transition-colors"
                  onClick={() => handleSelectWorkspace(ws.id, ws.name)}
                >
                  <CardHeader className="p-5">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Bot className="w-5 h-5 text-primary" />
                      {ws.name}
                    </CardTitle>
                  </CardHeader>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // ── Chat UI (shown after workspace selected) ─────────────────────────────
  return (
    <div className="flex h-[calc(100vh-6rem)] border rounded-xl overflow-hidden bg-background shadow-sm animate-fade-in -mx-2 lg:mx-0">

      {/* Sidebar */}
      <div className="w-64 border-r bg-muted/10 hidden md:flex flex-col">
        <div className="p-4 border-b bg-card space-y-2">
          <Button onClick={() => { setSelectedWorkspaceId(null); setMessages([]); }} className="w-full gap-2" variant="ghost" size="sm">
            <ArrowLeft className="w-4 h-4" /> Switch Workspace
          </Button>
          <Button onClick={() => { setCurrentConvId(undefined); setMessages([]); }} className="w-full gap-2" variant="outline">
            <Plus className="w-4 h-4" /> New Chat
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations?.map((conv: any) => (
            <div key={conv.id} className="group flex items-center gap-1">
              <button
                onClick={() => { setCurrentConvId(conv.id); setMessages([]); }}
                className={`flex-1 text-left px-3 py-2 text-sm rounded-md truncate transition-colors flex items-center gap-2 ${currentConvId === conv.id ? "bg-primary/10 text-primary font-medium" : "hover:bg-muted text-muted-foreground"}`}
              >
                <MessageSquare className="w-3.5 h-3.5 shrink-0" />
                {conv.title || "New Conversation"}
              </button>
              <button
                onClick={(e) => handleDeleteConversation(conv.id, e)}
                className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-destructive/10 hover:text-destructive transition-all shrink-0"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
          {conversations?.length === 0 && (
            <p className="p-4 text-xs text-center text-muted-foreground">No previous chats.</p>
          )}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col h-full bg-card relative">
        <div className="p-3 md:p-4 border-b flex items-center gap-3 bg-muted/20">
          <div className="min-w-0">
            <h2 className="font-semibold text-base md:text-lg truncate">
              {selectedWorkspaceName}
            </h2>
            <p className="text-xs text-muted-foreground hidden sm:block">Ask questions about your workspace documents</p>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 bg-background">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-muted-foreground opacity-50">
              <Bot className="w-16 h-16 mb-4" />
              <h3 className="text-xl font-medium">How can I help you today?</h3>
              <p className="text-sm mt-2 text-center max-w-sm">Ask questions about the documents in this workspace.</p>
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