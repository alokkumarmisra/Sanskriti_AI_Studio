/** Project type definitions. */

export interface Project {
  id: string;
  name: string;
  description?: string | null;
  status: "draft" | "in_progress" | "completed";
  projectType: string;
  createdAt: string;
  updatedAt: string;
}