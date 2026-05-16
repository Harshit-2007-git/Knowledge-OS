"use client";

import { Search as SearchIcon, Sparkles, FileText, Loader2, FolderOpen } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useState, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { searchDocuments, SearchResponse } from "@/lib/api/search";
import api from "@/lib/api";

interface Workspace {
  id: string;
  name: string;
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState<string>("");

  useEffect(() => {
    api.get("/workspaces/").then((res) => {
      setWorkspaces(res.data.items || res.data || []);
      if (res.data.items?.length > 0) setSelectedWorkspace(res.data.items[0].id);
      else if (res.data?.length > 0) setSelectedWorkspace(res.data[0].id);
    }).catch(() => { });
  }, []);

  const searchMutation = useMutation({
    mutationFn: searchDocuments,
    onSuccess: (data) => setResults(data),
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || searchMutation.isPending || !selectedWorkspace) return;
    searchMutation.mutate({ query, workspace_id: selectedWorkspace, top_k: 10 });
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto animate-fade-in pb-10">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Document Search</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Search across your uploaded documents by keyword or topic
        </p>
      </div>

      {/* Workspace selector */}
      {workspaces.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <FolderOpen className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">Search in:</span>
          {workspaces.map((ws) => (
            <button
              key={ws.id}
              onClick={() => setSelectedWorkspace(ws.id)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${selectedWorkspace === ws.id
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-accent"
                }`}
            >
              {ws.name}
            </button>
          ))}
        </div>
      )}

      {/* Search Input */}
      <form onSubmit={handleSearch} className="relative">
        <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
        <Input
          placeholder="Search your documents..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="pl-12 h-14 text-base bg-card/50 border-border/30 focus:border-primary/50 rounded-xl"
        />
        <Button
          type="submit"
          size="sm"
          className="absolute right-2 top-1/2 -translate-y-1/2 gap-1.5"
          disabled={!query.trim() || searchMutation.isPending || !selectedWorkspace}
        >
          {searchMutation.isPending
            ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
            : <Sparkles className="w-3.5 h-3.5" />}
          Search
        </Button>
      </form>

      {/* Results */}
      {searchMutation.isPending ? (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
          <Loader2 className="w-8 h-8 animate-spin mb-4" />
          <p>Searching through documents...</p>
        </div>
      ) : results ? (
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Found <span className="font-medium text-foreground">{results.total_results}</span> results in {results.search_time_ms.toFixed(0)}ms
          </p>
          {results.results.length === 0 ? (
            <Card className="bg-card/50 border-border/30">
              <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                <SearchIcon className="w-8 h-8 text-muted-foreground opacity-20 mb-4" />
                <h3 className="text-lg font-semibold mb-2">No results found</h3>
                <p className="text-sm text-muted-foreground">Try different keywords or upload more documents.</p>
              </CardContent>
            </Card>
          ) : (
            results.results.map((result, i) => (
              <Card key={i} className="bg-card/50 border-border/30 hover:border-primary/30 transition-colors">
                <CardHeader className="py-4 pb-2 flex flex-row items-center justify-between space-y-0">
                  <CardTitle className="text-sm font-medium flex items-center gap-2 text-primary">
                    <FileText className="w-4 h-4" />
                    {result.document_name}
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    {result.page_number && (
                      <Badge variant="outline" className="text-xs">
                        Page {result.page_number}
                      </Badge>
                    )}
                    <Badge variant="secondary" className="text-xs">
                      {(result.relevance_score * 100).toFixed(0)}% match
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="py-4 pt-2">
                  <p className="text-sm leading-relaxed text-foreground/80 bg-muted/30 p-3 rounded-md border border-border/50">
                    ...{result.content}...
                  </p>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      ) : (
        <Card className="bg-card/50 border-border/30">
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
              <SearchIcon className="w-8 h-8 text-primary" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Search your documents</h3>
            <p className="text-sm text-muted-foreground max-w-sm">
              Upload documents to a workspace first, then search by keyword or topic.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}