"use client";

import {
  FileText,
  MessageSquare,
  FolderOpen,
  Search,
  TrendingUp,
  Clock,
  Upload,
  Brain,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";

const stats = [
  { label: "Documents", value: "0", icon: FileText, color: "text-blue-400" },
  { label: "Workspaces", value: "0", icon: FolderOpen, color: "text-emerald-400" },
  { label: "Conversations", value: "0", icon: MessageSquare, color: "text-violet-400" },
  { label: "Searches", value: "0", icon: Search, color: "text-amber-400" },
];

const quickActions = [
  { label: "Upload Documents", href: "/workspaces", icon: Upload, description: "Add PDFs and text files to your workspace" },
  { label: "Semantic Search", href: "/search", icon: Search, description: "Search across all your documents with AI" },
  { label: "Start Chat", href: "/chat", icon: MessageSquare, description: "Chat with your documents using RAG" },
  { label: "Create Workspace", href: "/workspaces", icon: FolderOpen, description: "Organize documents into projects" },
];

import { useQuery } from "@tanstack/react-query";
import { getSystemSummary, getRecentActivity } from "@/lib/api/analytics";

export default function DashboardPage() {
  const { data: summary } = useQuery({
    queryKey: ["analytics", "summary"],
    queryFn: getSystemSummary,
  });

  const { data: activity } = useQuery({
    queryKey: ["analytics", "activity"],
    queryFn: getRecentActivity,
  });

  const stats = [
    { label: "Documents", value: summary?.total_documents || 0, icon: FileText, color: "text-blue-400" },
    { label: "Workspaces", value: summary?.total_workspaces || 0, icon: FolderOpen, color: "text-emerald-400" },
    { label: "Chunks Extracted", value: summary?.total_chunks || 0, icon: TrendingUp, color: "text-violet-400" },
    { label: "Searches", value: "0", icon: Search, color: "text-amber-400" }, // Mocked until Search API adds history
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto animate-fade-in">
      {/* Welcome Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Welcome to your AI Knowledge OS. Get started by creating a workspace.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Card key={stat.label} className="bg-card/50 border-border/30 hover:border-border/60 transition-all">
            <CardContent className="flex items-center gap-4 p-5">
              <div className={`flex items-center justify-center w-11 h-11 rounded-xl bg-muted/50 ${stat.color}`}>
                <stat.icon className="w-5 h-5" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stat.value}</p>
                <p className="text-sm text-muted-foreground">{stat.label}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action) => (
            <Link key={action.label} href={action.href}>
              <Card className="group bg-card/50 border-border/30 hover:border-primary/30 hover:bg-primary/5 transition-all duration-300 cursor-pointer h-full">
                <CardContent className="p-5">
                  <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-primary/10 text-primary mb-3 group-hover:scale-110 transition-transform">
                    <action.icon className="w-5 h-5" />
                  </div>
                  <h3 className="text-sm font-semibold mb-1">{action.label}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {action.description}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Activity + System Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <Card className="bg-card/50 border-border/30">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Clock className="w-4 h-4 text-muted-foreground" />
              Recent Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            {(() => {
              const safeActivity = Array.isArray(activity) ? activity : [];
              
              if (safeActivity.length === 0) {
                return (
                  <div className="flex flex-col items-center justify-center py-8 text-center">
                    <div className="w-12 h-12 rounded-2xl bg-muted/50 flex items-center justify-center mb-3">
                      <FileText className="w-6 h-6 text-muted-foreground" />
                    </div>
                    <p className="text-sm text-muted-foreground">No recent activity</p>
                    <p className="text-xs text-muted-foreground/60 mt-1">
                      Upload documents to get started
                    </p>
                  </div>
                );
              }

              return (
                <div className="space-y-4">
                  {safeActivity.map((item) => (
                    <div key={item.id} className="flex items-center gap-4">
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{item.name}</p>
                        <p className="text-xs text-muted-foreground">
                          Uploaded • {item.date ? new Date(item.date).toLocaleDateString() : "Unknown date"}
                        </p>
                      </div>
                      <div className="text-xs px-2 py-1 bg-muted rounded-md capitalize">
                        {item.status}
                      </div>
                    </div>
                  ))}
                </div>
              );
            })()}
          </CardContent>
        </Card>

        {/* System Status */}
        <Card className="bg-card/50 border-border/30">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Brain className="w-4 h-4 text-muted-foreground" />
              System Status
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { name: "Backend API", status: "online", color: "bg-emerald-500" },
              { name: "MySQL Database", status: "online", color: "bg-emerald-500" },
              { name: "ChromaDB Vector Store", status: "online", color: "bg-emerald-500" },
              { name: "Ollama LLM Service", status: "checking", color: "bg-amber-500 animate-pulse" },
            ].map((service) => (
              <div
                key={service.name}
                className="flex items-center justify-between py-2"
              >
                <span className="text-sm">{service.name}</span>
                <span className="flex items-center gap-2 text-xs text-muted-foreground capitalize">
                  <span className={`w-2 h-2 rounded-full ${service.color}`} />
                  {service.status}
                </span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
