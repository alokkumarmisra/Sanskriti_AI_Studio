/** Settings view component for user preferences. */

import React from "react";
import { useNavigate } from "react-router-dom";

export function SettingsView() {
  const navigate = useNavigate();

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate(-1)} className="self-start px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground rounded-md transition-colors">
          ← Back
        </button>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
      </div>

      {/* Appearance Section */}
      <div className="border rounded-lg bg-card p-6 space-y-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium">Appearance</h2>
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-secondary">Active</span>
        </div>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label htmlFor="theme" className="font-medium">Theme</label>
              <p className="text-sm text-muted-foreground">Choose your preferred color theme</p>
            </div>
            <div className="flex gap-2">
              <button className="px-4 py-2 border rounded-md hover:bg-muted transition-colors bg-white dark:bg-gray-800">Light</button>
              <button className="px-4 py-2 border rounded-md hover:bg-muted transition-colors bg-gray-900 dark:bg-black">Dark</button>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label htmlFor="sidebar" className="font-medium">Sidebar Position</label>
              <p className="text-sm text-muted-foreground">Toggle sidebar visibility</p>
            </div>
            <button className="px-4 py-2 border rounded-md hover:bg-muted transition-colors">Default</button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label htmlFor="fontSize" className="font-medium">Font Size</label>
              <p className="text-sm text-muted-foreground">Adjust base font size</p>
            </div>
            <select className="px-3 py-2 border rounded-md bg-white dark:bg-gray-800">
              <option value="sm">Small</option>
              <option value="md" selected>Medium</option>
              <option value="lg">Large</option>
            </select>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end pt-4 border-t">
          <button
            onClick={() => alert("Settings saved!")}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors font-medium"
          >
            Save Changes
          </button>
        </div>
      </div>

      {/* Notifications Section */}
      <div className="border rounded-lg bg-card p-6 space-y-4">
        <h2 className="text-lg font-medium mb-4">Notifications</h2>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="font-medium">Email Notifications</label>
              <p className="text-sm text-muted-foreground">Receive email notifications for updates</p>
            </div>
            <button className="px-4 py-2 border rounded-md hover:bg-muted transition-colors bg-gray-100 dark:bg-gray-700">Enabled</button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="font-medium">Push Notifications</label>
              <p className="text-sm text-muted-foreground">Receive push notifications in the browser</p>
            </div>
            <button className="px-4 py-2 border rounded-md hover:bg-muted transition-colors bg-gray-100 dark:bg-gray-700">Disabled</button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="font-medium">Desktop Notifications</label>
              <p className="text-sm text-muted-foreground">Show notifications on desktop</p>
            </div>
            <button className="px-4 py-2 border rounded-md hover:bg-muted transition-colors bg-gray-100 dark:bg-gray-700">Disabled</button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="font-medium">Sound Notifications</label>
              <p className="text-sm text-muted-foreground">Play sound when notifications arrive</p>
            </div>
            <button className="px-4 py-2 border rounded-md hover:bg-muted transition-colors bg-gray-100 dark:bg-gray-700">Enabled</button>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end pt-4 border-t">
          <button
            onClick={() => alert("Notifications saved!")}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors font-medium"
          >
            Save Changes
          </button>
        </div>
      </div>

      {/* Data Management Section */}
      <div className="border rounded-lg bg-card p-6 space-y-4">
        <h2 className="text-lg font-medium mb-4">Data Management</h2>
        
        <div className="space-y-4">
          <div>
            <label className="font-medium block mb-1">Export Project Data</label>
            <p className="text-sm text-muted-foreground">Download all your projects and lyrics as JSON</p>
            <button
              onClick={() => alert("Downloading your data...")}
              className="mt-2 px-4 py-2 bg-primary/10 text-primary rounded-md hover:bg-primary/20 transition-colors font-medium text-sm"
            >
              Export Data
            </button>
          </div>

          <div>
            <label className="font-medium block mb-1">Clear Cache</label>
            <p className="text-sm text-muted-foreground">Remove cached data and refresh application state</p>
            <button
              onClick={() => alert("Cache cleared!")}
              className="mt-2 px-4 py-2 bg-primary/10 text-primary rounded-md hover:bg-primary/20 transition-colors font-medium text-sm"
            >
              Clear Cache
            </button>
          </div>

          <div>
            <label className="font-medium block mb-1">Reset Application</label>
            <p className="text-sm text-muted-foreground">Reset all settings to default values</p>
            <button
              onClick={() => alert("Settings reset to defaults!")}
              className="mt-2 px-4 py-2 bg-primary/10 text-primary rounded-md hover:bg-primary/20 transition-colors font-medium text-sm"
            >
              Reset Settings
            </button>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end pt-4 border-t">
          <button
            onClick={() => alert("Data management settings saved!")}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors font-medium"
          >
            Save Changes
          </button>
        </div>
      </div>

      {/* About Section */}
      <div className="border rounded-lg bg-card p-6 space-y-4">
        <h2 className="text-lg font-medium mb-4">About</h2>
        
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Version</span>
            <span className="font-medium">1.0.0</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Build</span>
            <span className="font-medium">2026-08-12</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Database</span>
            <span className="font-medium">PostgreSQL Connected</span>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end pt-4 border-t">
          <button
            onClick={() => alert("About information displayed!")}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors font-medium"
          >
            Refresh Info
          </button>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between p-4 border rounded-md bg-muted/20">
        <p className="text-sm text-muted-foreground">Manage your application preferences and settings</p>
        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-secondary">General Settings</span>
      </div>
    </div>
  );
}

export default SettingsView;
