/** Dashboard home page component showing project overview and quick actions. */

import React from "react";
import { useNavigate } from "react-router-dom";
import type { Project } from "../../types/project";
import { useProjectsQuery } from "../../api/projects";

export function DashboardView() {
  const navigate = useNavigate();

  // Fetch projects for dashboard overview
  const { data: projects, isLoading, error } = useProjectsQuery();

  // Handle loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] p-8 gap-4">
        <div className="inline-block animate-spin rounded-full border-4 border-gray-300 border-t-blue-600 h-12 w-12 mb-4"></div>
        <p className="text-gray-600 dark:text-gray-400">Loading dashboard...</p>
      </div>
    );
  }

  // Handle error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-8 gap-4">
        <div className="text-destructive text-xl font-semibold">Error Loading Dashboard</div>
        <p className="text-muted-foreground text-sm">Failed to load projects. Please try again later.</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 border rounded-md hover:bg-muted transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  // Handle empty state (no projects)
  if (!projects || projects.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-8 gap-4">
        <div className="text-xl font-semibold">Welcome to Sanskriti AI Studio</div>
        <p className="text-muted-foreground text-sm text-center max-w-md">
          This is your workspace dashboard. Create your first project to get started.
        </p>
        <button
          onClick={() => navigate("/projects")}
          className="mt-4 px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors font-medium"
        >
          Browse Projects
        </button>
      </div>
    );
  }

  // Get project statistics
  const totalProjects = projects.length;
  const activeProjects = projects.filter((p: Project) => p.status === "in_progress").length;
  
  // Group projects by type for better organization
  const projectsByType: Record<string, Project[]> = {};
  projects.forEach((project: Project) => {
    const type = project.projectType || "general";
    if (!projectsByType[type]) {
      projectsByType[type] = [];
    }
    projectsByType[type].push(project);
  });

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Welcome to your workspace. Manage projects and explore features below.
          </p>
        </div>
      </div>

      {/* Dashboard Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Projects Card */}
        <div className="border rounded-lg bg-card p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-md bg-primary/10">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                <line x1="16" y1="2" x2="16" y2="6" />
                <line x1="8" y1="2" x2="8" y2="6" />
                <line x1="3" y1="10" x2="21" y2="10" />
              </svg>
            </div>
            <span className="text-sm text-muted-foreground font-medium">Total Projects</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold">{totalProjects}</span>
          </div>
        </div>

        {/* Active Projects Card */}
        <div className="border rounded-lg bg-card p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-md bg-blue-100 dark:bg-blue-900/30">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
            <span className="text-sm text-muted-foreground font-medium">Active Projects</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-blue-600 dark:text-blue-400">{activeProjects}</span>
          </div>
        </div>

        {/* Projects by Type Card */}
        <div className="border rounded-lg bg-card p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-md bg-green-100 dark:bg-green-900/30">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="8" y1="6" x2="21" y2="6" />
                <line x1="8" y1="12" x2="21" y2="12" />
                <line x1="8" y1="18" x2="21" y2="18" />
                <line x1="3" y1="6" x2="3.01" y2="6" />
                <line x1="3" y1="12" x2="3.01" y2="12" />
                <line x1="3" y1="18" x2="3.01" y2="18" />
              </svg>
            </div>
            <span className="text-sm text-muted-foreground font-medium">Project Types</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold">{Object.keys(projectsByType).length}</span>
            <span className="text-sm text-muted-foreground">unique types</span>
          </div>
        </div>

        {/* Quick Action Card */}
        <div className="border rounded-lg bg-card p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-md bg-purple-100 dark:bg-purple-900/30">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            </div>
            <span className="text-sm text-muted-foreground font-medium">Quick Actions</span>
          </div>
          <div className="space-y-2">
            <button
              onClick={() => navigate("/projects/new")}
              className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors text-sm font-medium"
            >
              Create New Project
            </button>
            <button
              onClick={() => navigate("/projects")}
              className="w-full px-4 py-2 border rounded-md hover:bg-muted transition-colors text-sm font-medium"
            >
              Browse All Projects
            </button>
          </div>
        </div>
      </div>

      {/* Recent/Featured Projects */}
      <div className="border rounded-lg bg-card overflow-hidden">
        <div className="p-6 border-b">
          <h2 className="text-xl font-semibold tracking-tight">Your Projects</h2>
        </div>
        
        {Object.keys(projectsByType).length > 0 ? (
          <div className="divide-y">
            {Object.entries(projectsByType).map(([type, typeProjects]: [string, Project[]]) => (
              <div key={type} className="p-6 space-y-4">
                {/* Section Header */}
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium capitalize bg-secondary text-secondary-foreground">
                    {type}
                  </span>
                  <span className="text-sm text-muted-foreground">{typeProjects.length} projects</span>
                </div>
                
                {/* Project Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {typeProjects.slice(0, 6).map((project) => (
                    <button
                      key={project.id}
                      onClick={() => navigate(`/projects/${project.id}`)}
                      className="p-4 border rounded-lg hover:border-primary/30 transition-colors text-left group"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-base truncate group-hover:text-primary transition-colors" title={project.name}>
                            {project.name}
                          </h3>
                          {project.description && (
                            <p className="text-sm text-muted-foreground mt-2 line-clamp-2">
                              {project.description}
                            </p>
                          )}
                        </div>
                        
                        {/* Status Badge */}
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium capitalize ${getStatusColorClass(project.status)}`}>
                          {project.status.replace("_", " ")}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center text-muted-foreground">
            No projects found. Create your first project to get started.
          </div>
        )}
      </div>

      {/* Quick Links Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <button
          onClick={() => navigate("/lyrics")}
          className="p-6 border rounded-lg hover:border-primary/30 transition-colors text-left space-y-4 group"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-md bg-pink-100 dark:bg-pink-900/30 group-hover:bg-pink-200 dark:group-hover:bg-pink-800/30 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 18V5l12-2v13" />
                <circle cx="6" cy="18" r="3" />
                <circle cx="18" cy="16" r="3" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold">Lyrics Library</h3>
              <p className="text-sm text-muted-foreground mt-1">Browse and manage all lyrics in your projects.</p>
            </div>
          </div>
        </button>

        <button
          onClick={() => navigate("/assets")}
          className="p-6 border rounded-lg hover:border-primary/30 transition-colors text-left space-y-4 group"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-md bg-orange-100 dark:bg-orange-900/30 group-hover:bg-orange-200 dark:group-hover:bg-orange-800/30 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold">Assets</h3>
              <p className="text-sm text-muted-foreground mt-1">Manage your project assets and resources.</p>
            </div>
          </div>
        </button>
      </div>
    </div>
  );
}

// Status color class helper
function getStatusColorClass(status: string): string {
  switch (status) {
    case "draft":
      return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300";
    case "in_progress":
    case "active":
      return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300";
    case "completed":
      return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300";
    default:
      return "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300";
  }
}

export default DashboardView;