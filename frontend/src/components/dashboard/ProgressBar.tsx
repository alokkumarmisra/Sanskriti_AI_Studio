/** Progress Bar Component for Agent Monitoring Dashboard */

import React from "react";

interface ProgressBarProps {
  progress: number; // 0-100
  size?: "sm" | "md" | "lg";
  color?: "indigo" | "green" | "yellow" | "red" | "blue" | "gray";
  label?: string;
}

const COLOR_CONFIG: Record<string, string> = {
  indigo: "bg-indigo-600",
  green: "bg-green-600",
  yellow: "bg-yellow-500",
  red: "bg-red-600",
  blue: "bg-blue-600",
  gray: "bg-gray-600",
};

export const ProgressBar: React.FC<ProgressBarProps> = ({ 
  progress, 
  size = "md", 
  color = "indigo",
  label 
}) => {
  const width = Math.min(Math.max(progress, 0), 100);
  
  return (
    <div className="w-full">
      {label && (
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-gray-700">{label}</span>
          <span className="text-sm text-gray-500">{Math.round(progress)}%</span>
        </div>
      )}
      <div className={`w-full bg-gray-200 rounded-full overflow-hidden ${size}`}>
        <div
          className={`${COLOR_CONFIG[color]} h-full rounded-full transition-all duration-500 ease-out`}
          style={{ width: `${width}%` }}
          role="progressbar"
          aria-valuenow={width}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  );
};

export default ProgressBar;
