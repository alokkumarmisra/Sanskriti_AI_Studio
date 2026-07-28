/** Project Detail page component connected to the real backend API. */

import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import type { Project } from "../../types/project";
import { useProjectQuery, useUpdateProjectMutation, useDeleteProjectMutation } from "../../api/projects";
import EditProjectDialog from "./EditProjectDialog";
import DeleteConfirmationDialog from "./DeleteConfirmationDialog";

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  // Always define hooks at the top - never conditionally after returns
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Fetch project data from API (always called at top level)
  const { data: project, isLoading, error, refetch } = useProjectQuery(projectId || "");

  const updateMutation = useUpdateProjectMutation();
  const deleteMutation = useDeleteProjectMutation();

  // Check if projectId is missing
  if (!projectId) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] p-8 gap-4">
        <div className="text-destructive text-xl font-semibold">Invalid Project ID</div>
        <p className="text-muted-foreground text-sm">
          Please select a valid project from the Projects list.
        </p>
      </div>
    );
  }

  // Handle loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] p-8 gap-4">
        <div className="inline-block animate-spin rounded-full border-4 border-gray-300 border-t-blue-600 h-12 w-12 mb-4"></div>
        <p className="text-gray-600 dark:text-gray-400">Loading project...</p>
      </div>
    );
  }

  // Handle error state (project not found or API error)
  if (error) {
    const errorMessage = error instanceof Error ? error.message : "An unknown error occurred";
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-8 gap-4">
        <div className="text-destructive text-xl font-semibold">Error Loading Project</div>
        <p className="text-muted-foreground text-sm">{errorMessage}</p>
        <button
          onClick={() => refetch()}
          disabled={isDeleting}
          className="px-4 py-2 border rounded-md hover:bg-muted transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  // Handle not found state (project was deleted)
  if (!project) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-8 gap-4">
        <div className="text-muted-foreground text-2xl font-bold">Project Not Found</div>
        <p className="text-muted-foreground text-sm">
          This project no longer exists or was deleted.
        </p>
        <button
          onClick={() => navigate("/projects")}
          className="mt-4 px-4 py-2 border rounded-md hover:bg-muted transition-colors"
        >
          Go to Projects List
        </button>
      </div>
    );
  }

  // Format project status display
  const getStatusDisplay = (status: string) => {
    switch (status.toLowerCase()) {
      case "draft": return "Draft";
      case "in_progress": return "In Progress";
      case "completed": return "Completed";
      default: return status.charAt(0).toUpperCase() + status.slice(1);
    }
  };

  // Format project type display
  const getProjectTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      documentation: "Documentation",
      research: "Research",
      product: "Product",
      other: "Other",
      general: "General",
      unknown: "Unknown",
    };
    return labels[type] || type;
  };

  const getProjectTypeColor = (type: string) => {
    switch (getProjectTypeLabel(type)) {
      case "Documentation":
        return "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300";
      case "Research":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300";
      case "Product":
        return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300";
      case "General":
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300";
    }
  };

  const getStatusColorClass = (status: string) => {
    switch (status.toLowerCase()) {
      case "draft":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300";
      case "in_progress":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300";
      case "completed":
        return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300";
    }
  };

  const handleUpdateProject = (updatedProject: { 
    name?: string; 
    description?: string | null; 
    projectType?: string;
    status?: string;
  }) => {
    if (!project) return;
    
    const payload = {
      name: updatedProject.name || undefined,
      description: updatedProject.description || undefined,
      project_type: updatedProject.projectType || undefined,
      status: updatedProject.status || undefined,
    };

    updateMutation.mutate({
      id: project.id,
      payload,
    });
  };

  const handleDeleteProject = () => {
    if (!projectToDelete || isDeleting) return;

    deleteMutation.mutate(projectToDelete.id);

    setIsDeleting(true);

    setTimeout(() => {
      setProjectToDelete(null);
      refetch();
    }, 300);
  };

  const handleOpenEdit = () => {
    if (project) {
      setProjectToDelete(null);
      setIsEditDialogOpen(true);
    }
  };

  const handleOpenDelete = () => {
    setProjectToDelete(project);
    setIsEditDialogOpen(false);
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <button
          onClick={() => navigate("/projects")}
          className="self-start px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground rounded-md transition-colors"
        >
          ← Back to Projects
        </button>
        
        <div className="flex items-center gap-2">
          {/* Edit Button */}
          <button
            onClick={handleOpenEdit}
            disabled={!project || isDeleting}
            className="px-4 py-2 border rounded-md hover:bg-muted transition-colors font-medium flex items-center gap-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />
            </svg>
            Edit Project
          </button>
          
          {/* Delete Button */}
          <button
            onClick={handleOpenDelete}
            disabled={!project || isDeleting}
            className="px-4 py-2 border border-destructive rounded-md hover:bg-destructive/10 transition-colors font-medium text-destructive flex items-center gap-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M5 7h14M5 7v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7m-9 4h4" />
              <line x1="9" y1="22" x2="15" y2="22" />
            </svg>
            Delete Project
          </button>
        </div>
      </div>

      {/* Project Details Card */}
      <div className="border rounded-lg bg-card space-y-6">
        {/* Main Info Section */}
        <div className="p-6 border-b">
          <h1 className="text-3xl font-semibold tracking-tight">{project.name}</h1>
          
          {project.description && (
            <p className="text-muted-foreground text-lg mt-2">{project.description}</p>
          )}
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-6 border-b">
          {/* Project Type */}
          <div className="space-y-2">
            <span className="text-sm text-muted-foreground">Type</span>
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium capitalize ${getProjectTypeColor(project.project_type || project.projectType)}`}>
              {getProjectTypeLabel(project.project_type || project.projectType)}
            </span>
          </div>

          {/* Status */}
          <div className="space-y-2">
            <span className="text-sm text-muted-foreground">Status</span>
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium capitalize ${getStatusColorClass(project.status)}`}>
              {getStatusDisplay(project.status)}
            </span>
          </div>

          {/* Owner */}
          <div className="space-y-2">
            <span className="text-sm text-muted-foreground">Owner</span>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary capitalize">
              {project.owner || "Not set"}
            </span>
          </div>

          {/* Created At */}
          <div className="space-y-2">
            <span className="text-sm text-muted-foreground">Created</span>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-secondary">
              {new Date(project.created_at).toLocaleDateString()}
            </span>
          </div>

          {/* Updated At */}
          <div className="space-y-2">
            <span className="text-sm text-muted-foreground">Updated</span>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-secondary">
              {new Date(project.updated_at).toLocaleDateString()}
            </span>
          </div>

          {/* Last Modified */}
          <div className="space-y-2">
            <span className="text-sm text-muted-foreground">Last Modified</span>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-secondary">
              {new Date(project.updated_at).toLocaleTimeString()}
            </span>
          </div>

          {/* Project ID */}
          <div className="space-y-2 sm:col-span-2 lg:col-span-4">
            <span className="text-sm text-muted-foreground">Project ID</span>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-secondary/80 break-all">
              {project.id}
            </span>
          </div>
        </div>

        {/* Empty state for minimal projects */}
        {!project.description && (
          <div className="p-6 border-b text-center text-muted-foreground text-sm">
            No additional description available.
          </div>
        )}
      </div>

      {/* Project Details Card - Actions Footer */}
      <div className="flex items-center justify-between p-4 border rounded-md bg-muted/20">
        <p className="text-sm text-muted-foreground">
          Showing project details for 1 project
        </p>
        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary">
          {project.project_type || "General"} Project
        </span>
      </div>

      {/* Edit Project Dialog */}
      {project && (
        <EditProjectDialog 
          open={isEditDialogOpen} 
          onOpenChange={setIsEditDialogOpen}
          project={{ ...project, projectType: project.project_type || undefined }}
          onSave={handleUpdateProject}
        />
      )}

      {/* Delete Confirmation Dialog */}
      {projectToDelete && (
        <DeleteConfirmationDialog 
          open={!!projectToDelete} 
          onOpenChange={(open) => open ? setProjectToDelete(null) : {}}
          projectName={projectToDelete.name}
          onConfirm={handleDeleteProject}
        />
      )}
    </div>
  );
}

export default ProjectDetailPage;