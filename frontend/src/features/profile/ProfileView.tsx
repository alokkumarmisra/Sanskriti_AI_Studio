/** User profile view component. */

import React from "react";
import { useNavigate } from "react-router-dom";

export function ProfileView() {
  const navigate = useNavigate();

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate(-1)} className="self-start px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground rounded-md transition-colors">
          ← Back
        </button>
        <h1 className="text-2xl font-semibold tracking-tight">My Profile</h1>
      </div>

      {/* Profile Form */}
      <div className="border rounded-lg bg-card p-6 space-y-4">
        <h2 className="text-lg font-medium">Personal Information</h2>
        
        <div className="space-y-4">
          <div>
            <label htmlFor="firstName" className="block text-sm font-medium mb-1">First Name</label>
            <input
              type="text"
              id="firstName"
              placeholder="Enter your first name"
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          <div>
            <label htmlFor="lastName" className="block text-sm font-medium mb-1">Last Name</label>
            <input
              type="text"
              id="lastName"
              placeholder="Enter your last name"
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-1">Email Address</label>
            <input
              type="email"
              id="email"
              placeholder="your.email@example.com"
              disabled
              className="w-full px-3 py-2 border rounded-md bg-muted/50 focus:outline-none cursor-not-allowed"
            />
          </div>

          <div>
            <label htmlFor="role" className="block text-sm font-medium mb-1">Role</label>
            <select
              id="role"
              disabled
              className="w-full px-3 py-2 border rounded-md bg-muted/50 focus:outline-none cursor-not-allowed"
            >
              <option value="viewer">Viewer</option>
              <option value="editor">Editor</option>
              <option value="admin">Admin</option>
            </select>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end pt-4 border-t">
          <button
            onClick={() => alert("Profile saved!")}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors font-medium"
          >
            Save Changes
          </button>
        </div>
      </div>

      {/* Password Change Section */}
      <div className="border rounded-lg bg-card p-6 space-y-4">
        <h2 className="text-lg font-medium">Change Password</h2>
        
        <div className="space-y-4">
          <div>
            <label htmlFor="currentPassword" className="block text-sm font-medium mb-1">Current Password</label>
            <input
              type="password"
              id="currentPassword"
              placeholder="Enter your current password"
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          <div>
            <label htmlFor="newPassword" className="block text-sm font-medium mb-1">New Password</label>
            <input
              type="password"
              id="newPassword"
              placeholder="Enter your new password"
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium mb-1">Confirm New Password</label>
            <input
              type="password"
              id="confirmPassword"
              placeholder="Confirm your new password"
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          {/* Change Password Button */}
          <div className="flex justify-end pt-4 border-t">
            <button
              onClick={() => alert("Password changed successfully!")}
              className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors font-medium"
            >
              Change Password
            </button>
          </div>
        </div>
      </div>

      {/* Account Actions */}
      <div className="border rounded-lg bg-card p-6 space-y-4">
        <h2 className="text-lg font-medium">Account Settings</h2>
        
        <div className="space-y-3">
          <button
            onClick={() => alert("Preferences panel would open here")}
            className="w-full px-4 py-2 border rounded-md hover:bg-muted transition-colors text-left"
          >
            Preferences & Notifications
          </button>

          <button
            onClick={() => alert("Account settings would open here")}
            className="w-full px-4 py-2 border rounded-md hover:bg-muted transition-colors text-left"
          >
            Account Settings
          </button>

          <div className="flex items-center justify-between pt-4 border-t">
            <span className="text-sm font-medium">Delete Account</span>
            <button
              onClick={() => alert("This would permanently delete your account. This action cannot be undone.")}
              className="px-4 py-2 bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90 transition-colors font-medium"
            >
              Delete Account
            </button>
          </div>
        </div>
      </div>

      {/* User Info Footer */}
      <div className="flex items-center justify-between p-4 border rounded-md bg-muted/20">
        <p className="text-sm text-muted-foreground">View your account information and settings</p>
        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-secondary">Viewer Role</span>
      </div>
    </div>
  );
}

export default ProfileView;
