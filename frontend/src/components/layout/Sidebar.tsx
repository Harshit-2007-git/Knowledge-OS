"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/authStore";
import {
  LayoutDashboard,
  FolderOpen,
  Search,
  MessageSquare,
  Settings,
  Upload,
  BarChart3,
  Brain,
  ChevronLeft,
  LogOut,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { useState } from "react";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/workspaces", label: "Workspaces", icon: FolderOpen },
  { href: "/search", label: "Search", icon: Search },
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/settings", label: "Settings", icon: Settings },
];

const secondaryItems = [
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const [collapsed, setCollapsed] = useState(false);

  const initials = user?.full_name
    ?.split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2) || "U";

  return (
    <aside
      className={cn(
        "flex flex-col h-full border-r border-border/50 bg-card/50 backdrop-blur-sm transition-all duration-300",
        collapsed ? "w-[68px]" : "w-[260px]"
      )}
    >
      {/* Logo / Brand */}
      <div className="flex items-center gap-3 px-4 h-16 shrink-0">
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-primary text-primary-foreground animate-pulse-glow">
          <Brain className="w-5 h-5" />
        </div>
        {!collapsed && (
          <div className="animate-fade-in">
            <h1 className="text-sm font-bold tracking-tight gradient-text">
              Knowledge OS
            </h1>
            <p className="text-[10px] text-muted-foreground">Enterprise AI Platform</p>
          </div>
        )}
        <Button
          variant="ghost"
          size="icon"
          className="ml-auto h-7 w-7 text-muted-foreground hover:text-foreground"
          onClick={() => setCollapsed(!collapsed)}
        >
          <ChevronLeft
            className={cn(
              "h-4 w-4 transition-transform duration-300",
              collapsed && "rotate-180"
            )}
          />
        </Button>
      </div>

      <Separator className="opacity-50" />

      {/* Primary Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                "hover:bg-accent/50 hover:text-foreground",
                isActive
                  ? "bg-primary/10 text-primary glow-sm"
                  : "text-muted-foreground"
              )}
            >
              <item.icon className={cn("h-[18px] w-[18px] shrink-0", isActive && "text-primary")} />
              {!collapsed && <span className="animate-fade-in">{item.label}</span>}
            </Link>
          );
        })}

        {!collapsed && (
          <div className="pt-4 pb-2 px-3">
            <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
              Insights
            </span>
          </div>
        )}

        {secondaryItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                "hover:bg-accent/50 hover:text-foreground",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground"
              )}
            >
              <item.icon className="h-[18px] w-[18px] shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      <Separator className="opacity-50" />

      {/* User Section */}
      <div className="px-3 py-3">
        <div
          className={cn(
            "flex items-center gap-3 px-3 py-2 rounded-lg",
            "hover:bg-accent/30 transition-colors cursor-pointer"
          )}
        >
          <Avatar className="h-8 w-8 shrink-0">
            <AvatarFallback className="bg-primary/20 text-primary text-xs font-bold">
              {initials}
            </AvatarFallback>
          </Avatar>
          {!collapsed && (
            <div className="flex-1 min-w-0 animate-fade-in">
              <p className="text-sm font-medium truncate">{user?.full_name || "User"}</p>
              <p className="text-[11px] text-muted-foreground truncate">{user?.email || ""}</p>
            </div>
          )}
          {!collapsed && (
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 shrink-0 text-muted-foreground hover:text-destructive"
              onClick={logout}
            >
              <LogOut className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </aside>
  );
}
