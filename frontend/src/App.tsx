/** Main application component with routing, layout shell, and TanStack Query provider. */

import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { Header } from "./components/Header";
import { Sidebar } from "./components/Sidebar";
import { Footer } from "./components/Footer";

import ProjectsPage from "./features/projects/ProjectsPage";
import { ProjectDetailPage } from "./features/projects/ProjectDetailPage";

// Milestone 6.6 - Dashboard and Workspace Views
import { DashboardView } from "./features/dashboard/DashboardView";
import LyricsLibraryView from "./features/lyrics/LyricsLibraryView";
import ProfileView from "./features/profile/ProfileView";
import { SettingsView } from "./features/settings/SettingsView";

// Create a single QueryClient instance at the application level (NOT inside component functions)
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 5, // 5 seconds
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="flex flex-col h-screen bg-background">
          <Header title="Sanskriti AI Studio" />
          <div className="flex flex-1 overflow-hidden">
            <Sidebar activeRoute="/projects" />
            <main className="flex-1 overflow-auto bg-muted/20">
              <Routes>
                {/* Default to Dashboard on root path */}
                <Route path="/" element={<DashboardView />} />
                
                {/* Projects Routes */}
                <Route path="/projects" element={<ProjectsPage />} />
                <Route path="/assets" element={<div className="p-8"><h1>Assets (Coming Soon)</h1></div>} />
                
                {/* Project detail route - uses dynamic routing */}
                <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
                
                {/* Milestone 6.6 New Routes */}
                <Route path="/dashboard" element={<DashboardView />} />
                <Route path="/lyrics" element={<LyricsLibraryView />} />
                <Route path="/profile" element={<ProfileView />} />
                <Route path="/settings" element={<SettingsView />} />
              </Routes>
            </main>
          </div>
          <Footer />
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
