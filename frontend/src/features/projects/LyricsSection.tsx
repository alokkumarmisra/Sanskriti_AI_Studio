/** Lyrics section component for Project Detail page. */

import React, { useState } from "react";
import type { Project } from "../../types/project";
import { useProjectLyricsQuery, useCreateLyricsMutation, useUpdateLyricsMutation, useDeleteLyricsMutation } from "../../api/lyrics";

/** API response types for lyrics (from backend) */
interface LyricsApiResponse {
  id: string;
  project_id?: string;
  title: string | null;
  content: string;
  language: string | null;
  status: string;
  created_at?: string;
  updated_at?: string;
}

/** Frontend display type for lyrics */
interface DisplayLyrics {
  id: string;
  projectId: string;
  title: string | null;
  content: string;
  language: string | null;
  status: string;
  createdAt: string;
  updatedAt: string;
}

/** Lyrics form dialog component. */
function LyricsFormDialog({ 
  open, 
  onOpenChange, 
  lyrics, 
  projectId,
  onSave 
}: { 
  open: boolean; 
  onOpenChange: (open: boolean) => void;
  lyrics?: LyricsApiResponse | null;
  projectId: string;
  onSave: (lyricsData: Omit<LyricsApiResponse, "id" | "projectId" | "createdAt" | "updatedAt">) => void;
}) {

  interface FormState {
    title: string | null;
    content: string;
    language: string | null;
    status: string;
  }
  const [title, setTitle] = useState(lyrics?.title || "");
  const [content, setContent] = useState(lyrics?.content || "");
  const [language, setLanguage] = useState(lyrics?.language || "English");
  const [status, setStatus] = useState(lyrics?.status || "draft");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({ title, content, language, status });
    setTitle("");
    setContent("");
    setLanguage("English");
    setStatus("draft");
  };

  return (
    open && (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => onOpenChange(false)}>
        <div className="bg-white border rounded-lg shadow-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">{lyrics ? "Edit Lyrics" : "Add Lyrics"}</h2>
            <button
              onClick={() => onOpenChange(false)}
              className="p-2 hover:bg-muted rounded-md transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Optional title for this lyrics entry"
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Content</label>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Enter the lyrics content here..."
                rows={10}
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50 font-mono text-sm"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Language</label>
                <input
                  type="text"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50 capitalize"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Status</label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50 capitalize"
                >
                  <option value="draft">Draft</option>
                  <option value="active">Active</option>
                </select>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-4 border-t">
              <button
                type="button"
                onClick={() => onOpenChange(false)}
                className="px-4 py-2 border rounded-md hover:bg-secondary transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-add text-white font-medium rounded-md hover:bg-add-hover transition-colors"
              >
                {lyrics ? "Save Changes" : "Add Lyrics"}
              </button>
            </div>
          </form>
        </div>
      </div>
    )
  );
}

/** Lyrics entry component for display. */
function LyricsEntry({ lyrics, onEdit, onDelete }: { lyrics: DisplayLyrics; onEdit: (lyrics: DisplayLyrics) => void; onDelete: (id: string) => void }) {
  const getStatusColorClass = (status: string) => {
    switch (status.toLowerCase()) {
      case "draft": return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300";
      case "active": return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300";
      default: return "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300";
    }
  };

  const getStatusText = (status: string) => {
    switch (status.toLowerCase()) {
      case "draft": return "Draft";
      case "active": return "Active";
      default: return status.charAt(0).toUpperCase() + status.slice(1);
    }
  };

  return (
    <div className="border rounded-lg bg-card p-4 space-y-3">
      <div className="flex items-start justify-between gap-2">
        {lyrics.title && (
          <h4 className="font-semibold text-base truncate flex-1">{lyrics.title || "Untitled"}</h4>
        )}
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${getStatusColorClass(lyrics.status)}`}>
          {getStatusText(lyrics.status)}
        </span>
      </div>

      <p className="text-muted-foreground text-sm whitespace-pre-wrap font-mono leading-relaxed">
        {lyrics.content || "No content"}
      </p>

      <div className="flex items-center justify-between pt-2 border-t">
        <span className="text-xs text-muted-foreground">
          {lyrics.language && <span className="text-gray-500">{lyrics.language}</span>}
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => onEdit(lyrics)}
            className="p-2 hover:bg-muted rounded-md transition-colors"
            title="Edit lyrics"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />
            </svg>
          </button>
          <button
            onClick={() => onDelete(lyrics.id)}
            className="p-2 hover:bg-destructive/10 rounded-md transition-colors text-destructive"
            title="Delete lyrics"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M5 7h14M5 7v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7m-9 4h4" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

/** Lyrics section component for the Project Detail page. */
export function LyricsSection({ projectId }: { projectId: string }) {
  const [isAddFormOpen, setIsAddFormOpen] = useState(false);
  const [editingLyrics, setEditingLyrics] = useState<DisplayLyrics | null>(null);
  
  // Use useProjectLyricsQuery to list ALL lyrics for the project
  const lyricsQuery = useProjectLyricsQuery(projectId || "");
  const createMutation = useCreateLyricsMutation();
  const updateMutation = useUpdateLyricsMutation();
  const deleteMutation = useDeleteLyricsMutation();

  // Format lyrics for display - map snake_case from API to frontend-friendly format
  const formatLyricsForDisplay = (lyric: LyricsApiResponse): DisplayLyrics => ({
    id: lyric.id,
    projectId: lyric.project_id || projectId,
    title: lyric.title ?? null,
    content: lyric.content,
    language: lyric.language ?? null,
    status: lyric.status,
    createdAt: lyric.created_at || new Date().toISOString(),
    updatedAt: lyric.updated_at || new Date().toISOString(),
  });

  const handleAddLyrics = async (lyricsData: Omit<LyricsApiResponse, "id" | "projectId" | "createdAt" | "updatedAt">) => {
    if (!projectId) return;
    try {
      await createMutation.mutateAsync({
        projectId,
        content: lyricsData.content,
        title: lyricsData.title || null,
        language: lyricsData.language || "English",
      });
      setIsAddFormOpen(false);
      lyricsQuery.refetch();
    } catch (error) {
      console.error("Failed to create lyrics:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to create lyrics";
      alert(errorMessage);
    }
  };

  const handleEditLyrics = async (lyric: LyricsApiResponse, updatedData: Omit<LyricsApiResponse, "id" | "projectId" | "createdAt" | "updatedAt">) => {
    if (!lyric.id) return;
    try {
      // Build payload with optional fields only if they have values
      const payload: Record<string, string> = {};
      if (updatedData.title != null) {
        payload.title = updatedData.title;
      }
      if (updatedData.content != null) {
        payload.content = updatedData.content;
      }
      if (updatedData.language != null) {
        payload.language = updatedData.language;
      }
      if (updatedData.status != null) {
        payload.status = updatedData.status;
      }
      
      await updateMutation.mutateAsync({
        id: lyric.id,
        payload,
      });
      setEditingLyrics(null);
      lyricsQuery.refetch();
    } catch (error) {
      console.error("Failed to update lyrics:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to update lyrics";
      alert(errorMessage);
    }
  };

  const handleDeleteLyrics = async (lyricsId: string) => {
    try {
      await deleteMutation.mutateAsync(lyricsId);
      lyricsQuery.refetch();
    } catch (error) {
      console.error("Failed to delete lyrics:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to delete lyrics";
      alert(errorMessage);
    }
  };

  const handleOpenEdit = (lyrics: LyricsApiResponse) => {
    setEditingLyrics(formatLyricsForDisplay(lyrics));
  };

  const handleCloseEdit = () => {
    setEditingLyrics(null);
  };

  return (
    <>
      <div className="border rounded-lg bg-card space-y-4">
        {/* Section Header */}
        <div className="p-4 border-b flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">Lyrics</h2>
            <p className="text-sm text-muted-foreground">Manage lyrics entries for this project</p>
          </div>
          <button
            onClick={() => setIsAddFormOpen(true)}
            disabled={lyricsQuery.isLoading}
            className="px-4 py-2 bg-add text-white rounded-md hover:bg-add-hover transition-colors text-sm font-medium flex items-center gap-2 disabled:opacity-50"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14" />
            </svg>
            Add Lyrics
          </button>
        </div>

        {/* Empty State */}
        {!lyricsQuery.data && !lyricsQuery.isLoading && (
          <div className="p-8 text-center">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" className="mx-auto text-muted-foreground opacity-50">
              <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5.586a1 1 0 0 1 .707.293l5.414 5.414a1 1 0 0 1 .293.707V19a2 2 0 0 1-2 2z" />
            </svg>
            <p className="text-muted-foreground mt-4">No lyrics entries yet</p>
            <button
              onClick={() => setIsAddFormOpen(true)}
              className="mt-4 px-4 py-2 border rounded-md hover:bg-muted transition-colors text-sm"
            >
              Add your first lyrics
            </button>
          </div>
        )}

        {/* Lyrics List */}
        {lyricsQuery.data && (
          <div className="p-4 space-y-3">
            {(lyricsQuery.data as Array<LyricsApiResponse>).map((lyric) => (
              <LyricsEntry 
                key={lyric.id} 
                lyrics={formatLyricsForDisplay(lyric)} 
                onEdit={handleOpenEdit}
                onDelete={handleDeleteLyrics}
              />
            ))}
          </div>
        )}

        {/* Loading State */}
        {lyricsQuery.isLoading && (
          <div className="p-8 text-center">
            <div className="inline-block animate-spin rounded-full border-4 border-gray-300 border-t-primary h-12 w-12 mb-4"></div>
            <p className="text-muted-foreground">Loading lyrics...</p>
          </div>
        )}

        {/* Error State */}
        {lyricsQuery.error && (
          <div className="p-8 text-center">
            <div className="text-destructive mb-4">Error loading lyrics</div>
            <button
              onClick={() => lyricsQuery.refetch()}
              disabled={deleteMutation.isPending}
              className="px-4 py-2 border rounded-md hover:bg-muted transition-colors"
            >
              Retry
            </button>
          </div>
        )}
      </div>

      {/* Add Lyrics Form */}
      <LyricsFormDialog 
        open={isAddFormOpen}
        onOpenChange={setIsAddFormOpen}
        lyrics={null}
        projectId={projectId}
        onSave={handleAddLyrics}
      />

      {/* Edit Lyrics Form */}
      {editingLyrics && (
        <LyricsFormDialog 
          open={!!editingLyrics}
          onOpenChange={handleCloseEdit}
          lyrics={editingLyrics}
          projectId={projectId}
          onSave={(lyricsData) => handleEditLyrics(editingLyrics, lyricsData)}
        />
      )}
    </>
  );
}
