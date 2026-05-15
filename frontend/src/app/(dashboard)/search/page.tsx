"use client";

import { Search as SearchIcon, Sparkles, FileText, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { searchDocuments, SearchResponse } from "@/lib/api/search";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResponse | null>(null);

  const searchMutation = useMutation({
    mutationFn: searchDocuments,
    onSuccess: (data) => {
      setResults(data);
    },
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || searchMutation.isPending) return;
    searchMutation.mutate({ query, top_k: 10 });
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto animate-fade-in pb-10">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Semantic Search</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Search across all your documents using AI-powered semantic understanding
        </p>
      </div>

      {/* Search Input */}
      <form onSubmit={handleSearch} className="relative">
        <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
        <Input
          id="semantic-search"
          placeholder="Ask a question or search across your documents..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="pl-12 h-14 text-base bg-card/50 border-border/30 focus:border-primary/50 focus:glow-sm rounded-xl"
        />
        <Button
          type="submit"
          size="sm"
          className="absolute right-2 top-1/2 -translate-y-1/2 gap-1.5"
          disabled={!query.trim() || searchMutation.isPending}
        >
          {searchMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
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
            Found {results.total_results} results in {results.search_time_ms.toFixed(0)}ms
          </p>
          {results.results.length === 0 ? (
            <Card className="bg-card/50 border-border/30">
              <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                <SearchIcon className="w-8 h-8 text-muted-foreground opacity-20 mb-4" />
                <h3 className="text-lg font-semibold mb-2">No results found</h3>
                <p className="text-sm text-muted-foreground">Try a different search query.</p>
              </CardContent>
            </Card>
          ) : (
            results.results.map((result, i) => (
              <Card key={i} className="bg-card/50 border-border/30 hover:border-primary/30 transition-colors">
                <CardHeader className="py-4 pb-2 flex flex-row items-center justify-between space-y-0">
                  <CardTitle className="text-sm font-medium flex items-center gap-2 text-primary">
                    <FileText className="w-4 h-4" />
                    {result.filename}
                  </CardTitle>
                  <div className="text-xs text-muted-foreground px-2 py-1 bg-muted rounded-full">
                    Score: {(result.score * 100).toFixed(0)}%
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
            <h3 className="text-lg font-semibold mb-2">Search your knowledge base</h3>
            <p className="text-sm text-muted-foreground max-w-sm">
              Type a question or topic to find relevant information across all your uploaded documents.
              Results will be ranked by semantic similarity.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
