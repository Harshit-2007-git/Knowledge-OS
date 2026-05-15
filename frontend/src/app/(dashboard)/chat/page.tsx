"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { Bot, FolderOpen, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { getWorkspaces } from "@/lib/api/workspaces";

export default function GlobalChatPage() {
  const router = useRouter();
  
  const { data: workspaces, isLoading } = useQuery({
    queryKey: ["workspaces"],
    queryFn: getWorkspaces,
  });

  return (
    <div className="flex flex-col h-full max-w-5xl mx-auto animate-fade-in">
      <div className="flex items-center justify-between pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Chat with Knowledge</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Select a workspace to start asking questions about its documents.
          </p>
        </div>
      </div>

      <div className="flex-1 bg-card/50 border-border/30 flex flex-col overflow-hidden rounded-xl border p-8">
        {isLoading ? (
          <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground">
            <Loader2 className="w-8 h-8 animate-spin mb-4" />
            <p>Loading your workspaces...</p>
          </div>
        ) : !workspaces || workspaces.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground">
            <FolderOpen className="w-16 h-16 mb-4 opacity-20" />
            <h3 className="text-lg font-medium text-foreground">No workspaces found</h3>
            <p className="text-sm mt-1 mb-4">You need to create a workspace and upload documents first.</p>
            <button 
              onClick={() => router.push("/workspaces")}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium"
            >
              Go to Workspaces
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {workspaces.map((ws) => (
              <Card 
                key={ws.id} 
                className="cursor-pointer hover:border-primary/50 transition-colors"
                onClick={() => router.push(`/workspaces/${ws.id}/chat`)}
              >
                <CardHeader className="p-5">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Bot className="w-5 h-5 text-primary" />
                    {ws.name}
                  </CardTitle>
                  {ws.description && (
                    <CardDescription className="line-clamp-2 mt-2">
                      {ws.description}
                    </CardDescription>
                  )}
                </CardHeader>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
