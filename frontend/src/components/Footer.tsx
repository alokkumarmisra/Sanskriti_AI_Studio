import React from 'react';

export const Footer: React.FC = () => (
  <footer className="h-16 border-t flex items-center justify-between px-4 text-sm">
    <div>&copy; {new Date().getFullYear()} Sanskriti AI Studio</div>
    <nav className="flex gap-4">
      <a href="/dashboard" className="hover:underline">Dashboard</a>
      <a href="/projects" className="hover:underline">Projects</a>
      <a href="/assets" className="hover:underline">Assets</a>
      <a href="/settings" className="hover:underline">Settings</a>
    </nav>
  </footer>
);

export default Footer;