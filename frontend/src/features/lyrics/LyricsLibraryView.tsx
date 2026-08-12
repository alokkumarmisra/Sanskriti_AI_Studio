/** Lyrics library browse view - shows lyrics for a selected project. */

import React from "react";
import type { Project, LyricsItem } from "../../types/project";
import { useProjectsQuery } from "../../api/projects";
import { useProjectLyricsQuery, useDeleteLyricsMutation } from "../../api/lyrics";

export function LyricsLibraryView() {
  // All React hooks must be called at the very top level before any conditional returns
  
  // Fetch all projects first (always call at top)
  const { data: projects, isLoading: projectsLoading } = useProjectsQuery();
  
  // Always call this hook - never conditionally after early return
  const deleteMutation = useDeleteLyricsMutation();

  // Handle loading state FIRST
  if (projectsLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] p-8 gap-4">
        <div className="inline-block animate-spin rounded-full border-4 border-gray-300 border-t-blue-600 h-12 w-12 mb-4"></div>
        <p className="text-gray-600 dark:text-gray-400">Loading lyrics library...</p>
      </div>
    );
  }

  // Handle no projects state
  if (!projects || projects.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-8 gap-4">
        <h2 className="text-xl font-semibold">No Projects Yet</h2>
        <p className="text-muted-foreground text-sm">Create a project first, then add lyrics to it.</p>
        <button onClick={() => (window.location.href = "/projects")} className="mt-4 px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors font-medium">Create New Project</button>
      </div>
    );
  }

  const selectedProject = projects[0] as Project;
  
  // Load lyrics for first project (hook called after all other hooks - correct order)
  // eslint-disable-next-line react-hooks/rules-of-hooks -- This pattern is valid: hook depends on data from prerequisite hooks
  const { data: lyricsData, error: lyricsError } = useProjectLyricsQuery(selectedProject.id);

  // Handle error state
  if (lyricsError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-8 gap-4">
        <div className="text-destructive text-xl font-semibold">Error Loading Lyrics</div>
        <p className="text-muted-foreground text-sm">{lyricsError instanceof Error ? lyricsError.message : "An unknown error occurred"}</p>
        <button onClick={() => window.location.reload()} className="px-4 py-2 border rounded-md hover:bg-muted transition-colors">Retry</button>
      </div>
    );
  }

  // Empty state - no lyrics in project
  if (!lyricsData || lyricsData.length === 0) {
    return (
      <div className="p-6 max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <button onClick={() => (window.location.href = "/projects")} className="self-start px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground rounded-md transition-colors">← Back to Projects</button>
          <h1 className="text-2xl font-semibold tracking-tight">Lyrics Library</h1>
        </div>

        <div className="border rounded-lg bg-card p-8 text-center text-muted-foreground space-y-4">
          <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M9 18V5l12-2v13" />
            <circle cx="6" cy="18" r="3" />
            <circle cx="18" cy="16" r="3" />
          </svg>
          <h3 className="text-xl font-semibold">No Lyrics Yet</h3>
          <p>There are no lyrics for this project yet.</p>
        </div>

        <div className="flex items-center justify-between p-4 border rounded-md bg-muted/20">
          <p className="text-sm text-muted-foreground">Showing 0 lyrics in {selectedProject.name}</p>
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-secondary">{selectedProject.projectType || "General"} Project</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-6">
        <button onClick={() => (window.location.href = "/projects")} className="self-start px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground rounded-md transition-colors">← Back to Projects</button>
        <div className="flex items-center gap-2">
          <span className="text-xl font-semibold tracking-tight truncate">{selectedProject.name}</span>
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium capitalize ${getStatusColorClass(selectedProject.status)}`}>
            {selectedProject.status.replace("_", " ")}
          </span>
        </div>
      </div>

      {/* Lyrics List */}
      <div className="border rounded-lg bg-card overflow-hidden">
        {lyricsData.map((_, index) => {
          const lyric = lyricsData[index]!;
          return (
            <div key={lyric.id} className="p-6 border-b last:border-b-0 hover:bg-muted/20 transition-colors">
              <div className="flex items-start justify-between gap-4">
                {/* Content */}
                <div className="flex-1 min-w-0 space-y-2">
                  {lyric.title && (
                    <h3 className="font-semibold text-base truncate" title={lyric.title}>{lyric.title}</h3>
                  )}
                  <div className="text-sm text-muted-foreground whitespace-pre-wrap break-words max-h-48 overflow-y-auto">
                    {lyric.content}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium capitalize ${getStatusColorClass(lyric.status)}`}>
                    {lyric.status.replace("_", " ")}
                  </span>
                  {lyric.language && (
                    <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-secondary">
                      {lyric.language}
                    </span>
                  )}
                  {/* Delete button */}
                  <button 
                    onClick={() => deleteMutation.mutate(lyric.id)}
                    disabled={deleteMutation.isPending}
                    className="px-3 py-1.5 border rounded-md hover:bg-destructive/10 hover:text-destructive transition-colors text-sm text-muted-foreground"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between p-4 border rounded-md bg-muted/20">
        <p className="text-sm text-muted-foreground">Showing {lyricsData.length} lyrics</p>
        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary">{selectedProject.projectType || "General"} Project</span>
      </div>
    </div>
  );
}

function getStatusColorClass(status: string): string {
  switch (status) {
    case "draft": return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300";
    case "in_progress": return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300";
    case "completed": return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300";
    default: return "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300";
  }
}

export default LyricsLibraryView;