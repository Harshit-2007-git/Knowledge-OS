"use client";

import { Settings as SettingsIcon, User, Palette, Shield, Bell, Database, Brain } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";

const settingsSections = [
  { icon: User, label: "Profile", description: "Manage your account details" },
  { icon: Palette, label: "Appearance", description: "Theme and display preferences" },
  { icon: Brain, label: "AI Models", description: "Configure LLM and embedding models" },
  { icon: Database, label: "Data", description: "Storage and export settings" },
  { icon: Shield, label: "Security", description: "Password and access management" },
  { icon: Bell, label: "Notifications", description: "Alert and notification preferences" },
];

import { useAuthStore } from "@/stores/authStore";

export default function SettingsPage() {
  const { user } = useAuthStore();
  
  return (
    <div className="space-y-6 max-w-4xl mx-auto animate-fade-in pb-10">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Manage your account and platform preferences
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-card/50 border-border/30">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <User className="w-4 h-4 text-primary" />
              Profile
            </CardTitle>
            <CardDescription>Update your personal information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Full Name</label>
              <Input defaultValue={user?.full_name || ""} placeholder="Your Name" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Email</label>
              <Input defaultValue={user?.email || ""} disabled />
              <p className="text-xs text-muted-foreground">Email cannot be changed.</p>
            </div>
            <Button>Save Changes</Button>
          </CardContent>
        </Card>

        <Card className="bg-card/50 border-border/30">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Brain className="w-4 h-4 text-primary" />
              AI Models
            </CardTitle>
            <CardDescription>Configure your preferred models</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">LLM Provider</label>
              <select className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50">
                <option>Ollama (Local)</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Default Model</label>
              <Input defaultValue="llama3" />
            </div>
            <Button>Update Configuration</Button>
          </CardContent>
        </Card>
      </div>

      <Separator className="opacity-30" />

      {/* System Info */}
      <Card className="bg-card/50 border-border/30">
        <CardHeader>
          <CardTitle className="text-base">System Information</CardTitle>
          <CardDescription>Current platform configuration</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {[
            { label: "Platform Version", value: "0.1.0" },
            { label: "Backend", value: "FastAPI" },
            { label: "Frontend", value: "Next.js 15" },
            { label: "Database", value: "MySQL 8.0" },
            { label: "Vector Store", value: "ChromaDB" },
            { label: "Embedding Model", value: "all-MiniLM-L6-v2" },
          ].map((item) => (
            <div key={item.label} className="flex items-center justify-between py-1 border-b border-border/10 last:border-0">
              <span className="text-sm text-muted-foreground">{item.label}</span>
              <Badge variant="secondary" className="text-xs font-mono">
                {item.value}
              </Badge>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
