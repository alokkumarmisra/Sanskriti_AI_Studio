/** Log Viewer Component for Agent Monitoring Dashboard */

import React, { useState } from "react";
import type { LogEntry } from "../../types/agent-dashboard";

interface LogViewerProps {
  logs: LogEntry[];
  agent?: string;
}

const LEVEL_COLORS: Record<string, string> = {
  INFO: "text-blue-600",
  WARNING: "text-yellow-600",
  ERROR: "text-red-600",
  CRITICAL: "text-purple-600",
};

interface LogLineProps {
  entry: LogEntry;
}

const LogLine: React.FC<LogLineProps> = ({ entry }) => {
  return (
    <div className="flex gap-3 p-2 border-b border-gray-100 hover:bg-gray-50">
      <span className={`text-xs font-mono text-gray-500 whitespace-nowrap`}>{entry.timestamp}</span>
      <span className={`text-xs font-bold ${LEVEL_COLORS[entry.level] || "text-gray-500"}`}>[{entry.level}]</span>
      <span className="text-sm text-gray-800 flex-1">{entry.message}</span>
    </div>
  );
};

export const LogViewer: React.FC<LogViewerProps> = ({ logs, agent }) => {
  const [filter, setFilter] = useState("all");

  const filteredLogs = filter === "all" 
    ? logs 
    : logs.filter(log => log.level.toUpperCase() === filter.toUpperCase());

  return (
    <div className="bg-gray-900 rounded-lg p-4 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-white font-semibold flex items-center gap-2">
          <span className="w-2 h-2 bg-green-500 rounded-full"></span>
          {agent || "Logs"}
        </h3>
        {/* Filter Buttons */}
        <div className="flex gap-1">
          {["all", "info", "warning", "error", "critical"].map(level => (
            <button
              key={level}
              onClick={() => setFilter(level)}
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                filter === level
                  ? "bg-white text-gray-900"
                  : "bg-gray-700 text-gray-300 hover:bg-gray-600"
              }`}
            >
              {level.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Log Lines */}
      <div className="font-mono text-sm max-h-[400px] overflow-y-auto">
        {filteredLogs.length > 0 ? (
          filteredLogs.map((log, index) => (
            <LogLine key={`${log.timestamp}-${index}`} entry={log} />
          ))
        ) : (
          <div className="text-gray-400 text-center py-8">No logs available</div>
        )}
      </div>

      {/* Footer Info */}
      {logs.length > 0 && (
        <div className="mt-2 text-xs text-gray-400 text-right">
          Showing {filteredLogs.length} of {logs.length} lines
        </div>
      )}
    </div>
  );
};

export default LogViewer;
