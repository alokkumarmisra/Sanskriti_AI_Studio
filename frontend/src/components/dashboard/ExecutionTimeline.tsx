/** Execution Timeline Component for Agent Monitoring Dashboard */

import React from "react";
import type { ExecutionHistoryItem } from "../../types/agent-dashboard";

interface ExecutionTimelineProps {
  timeline: ExecutionHistoryItem[];
}

const AGENT_COLORS: Record<string, string> = {
  orchestrator: "bg-blue-100 text-blue-800 border-blue-300",
  planner: "bg-purple-100 text-purple-800 border-purple-300",
  coder_agent: "bg-indigo-100 text-indigo-800 border-indigo-300",
  tester_agent: "bg-green-100 text-green-800 border-green-300",
  reviewer_agent: "bg-yellow-100 text-yellow-800 border-yellow-300",
  vision_agent: "bg-pink-100 text-pink-800 border-pink-300",
  debugger_agent: "bg-orange-100 text-orange-800 border-orange-300",
};

// Helper to convert snake_case to Title Case
const toTitleCase = (str: string): string => {
  return str.toLowerCase().split("_").map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(" ");
};

export const ExecutionTimeline: React.FC<ExecutionTimelineProps> = ({ timeline }) => {
  if (!timeline || timeline.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No execution history available yet.
      </div>
    );
  }

  return (
    <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2">
      {timeline.map((event, index) => (
        <div 
          key={`${event.timestamp}-${index}`}
          className="flex gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
        >
          {/* Timestamp */}
          <div className="flex-shrink-0">
            <span className="text-xs font-mono text-gray-500">{event.timestamp}</span>
          </div>

          {/* Connector Line */}
          {index < timeline.length - 1 && (
            <div className="flex-shrink-0 w-px bg-gray-300 my-1"></div>
          )}

          {/* Event Content */}
          <div className="flex-1 min-w-0">
            {/* Agent Badge */}
            <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium border ${AGENT_COLORS[event.agent] || "bg-gray-100 text-gray-800 border-gray-300"}`}>
              {toTitleCase(event.agent)}
            </span>

            {/* Event Type */}
            <p className="text-sm font-medium text-gray-900 mt-1">
              {event.event}
            </p>

            {/* Details */}
            {event.details && (
              <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                {event.details}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default ExecutionTimeline;
