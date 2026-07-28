/** Projects page component connected to the real backend API. */

import React from "react";
import type { Project } from "../../types/project";
import { useProjectsQuery, useCreateProjectMutation, useUpdateProjectMutation, useDeleteProjectMutation } from "../../api/projects";
import CreateProjectDialog from "./CreateProjectDialog";
import EditProjectDialog from "./EditProjectDialog";
import DeleteConfirmationDialog from "./DeleteConfirmationDialog";
import ProjectActions from "./ProjectActions";

export function ProjectsPage() {
  const { data: projects, isLoading, error } = useProjectsQuery();
  const createMutation = useCreateProjectMutation();
  const updateMutation = useUpdateProjectMutation();
  const deleteMutation = useDeleteProjectMutation();

  // Dialog states
  const [isCreateDialogOpen, setIsCreateDialogOpen] = React.useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = React.useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = React.useState(false);
  const [projectToEdit, setProjectToEdit] = React.useState<Project | null>(null);
  const [projectToDelete, setProjectToDelete] = React.useState<Project | null>(null);

  // Handle create project with API
  const handleCreateProject = (newProject: { name: string; description?: string | null; projectType: string }) => {
    if (!newProject.name.trim()) return;
    
    // Create the full payload including project_type
    const payload = {
      name: newProject.name,
      description: newProject.description || null,
      status: "draft",
      project_type: newProject.projectType,
    };

    createMutation.mutate(payload);

    // Reset form after a brief delay (mutation is async)
    setTimeout(() => {
      setIsCreateDialogOpen(false);
    }, 300);
  };

  // Handle edit project with API
  const handleEditProject = (updatedProject: { name: string; description?: string | null; status?: "draft" | "in_progress" | "completed"; projectType?: string }) => {
    if (!projectToEdit || !updatedProject.name.trim()) return;

    const payload = {
      name: updatedProject.name,
      description: updatedProject.description || null,
      status: updatedProject.status || undefined,
    };

    updateMutation.mutate({
      id: projectToEdit.id,
      payload,
    });

    setTimeout(() => {
      setIsEditDialogOpen(false);
      setProjectToEdit(null);
    }, 300);
  };

  // Handle delete project with API
  const handleDeleteProject = () => {
    if (!projectToDelete) return;

    deleteMutation.mutate(projectToDelete.id);

    setTimeout(() => {
      setIsDeleteDialogOpen(false);
      setProjectToDelete(null);
    }, 300);
  };

  // Get project type display text
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

  // Handle loading state (empty)
  if (isLoading && (!projects || projects.length === 0)) {
    return (
      <div className="flex items-center justify-center min-h-[40vh] p-8 gap-4">
        <div className="inline-block animate-spin rounded-full border-4 border-gray-300 border-t-blue-600 h-12 w-12 mb-4"></div>
        <p className="text-gray-600 dark:text-gray-400">Loading projects...</p>
      </div>
    );
  }

  // Handle error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[40vh] p-8 gap-4">
        <div className="text-destructive text-xl font-semibold">Error</div>
        <p className="text-muted-foreground text-sm">Failed to load projects. Please try again later.</p>
        <button
          onClick={() => {
            // Refresh query by refetching
            window.location.reload();
          }}
          className="px-4 py-2 border rounded-md hover:bg-muted transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  // Empty state (no projects)
  if (!projects || projects.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[40vh] p-8 gap-4">
        <h2 className="text-xl font-semibold">No Projects</h2>
        <p className="text-muted-foreground text-sm">
          Create your first project to get started.
        </p>
        <button
          onClick={() => setIsCreateDialogOpen(true)}
          className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
        >
          Create New Project
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Page Header with Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Projects</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Manage your projects, track progress, and collaborate with your team.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* New Project Button */}
          <button
            onClick={() => setIsCreateDialogOpen(true)}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors font-medium flex items-center gap-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M5 12h14M12 5v14" />
            </svg>
            New Project
          </button>
        </div>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {projects.map((project) => (
          <div key={project.id} className="p-5 border rounded-lg bg-card hover:border-primary/30 transition-colors cursor-pointer group">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-lg truncate" title={project.name}>{project.name}</h3>
                {project.description && (
                  <p className="text-sm text-muted-foreground mt-2 line-clamp-2">
                    {project.description}
                  </p>
                )}
              </div>
              
              {/* Status Badge */}
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${getStatusColorClass(project.status)}`}>
                {project.status.replace("_", " ")}
              </span>
            </div>

            {/* Project Type Badge */}
            <div className="mt-4 flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Type:</span>
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium capitalize ${getStatusColorClass(getProjectTypeLabel(project.projectType))}`}>
                {getProjectTypeLabel(project.projectType)}
              </span>
            </div>

            {/* Created Date */}
            <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                <line x1="16" y1="2" x2="16" y2="6" />
                <line x1="8" y1="2" x2="8" y2="6" />
                <line x1="3" y1="10" x2="21" y2="10" />
              </svg>
              Created: {new Date(project.created_at || project.createdAt).toLocaleDateString()}
            </div>

            {/* Actions */}
            <div className="mt-4 pt-4 border-t flex items-center justify-end gap-2">
              <ProjectActions 
                projectId={project.id}
                projectName={project.name}
                onEdit={() => {
                  setProjectToEdit(project);
                  setIsEditDialogOpen(true);
                }}
                onDelete={() => {
                  setProjectToDelete(project);
                  setIsDeleteDialogOpen(true);
                }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Footer with project count */}
      <div className="flex items-center justify-between p-4 border rounded-md bg-muted/20">
        <p className="text-sm text-muted-foreground">
          Showing {projects.length} project{projects.length !== 1 ? "s" : ""}
        </p>
        {/* Project count badge */}
        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary">
          {projects.length} Total Projects
        </span>
      </div>

      {/* Create Project Dialog */}
      <CreateProjectDialog 
        open={isCreateDialogOpen} 
        onOpenChange={setIsCreateDialogOpen}
        onCreate={handleCreateProject}
      />

      {/* Edit Project Dialog */}
      {projectToEdit && (
        <EditProjectDialog 
          open={isEditDialogOpen} 
          onOpenChange={setIsEditDialogOpen}
          project={{ ...projectToEdit, projectType: projectToEdit.projectType }}
          onSave={handleEditProject}
        />
      )}

      {/* Delete Confirmation Dialog */}
      {projectToDelete && (
        <DeleteConfirmationDialog 
          open={isDeleteDialogOpen} 
          onOpenChange={setIsDeleteDialogOpen}
          projectName={projectToDelete.name}
          onConfirm={handleDeleteProject}
        />
      )}
    </div>
  );
}

// Status color class helper
const getStatusColorClass = (status: string) => {
  switch (status) {
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

export default ProjectsPage;