"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BarChart3, Database, HardDrive, Files, TrendingUp, Loader2, Tags, FolderOpen } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { getSystemSummary, getWorkspaceClusters } from "@/lib/api/analytics";
import { getWorkspaces } from "@/lib/api/workspaces";
import { Badge } from "@/components/ui/badge";

export default function AnalyticsPage() {
  const [selectedWorkspace, setSelectedWorkspace] = useState<string>("");

  const { data: summary, isLoading: isLoadingSummary } = useQuery({
    queryKey: ["analytics", "summary"],
    queryFn: getSystemSummary,
  });

  const { data: workspaces } = useQuery({
    queryKey: ["workspaces"],
    queryFn: getWorkspaces,
  });

  const { data: clusters, isLoading: isLoadingClusters } = useQuery({
    queryKey: ["analytics", "clusters", selectedWorkspace],
    queryFn: () => getWorkspaceClusters(selectedWorkspace),
    enabled: !!selectedWorkspace,
  });

  const totalChunks = summary?.total_chunks || 0;
  // Estimate 1.5KB per chunk
  const storageUsedMB = (totalChunks * 1.5) / 1024;
  const storageLimitMB = 100;
  const storagePercentage = Math.min((storageUsedMB / storageLimitMB) * 100, 100);

  return (
    <div className="space-y-8 max-w-7xl mx-auto animate-fade-in pb-10">
      <div>
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <BarChart3 className="w-8 h-8 text-primary" />
          Analytics & Usage
        </h1>
        <p className="text-muted-foreground mt-1">
          Monitor your workspace usage, storage limits, and processing metrics.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-card/50 border-border/30">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <HardDrive className="w-4 h-4" />
              Vector Storage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold">{storageUsedMB.toFixed(2)}</span>
              <span className="text-sm text-muted-foreground">MB / {storageLimitMB} MB</span>
            </div>
            <div className="mt-4 h-2 w-full bg-muted rounded-full overflow-hidden">
              <div 
                className="h-full bg-primary transition-all duration-500" 
                style={{ width: `${storagePercentage}%` }}
              />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/50 border-border/30">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Database className="w-4 h-4" />
              Total Chunks
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold">{isLoadingSummary ? "-" : totalChunks}</span>
              <span className="text-sm text-muted-foreground">vectors indexed</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/50 border-border/30">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Files className="w-4 h-4" />
              Ingested Documents
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold">{isLoadingSummary ? "-" : summary?.total_documents || 0}</span>
              <span className="text-sm text-muted-foreground">files</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Advanced Analytics - Clusters */}
      <Card className="bg-card/50 border-border/30 min-h-[300px]">
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-primary" />
                Document Clustering
              </CardTitle>
              <CardDescription>AI automatically groups related documents using K-Means and TF-IDF.</CardDescription>
            </div>
            
            <div className="w-full sm:w-64">
              <select 
                className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                value={selectedWorkspace}
                onChange={(e) => setSelectedWorkspace(e.target.value)}
              >
                <option value="" disabled>Select a workspace</option>
                {workspaces?.map((w) => (
                  <option key={w.id} value={w.id}>{w.name}</option>
                ))}
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {!selectedWorkspace ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FolderOpen className="w-12 h-12 text-muted-foreground opacity-20 mb-4" />
              <p className="text-muted-foreground">Select a workspace above to view its document clusters.</p>
            </div>
          ) : isLoadingClusters ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-muted-foreground mb-4" />
              <p className="text-sm text-muted-foreground">Running K-Means Clustering on documents...</p>
            </div>
          ) : !clusters || clusters.length === 0 ? (
             <div className="flex flex-col items-center justify-center py-12 text-center">
              <Tags className="w-12 h-12 text-muted-foreground opacity-20 mb-4" />
              <p className="text-muted-foreground">Not enough documents to form clusters (needs at least 2).</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
              {clusters.map((cluster) => (
                <Card key={cluster.cluster_id} className="bg-background/50 border-border/50">
                  <CardHeader className="py-3 px-4 bg-muted/20 border-b border-border/30">
                    <CardTitle className="text-sm flex items-center justify-between">
                      <span>{cluster.label}</span>
                      <Badge variant="secondary">{cluster.document_ids.length} docs</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-4 space-y-4">
                    <div>
                      <p className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wider">Top Keywords</p>
                      <div className="flex flex-wrap gap-1.5">
                        {cluster.keywords.map(kw => (
                          <span key={kw} className="text-[11px] px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
                            {kw}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                       <p className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wider">Documents</p>
                       <ul className="text-xs space-y-1 list-disc pl-4 text-muted-foreground">
                         {cluster.document_names.map((name, i) => (
                           <li key={i} className="truncate">{name}</li>
                         ))}
                       </ul>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
