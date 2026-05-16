"use client";

import { useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { FolderOpen, Plus, FileText, UploadCloud, Loader2, Trash2, Bot } from "lucide-react";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { cn } from "@/lib/utils";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { getWorkspaces, createWorkspace, deleteWorkspace, Workspace } from "@/lib/api/workspaces";
import { getDocuments, uploadDocument, deleteDocument, Document as DocType } from "@/lib/api/documents";
import { formatDistanceToNow } from "date-fns";

export default function WorkspacesPage() {
  const queryClient = useQueryClient();
  const [selectedWorkspace, setSelectedWorkspace] = useState<Workspace | null>(null);
  const [newWorkspaceName, setNewWorkspaceName] = useState("");
  const [newWorkspaceDesc, setNewWorkspaceDesc] = useState("");
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  // Queries
  const { data: workspaces, isLoading: loadingWorkspaces } = useQuery({
    queryKey: ["workspaces"],
    queryFn: getWorkspaces,
  });

  const { data: documentData, isLoading: loadingDocs, refetch: refetchDocs } = useQuery({
    queryKey: ["documents", selectedWorkspace?.id],
    queryFn: () => getDocuments(selectedWorkspace!.id),
    enabled: !!selectedWorkspace,
    refetchInterval: 3000, // Poll every 3s to get status updates
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: createWorkspace,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
      setIsDialogOpen(false);
      setNewWorkspaceName("");
      setNewWorkspaceDesc("");
    },
  });

  const uploadMutation = useMutation({
    mutationFn: ({ workspaceId, file }: { workspaceId: string; file: File }) =>
      uploadDocument(workspaceId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents", selectedWorkspace?.id] });
    },
    onError: (err: any) => {
      console.error("Upload failed:", err);
      const detail = err.response?.data?.detail;
      const message = typeof detail === "string"
        ? detail
        : JSON.stringify(detail) || "Failed to upload document. Please check file size and type.";
      alert(message);
    }
  });

  const deleteDocMutation = useMutation({
    mutationFn: (id: string) => deleteDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents", selectedWorkspace?.id] });
      queryClient.invalidateQueries({ queryKey: ["analytics", "summary"] });
    },
  });

  const deleteWorkspaceMutation = useMutation({
    mutationFn: deleteWorkspace,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
      if (selectedWorkspace) {
        setSelectedWorkspace(null);
      }
    },
  });

  const handleDeleteWorkspace = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirm("Are you sure you want to delete this workspace and all its documents?")) {
      deleteWorkspaceMutation.mutate(id);
    }
  };

  const handleFileDelete = (id: string) => {
    if (confirm("Are you sure you want to delete this document? This will also remove its embeddings.")) {
      deleteDocMutation.mutate(id);
    }
  };

  // Handlers
  const handleCreateWorkspace = () => {
    if (!newWorkspaceName.trim()) return;
    createMutation.mutate({ name: newWorkspaceName, description: newWorkspaceDesc });
  };

  const handleFileUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !e.target.files.length || !selectedWorkspace) return;
    const file = e.target.files[0];
    uploadMutation.mutate({ workspaceId: selectedWorkspace.id, file });
  }, [selectedWorkspace, uploadMutation]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed": return <Badge className="bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20">Ready</Badge>;
      case "processing": return <Badge className="bg-blue-500/10 text-blue-500 hover:bg-blue-500/20"><Loader2 className="w-3 h-3 mr-1 animate-spin" /> Processing</Badge>;
      case "failed": return <Badge variant="destructive">Failed</Badge>;
      default: return <Badge variant="outline">Pending</Badge>;
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fade-in flex flex-col md:flex-row gap-6 h-[calc(100vh-8rem)]">

      {/* Sidebar: Workspaces List */}
      <div className="w-full md:w-1/3 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-tight">Workspaces</h1>
          </div>

          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-9 px-3 gap-2">
              <Plus className="w-4 h-4" />
              New
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
              <DialogHeader>
                <DialogTitle>Create Workspace</DialogTitle>
                <DialogDescription>
                  Organize documents into isolated projects.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    value={newWorkspaceName}
                    onChange={(e) => setNewWorkspaceName(e.target.value)}
                    placeholder="e.g. HR Policies 2024"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="desc">Description</Label>
                  <Input
                    id="desc"
                    value={newWorkspaceDesc}
                    onChange={(e) => setNewWorkspaceDesc(e.target.value)}
                    placeholder="Optional details"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button disabled={createMutation.isPending || !newWorkspaceName.trim()} onClick={handleCreateWorkspace}>
                  {createMutation.isPending ? "Creating..." : "Create Workspace"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
          {loadingWorkspaces ? (
            <div className="flex justify-center p-8"><Loader2 className="w-6 h-6 animate-spin text-muted-foreground" /></div>
          ) : workspaces?.length === 0 ? (
            <Card className="bg-card/50 border-border/30 border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-10 text-center">
                <FolderOpen className="w-8 h-8 text-muted-foreground mb-3" />
                <p className="text-sm text-muted-foreground">No workspaces yet</p>
              </CardContent>
            </Card>
          ) : (
            workspaces?.map((ws) => (
              <Card
                key={ws.id}
                className={`cursor-pointer transition-all group ${selectedWorkspace?.id === ws.id ? 'border-primary ring-1 ring-primary/50 bg-primary/5' : 'hover:border-primary/50'}`}
                onClick={() => setSelectedWorkspace(ws)}
              >
                <CardHeader className="p-4 flex flex-row items-center justify-between space-y-0">
                  <div className="space-y-1">
                    <CardTitle className="text-base flex items-center gap-2">
                      <FolderOpen className="w-4 h-4 text-primary" />
                      {ws.name}
                    </CardTitle>
                    {ws.description && <CardDescription className="text-xs line-clamp-1">{ws.description}</CardDescription>}
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => handleDeleteWorkspace(e, ws.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </CardHeader>
              </Card>
            ))
          )}
        </div>
      </div>

      {/* Main Content: Documents & Upload */}
      <div className="w-full md:w-2/3 border rounded-xl bg-card overflow-hidden flex flex-col">
        {!selectedWorkspace ? (
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-muted-foreground">
            <FileText className="w-12 h-12 mb-4 opacity-20" />
            <h3 className="text-lg font-medium text-foreground">Select a workspace</h3>
            <p className="text-sm mt-1">Choose a workspace from the sidebar to manage its documents.</p>
          </div>
        ) : (
          <>
            <div className="p-6 border-b flex justify-between items-center bg-muted/20">
              <div>
                <h2 className="text-lg font-bold">{selectedWorkspace.name}</h2>
                <p className="text-sm text-muted-foreground">{documentData?.total || 0} documents</p>
              </div>
              <div className="flex items-center gap-3">
                <Link
                  href={`/workspaces/${selectedWorkspace.id}/chat`}
                  className={cn(buttonVariants({ variant: "outline", size: "sm" }), "gap-2")}
                >
                  <Bot className="size-4" />
                  Chat
                </Link>
                <input
                  type="file"
                  id="file-upload"
                  className="hidden"
                  accept=".pdf,.txt,.md,.docx"
                  onChange={handleFileUpload}
                  disabled={uploadMutation.isPending}
                />
                <Label htmlFor="file-upload" className="cursor-pointer">
                  <div className={cn(buttonVariants({ variant: "default", size: "sm" }), "gap-2")}>
                    {uploadMutation.isPending ? <Loader2 className="size-4 animate-spin" /> : <UploadCloud className="size-4" />}
                    Upload File
                  </div>
                </Label>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
              {loadingDocs ? (
                <div className="flex justify-center p-8"><Loader2 className="w-6 h-6 animate-spin text-muted-foreground" /></div>
              ) : documentData?.documents.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-center border-2 border-dashed border-border/50 rounded-xl bg-background/50">
                  <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                    <UploadCloud className="w-8 h-8 text-primary" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">Upload your first document</h3>
                  <p className="text-sm text-muted-foreground max-w-sm">
                    Drag and drop a PDF, TXT, Markdown, or Word (.docx) file here, or click the upload button above.
                  </p>
                </div>
              ) : (
                <div className="grid gap-3">
                  {documentData?.documents.map((doc) => (
                    <Card key={doc.id} className="bg-card/50 shadow-sm hover:shadow transition-all group">
                      <CardContent className="p-4 flex items-center justify-between">
                        <div className="flex items-center gap-3 overflow-hidden">
                          <div className="p-2 bg-primary/10 rounded-lg shrink-0">
                            <FileText className="w-5 h-5 text-primary" />
                          </div>
                          <div className="truncate">
                            <h4 className="font-medium text-sm truncate">{doc.original_filename}</h4>
                            <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                              <span>{(doc.file_size / 1024).toFixed(1)} KB</span>
                              <span>•</span>
                              <span>{formatDistanceToNow(new Date(doc.created_at), { addSuffix: true })}</span>
                              {doc.chunk_count > 0 && (
                                <>
                                  <span>•</span>
                                  <span>{doc.chunk_count} chunks</span>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-3 shrink-0">
                          {getStatusBadge(doc.status)}
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity"
                            onClick={() => handleFileDelete(doc.id)}
                            disabled={deleteDocMutation.isPending}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                          {doc.error_message && (
                            <span className="text-xs text-destructive max-w-[150px] truncate" title={doc.error_message}>
                              {doc.error_message}
                            </span>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}