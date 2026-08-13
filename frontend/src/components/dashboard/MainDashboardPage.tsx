/** Main Agent Monitoring Dashboard Page Component */

import React, { useEffect, useState } from "react";
import { dashboardAPI } from "../../api/dashboard";
import type { AgentListItem, ActivityStreamResponse, ExecutionHistoryItem, LogEntry } from "../../types/agent-dashboard";
import { StatusBadge } from "./StatusBadge";
import { ProgressBar } from "./ProgressBar";
import { AgentCard } from "./AgentCard";
import { ExecutionTimeline } from "./ExecutionTimeline";
import { LogViewer } from "./LogViewer";

interface MainDashboardPageProps {}

// Helper function to convert snake_case to Title Case
const toTitleCase = (str: string): string => {
  return str.toLowerCase().split("_").map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(" ");
};

// Define functions outside component scope for proper hoisting
const loadAllData = async (
  setAgents: React.Dispatch<React.SetStateAction<AgentListItem[]>>,
  setActivity: React.Dispatch<React.SetStateAction<ActivityStreamResponse>>,
  setHistory: React.Dispatch<React.SetStateAction<{ timeline: ExecutionHistoryItem[]; total_events: number }>>
) => {
  try {
    // Fetch agents
    const agentsData = await dashboardAPI.listAgents({ include_details: true });
    setAgents(agentsData.agents);
    
    // Fetch activity stream
    const activityData = await dashboardAPI.getActivityStream();
    setActivity(activityData);
    
    // Fetch history
    const historyData = await dashboardAPI.getExecutionHistory();
    setHistory(historyData);
  } catch (err) {
    console.error("Error loading dashboard data:", err);
  }
};

const loadActivityStream = async (setActivity: React.Dispatch<React.SetStateAction<ActivityStreamResponse>>) => {
  try {
    const data = await dashboardAPI.getActivityStream();
    setActivity(data);
  } catch (err) {
    // Silently fail activity updates
  }
};

export const MainDashboardPage: React.FC<MainDashboardPageProps> = () => {
  const [agents, setAgents] = useState<AgentListItem[]>([]);
  const [activity, setActivity] = useState<ActivityStreamResponse>({
    activities: [],
    count: 0,
    has_active_execution: false,
  });
  const [history, setHistory] = useState<{ timeline: ExecutionHistoryItem[]; total_events: number }>({
    timeline: [],
    total_events: 0,
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch all data on mount
  useEffect(() => {
    loadAllData(setAgents, setActivity, setHistory);
    
    // Poll for updates every 3 seconds
    const interval = setInterval(() => {
      loadActivityStream(setActivity);
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Agent Monitoring Dashboard</h1>
              <p className="text-sm text-gray-500 mt-1">Real-time monitoring of AI agent execution</p>
            </div>
            
            {/* Current Activity Status */}
            <div className="flex items-center gap-4">
              {activity.has_active_execution && (
                <div className="flex items-center gap-2 bg-green-100 text-green-800 px-3 py-1.5 rounded-full text-sm font-medium">
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                  Active: {toTitleCase(activity.activities[0]?.message || "Processing task")}
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-700">{error}</p>
          </div>
        ) : (
          <>
            {/* Activity Stream Panel */}
            {activity.count > 0 && (
              <div className="mb-6 bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <h2 className="text-lg font-semibold text-gray-900 mb-3">Current Activity</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {activity.activities.slice(0, 6).map((act, idx) => (
                    <div key={idx} className="flex items-start gap-2 p-3 bg-gray-50 rounded-lg">
                      <div className={`w-2 h-2 rounded-full ${
                        act.status === "running" || act.status === "in_progress" 
                          ? "bg-green-500 animate-pulse" 
                          : "bg-gray-400"
                      }`} />
                      <div>
                        <p className="text-sm font-medium text-gray-900">{toTitleCase(act.agent)}</p>
                        <p className="text-xs text-gray-600 truncate">{act.message}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Agents Grid */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Agents</h2>
                <span className="text-sm text-gray-500">{agents.length} agents</span>
              </div>
              
              {agents.length === 0 ? (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
                  <p className="text-gray-500 mb-2">No agent data available</p>
                  <p className="text-sm text-gray-400">Agents will appear when tasks are in progress</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {agents.map((agent) => (
                    <AgentCard 
                      key={agent.id} 
                      agent={agent} 
                      onClick={() => console.log("Viewing agent:", agent.id)} // TODO: Implement agent detail view
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Execution History */}
            <div className="mb-6 bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">Execution History</h2>
                <span className="text-sm text-gray-500">{history.total_events} events</span>
              </div>
              <ExecutionTimeline timeline={history.timeline} />
            </div>

            {/* Logs */}
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Agent Logs</h2>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Orchestrator Logs */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                  <div className="p-3 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
                    <h3 className="text-sm font-medium text-gray-700 flex items-center gap-2">
                      <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
                      Orchestrator Logs
                    </h3>
                  </div>
                  {/* TODO: Add logs fetch and LogViewer component */}
                  <div className="p-3 text-sm text-gray-500">Log data will appear here when tasks run</div>
                </div>

                {/* Planner Logs */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                  <div className="p-3 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
                    <h3 className="text-sm font-medium text-gray-700 flex items-center gap-2">
                      <span className="w-1.5 h-1.5 bg-purple-500 rounded-full"></span>
                      Planner Logs
                    </h3>
                  </div>
                  <div className="p-3 text-sm text-gray-500">Log data will appear here when tasks run</div>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Footer */}
        <footer className="mt-8 pt-4 border-t border-gray-200 text-center text-sm text-gray-500">
          <p>Agent Monitoring Dashboard v1.0 | Last update: {activity.count > 0 ? new Date().toLocaleTimeString() : "No data"}</p>
        </footer>
      </main>
    </div>
  );
};

export default MainDashboardPage;
