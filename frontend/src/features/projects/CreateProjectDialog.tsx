/** Create Project dialog component with Project Type field. */

import React, { useState } from "react";

interface CreateProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreate: (project: { name: string; description?: string | null; projectType: string }) => void;
}

export function CreateProjectDialog({ open, onOpenChange, onCreate }: CreateProjectDialogProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [projectType, setProjectType] = useState<"documentation" | "research" | "product" | "other">("documentation");
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError("Name is required");
      return;
    }

    // Call onCreate with the new project data
    onCreate({ name, description, projectType });
    
    // Reset form
    setName("");
    setDescription("");
    setProjectType("documentation");
    
    onOpenChange(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <form onSubmit={handleSubmit} className="w-full max-w-md p-6 bg-white rounded-lg shadow-xl border animate-in fade-in zoom-in duration-200">
        <h2 className="text-xl font-semibold mb-4">Create Project</h2>

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
            <label htmlFor="projectType" className="block text-sm font-medium mb-1.5">Project Type</label>
            <select
              id="projectType"
              value={projectType}
              onChange={(e) => setProjectType(e.target.value as "documentation" | "research" | "product" | "other")}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
            >
              <option value="documentation">Documentation</option>
              <option value="research">Research</option>
              <option value="product">Product</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={() => onOpenChange(false)} className="px-4 py-2 border rounded-md hover:bg-secondary transition-colors">
              Cancel
            </button>
            <button type="submit" disabled={!name.trim()} className="px-4 py-2 bg-add text-white rounded-md hover:bg-add-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
              Create Project
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}

export default CreateProjectDialog;