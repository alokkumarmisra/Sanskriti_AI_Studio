/** Reusable project actions button group. */

import React from "react";
import { Link } from "react-router-dom";

interface ProjectActionsProps {
  projectId: string;
  projectName: string;
  onEdit?: () => void;
  onDelete?: () => void;
}

export function ProjectActions({ projectId, projectName, onEdit, onDelete }: ProjectActionsProps) {
  return (
    <div className="flex items-center gap-2">
      {/* View Details Button */}
      <Link 
        to={`/projects/${projectId}`}
        title={`View details for ${projectName}`}
        className="p-2 text-primary hover:text-primary-foreground hover:bg-primary/10 rounded-md transition-colors font-medium"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M9 18l6-6-6-6" />
          <path d="M3 15h8" />
        </svg>
      </Link>
      
      {onEdit && (
        <button
          onClick={onEdit}
          title="Edit Project"
          className="p-2 text-muted-foreground hover:text-foreground rounded-md transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4" />
          </svg>
        </button>
      )}
      
      {onDelete && (
        <button
          onClick={onDelete}
          title="Delete Project"
          className="p-2 text-muted-foreground hover:text-destructive rounded-md transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M10 11v6M14 11v6" />
          </svg>
        </button>
      )}
    </div>
  );
}

export default ProjectActions;