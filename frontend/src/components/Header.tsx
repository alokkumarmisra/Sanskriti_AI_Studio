import React from 'react';

interface HeaderProps {
  title: string;
}

export const Header: React.FC<HeaderProps> = ({ title }) => (
  <header className="flex items-center justify-between h-16 px-4 border-b bg-background">
    <div className="text-xl font-semibold flex items-center gap-2">
      <span>Sanskriti AI Studio</span>
    </div>
    <nav className="hidden md:flex gap-6 text-sm">
      <a href="/dashboard" className="px-3 py-1.5 hover:underline rounded hover:bg-muted transition-colors">Dashboard</a>
      <a href="/projects" className="px-3 py-1.5 hover:underline rounded hover:bg-muted transition-colors">Projects</a>
      <a href="/assets" className="px-3 py-1.5 hover:underline rounded hover:bg-muted transition-colors">Assets</a>
      <a href="/settings" className="px-3 py-1.5 hover:underline rounded hover:bg-muted transition-colors">Settings</a>
    </nav>
  </header>
);

export default Header;