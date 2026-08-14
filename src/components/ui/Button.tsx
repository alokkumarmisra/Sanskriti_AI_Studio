/**
 * Global Reusable Button Component with Semantic Variants
 * 
 * Usage:
 * <Button variant="primary">Add Project</Button>
 * <Button variant="danger">Delete</Button>
 * <Button variant="secondary">Cancel</Button>
 */

import React from "react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Button semantic variant - see variants below */
  variant?: 
    | "primary"      // Green - Add/Save/Create/Success
    | "success"      // Green - Same as primary, for success actions
    | "danger"       // Red - Delete/Destructive/Cancel
    | "edit"         // Blue - Edit/Open/View
    | "info"         // Blue - General information/actions
    | "ai"           // Purple - AI/Generate actions
    | "warning"      // Orange - Warning/Stop actions
    | "amber"        // Yellow/Amber - Warning states
    | "secondary"    // Gray - Secondary actions
    | "ghost"        // Ghost button (transparent with hover)
    | "link";        // Link-style text

  /** Size: small, medium, large */
  size?: "sm" | "md" | "lg";
  
  /** Shows loading spinner */
  isLoading?: boolean;
}

const variantStyles: Record<string, { bg: string, hoverBg: string, textColor?: string }> = {
  primary: { bg: "bg-green-600", hoverBg: "hover:bg-green-700" },
  success: { bg: "bg-green-600", hoverBg: "hover:bg-green-700" },
  danger: { bg: "bg-red-600", hoverBg: "hover:bg-red-700" },
  edit: { bg: "bg-blue-600", hoverBg: "hover:bg-blue-700" },
  info: { bg: "bg-blue-600", hoverBg: "hover:bg-blue-700" },
  ai: { bg: "bg-purple-600", hoverBg: "hover:bg-purple-700" },
  warning: { bg: "bg-orange-600", hoverBg: "hover:bg-orange-700" },
  amber: { bg: "bg-amber-600", hoverBg: "hover:bg-amber-700" },
  secondary: { 
    bg: "bg-gray-100 border border-gray-300 text-gray-900",
    hoverBg: "hover:bg-gray-200"
  },
  ghost: { bg: "", hoverBg: "hover:bg-gray-100" },
  link: { bg: "", hoverBg: "", textColor: "text-blue-600 hover:text-blue-800 underline-offset-2 hover:underline" }
};

const sizeStyles: Record<string, { py: string, px: string, textSm?: boolean }> = {
  sm: { py: "py-1.5", px: "px-3", textSm: true },
  md: { py: "py-2", px: "px-4" },
  lg: { py: "py-2.5", px: "px-6", textSm: false }
};

export function Button({ 
  variant = "primary",
  size = "md",
  className = "",
  children,
  isLoading,
  disabled,
  ...props 
}: ButtonProps) {
  const style = variantStyles[variant];
  const sStyle = sizeStyles[size];

  // Determine if we have a colored background or text-link style
  const hasBackground = ["primary", "success", "danger", "edit", "info", "ai", "warning", "amber", "secondary"].includes(variant);
  const isGhostOrLink = variant === "ghost" || variant === "link";

  return (
    <button
      className={`
        inline-flex items-center justify-center font-medium rounded-md 
        transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2
        disabled:opacity-50 disabled:cursor-not-allowed
        ${hasBackground ? style.bg + " " + style.hoverBg : ""}
        ${isGhostOrLink ? variant === 'link' ? style.textColor : '' : ''}
        ${sStyle.py} ${sStyle.px}
        ${isGhostOrLink ? className : ""}
      `}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      )}
      {children}
    </button>
  );
}

export default Button;
