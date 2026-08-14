// Tailwind CSS v3 configuration
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Semantic button colors per design system
        add: "#16A34A",         // Green - Add/Create/Save actions
        "add-hover": "#15803D", 
        delete: "#DC2626",      // Red - Delete/Destructive actions  
        "delete-hover": "#B91C1C",
        edit: "#2563EB",        // Blue - Edit/Open/View actions
        "edit-hover": "#1D4ED8",
        ai: "#7C3AED",          // Purple - AI/Generate actions
        "ai-hover": "#6D28D9",
        stop: "#EA580C",        // Orange - Stop/Cancel execution
        warning: "#D97706",     // Amber/Yellow - Warning states
        secondary: "#F3F4F6",   // Light gray - Secondary actions
        "secondary-dark": "#111827",
      },
    },
  },
  darkMode: 'media',
};
