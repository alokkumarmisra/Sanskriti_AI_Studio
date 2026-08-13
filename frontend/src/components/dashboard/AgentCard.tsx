/** Agent Card Component for Agent Monitoring Dashboard */

import React from "react";
import { StatusBadge } from "./StatusBadge";
import { ProgressBar } from "./ProgressBar";
import type { AgentListItem } from "../../types/agent-dashboard";

interface AgentCardProps {
  agent: AgentListItem;
  onClick?: () => void;
}

export const AgentCard: React.FC<AgentCardProps> = ({ agent, onClick }) => {
  return (
    <div 
      className="bg-white border border-gray-200 rounded-lg p-4 hover:border-indigo-300 transition-colors cursor-pointer shadow-sm hover:shadow-md"
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">{agent.name}</h3>
          <p className="text-sm text-gray-500 mt-1 truncate">{agent.description}</p>
        </div>
        <StatusBadge status={agent.status} />
      </div>

      {/* Task Info */}
      {agent.current_task && (
        <div className="mb-3 p-2 bg-gray-50 rounded-md">
          <p className="text-sm text-gray-700 truncate">{agent.current_task}</p>
        </div>
      )}

      {/* Progress Bar */}
      {agent.progress > 0 && (
        <div className="mb-3">
          <ProgressBar progress={agent.progress} color={agent.status === "running" ? "indigo" : "gray"} label={`${Math.round(agent.progress)}%`} />
        </div>
      )}

      {/* Timestamp */}
      {agent.started_at && (
        <div className="text-xs text-gray-400">
          Started: {new Date(agent.started_at).toLocaleTimeString()}
        </div>
      )}

      {/* Duration */}
      {agent.elapsed_seconds > 0 && (
        <div className="text-xs text-gray-400">
          Elapsed: {Math.floor(agent.elapsed_seconds / 60)}m {agent.elapsed_seconds % 60}s
        </div>
      )}

      {/* Error Indicator */}
      {agent.last_error && (
        <div className="mt-2 p-2 bg-red-50 text-sm text-red-700 rounded-md">
          <strong>Error:</strong> {agent.last_error.substring(0, 100)}...
        </div>
      )}
    </div>
  );
};

export default AgentCard;
