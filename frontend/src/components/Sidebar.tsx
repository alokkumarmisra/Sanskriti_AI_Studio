import React from 'react';

interface SidebarProps {
  activeRoute: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeRoute }) => (
  <aside className="w-64 border-r flex flex-col h-full">
    <nav className="flex-1 p-4 space-y-2">
      <a href="/dashboard" className={`block px-3 py-2 rounded ${activeRoute === '/dashboard' ? 'bg-gray-100 dark:bg-gray-800' : ''}`}>Dashboard</a>
      <a href="/projects" className={`block px-3 py-2 rounded ${activeRoute === '/projects' ? 'bg-gray-100 dark:bg-gray-800' : ''}`}>Projects</a>
      <a href="/lyrics" className={`block px-3 py-2 rounded ${activeRoute === '/lyrics' ? 'bg-gray-100 dark:bg-gray-800' : ''}`}>Lyrics Library</a>
      {/* Milestone 7.2 - Content & Scene Planning Workspace */}
      <a href="/content-scene-planning" className={`block px-3 py-2 rounded ${activeRoute === '/content-scene-planning' ? 'bg-gray-100 dark:bg-gray-800' : ''}`}>Content & Scene Planning</a>
      <a href="/assets" className={`block px-3 py-2 rounded ${activeRoute === '/assets' ? 'bg-gray-100 dark:bg-gray-800' : ''}`}>Assets</a>
      <a href="/settings" className={`block px-3 py-2 rounded ${activeRoute === '/settings' ? 'bg-gray-100 dark:bg-gray-800' : ''}`}>Settings</a>
    </nav>
  </aside>
);

export default Sidebar;
