/** Delete Confirmation dialog component showing project name. */

import React from "react";

interface DeleteConfirmationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectName?: string;
  onConfirm: () => void;
}

export function DeleteConfirmationDialog({ open, onOpenChange, projectName = "this project", onConfirm }: DeleteConfirmationDialogProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <form onSubmit={(e) => { e.preventDefault(); onOpenChange(false); }} className="w-full max-w-sm p-6 bg-card rounded-lg shadow-xl border animate-in fade-in zoom-in duration-200">
        <h2 className="text-xl font-semibold mb-4">Delete Project</h2>

        <p className="text-muted-foreground text-sm mb-6">
          Are you sure you want to delete <strong>{projectName}</strong>? This action cannot be undone. All data associated with this project will be permanently removed.
        </p>

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={() => onOpenChange(false)} className="px-4 py-2 border rounded-md hover:bg-muted transition-colors">
            Cancel
          </button>
          <button type="submit" className="px-4 py-2 bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90 transition-colors">
            Delete
          </button>
        </div>
      </form>
    </div>
  );
}

export default DeleteConfirmationDialog;