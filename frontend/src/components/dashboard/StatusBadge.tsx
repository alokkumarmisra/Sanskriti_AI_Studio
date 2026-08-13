/** Status Badge Component for Agent Monitoring Dashboard */

import React from "react";

type StatusType = 
  | "idle" 
  | "queued" 
  | "running" 
  | "completed" 
  | "failed" 
  | "paused"
  | "waiting_for_approval"
  | "skipped"
  | "cancelled"
  | "unknown";

interface StatusBadgeProps {
  status: string;
  size?: "sm" | "md" | "lg";
}

const STATUS_CONFIG: Record<string, { color: string; label: string }> = {
  idle: { color: "bg-gray-100 text-gray-800", label: "Idle" },
  queued: { color: "bg-blue-100 text-blue-800", label: "Queued" },
  running: { color: "bg-green-100 text-green-800", label: "Running" },
  completed: { color: "bg-emerald-100 text-emerald-800", label: "Completed" },
  failed: { color: "bg-red-100 text-red-800", label: "Failed" },
  paused: { color: "bg-yellow-100 text-yellow-800", label: "Paused" },
  waiting_for_approval: { color: "bg-purple-100 text-purple-800", label: "Waiting for Approval" },
  skipped: { color: "bg-gray-100 text-gray-600", label: "Skipped" },
  cancelled: { color: "bg-slate-100 text-slate-600", label: "Cancelled" },
  unknown: { color: "bg-gray-100 text-gray-500", label: "" },
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = "md" }) => {
  const config = STATUS_CONFIG[status.toLowerCase()] || STATUS_CONFIG.unknown;
  
  const sizeClasses = {
    sm: "text-xs px-2 py-1",
    md: "text-sm px-3 py-1.5",
    lg: "text-base px-4 py-2",
  };

  return (
    <span className={`${config.color} ${sizeClasses[size]} rounded-full font-medium inline-flex items-center gap-1`}>
      {status !== "unknown" && config.label && <span>{config.label}</span>}
    </span>
  );
};

export default StatusBadge;
