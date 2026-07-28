/** Edit Project dialog component with Project Type field. */

import React, { useState } from "react";

interface EditProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  project: { name?: string; description?: string | null; status?: "draft" | "in_progress" | "completed"; projectType?: string };
  onSave: (project: { name: string; description?: string | null; status?: "draft" | "in_progress" | "completed"; projectType?: string }) => void;
}

export function EditProjectDialog({ open, onOpenChange, project, onSave }: EditProjectDialogProps) {
  const [name, setName] = useState(project.name || "");
  const [description, setDescription] = useState(project.description || "");
  const [status, setStatus] = useState<"draft" | "in_progress" | "completed">(project.status || "draft");
  const [projectType, setProjectType] = useState<string>(project.projectType || "documentation");
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError("Name is required");
      return;
    }

    // Call onSave with the updated project data
    onSave({ name, description: description || null, status, projectType });
    
    // Reset form
    setName("");
    setDescription("");
    setStatus("draft");
    setProjectType("documentation");
    
    onOpenChange(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <form onSubmit={handleSubmit} className="w-full max-w-md p-6 bg-card rounded-lg shadow-xl border animate-in fade-in zoom-in duration-200">
        <h2 className="text-xl font-semibold mb-4">Edit Project</h2>

        {error && (
          <div className="mb-4 p-3 bg-destructive/15 text-destructive rounded-md border border-destructive/20">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label htmlFor="name" className="block text-sm font-medium mb-1.5">Name *</label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter project name"
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium mb-1.5">Description</label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter project description (optional)"
              rows={3}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
            />
          </div>

          <div>
            <label htmlFor="status" className="block text-sm font-medium mb-1.5">Status</label>
            <select
              id="status"
              value={status}
              onChange={(e) => setStatus(e.target.value as "draft" | "in_progress" | "completed")}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50 capitalize"
            >
              <option value="draft">Draft</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
            </select>
          </div>

          <div>
            <label htmlFor="projectType" className="block text-sm font-medium mb-1.5">Project Type</label>
            <select
              id="projectType"
              value={projectType}
              onChange={(e) => setProjectType(e.target.value)}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50 capitalize"
            >
              <option value="documentation">Documentation</option>
              <option value="research">Research</option>
              <option value="product">Product</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={() => onOpenChange(false)} className="px-4 py-2 border rounded-md hover:bg-muted transition-colors">
              Cancel
            </button>
            <button type="submit" disabled={!name.trim()} className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
              Save Changes
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}

export default EditProjectDialog;