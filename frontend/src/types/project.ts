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

/** Lyrics type definitions. */

export interface LyricsItem {
  id: string;
  projectId: string;
  title?: string | null;
  content: string;
  language?: string | null;
  status: string;
  created_at?: string;
  updated_at?: string;
}

/** Lyrics create payload. */

export interface LyricsCreatePayload {
  projectId: string;
  title?: string | null;
  content: string;
  language?: string;
  status?: string;
}

/** Lyrics update payload. */

export interface LyricsUpdatePayload {
  title?: string | null;
  content?: string | null;
  language?: string | null;
  status?: string | null;
}
