import React, { useState, useEffect } from "react";
import comfyuiApi from "@/api/comfyui";
import StatusBadge from "./StatusBadge";

interface ComfyUIManagerState {
  serverStatus: "connected" | "disconnected" | "unavailable" | null;
  serverUrl: string;
  version: string | null;
  responseTimeMs: number | null;
  gpuName: string | null;
  vramTotalGb: number | null;
  vramUsedGb: number | null;
  totalRunning: number;
  totalPending: number;
  totalCompleted: number;
  totalFailed: number;
  workflows: Array<{ id: string; filename: string; status: string }> | [];
}

const ComfyUIManagerPage: React.FC = () => {
  const [state, setState] = useState<ComfyUIManagerState>({
    serverStatus: "disconnected",
    serverUrl: "",
    version: null,
    responseTimeMs: null,
    gpuName: null,
    vramTotalGb: null,
    vramUsedGb: null,
    totalRunning: 0,
    totalPending: 0,
    totalCompleted: 0,
    totalFailed: 0,
    workflows: [],
  });

  const [queueData, setQueueData] = useState<any>({ running: [], pending: [], completed: [], failed: [] });
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);
  const [historyLimit, setHistoryLimit] = useState(20);

  // Health check on mount and every 10 seconds
  useEffect(() => {
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      await comfyuiApi.healthCheck();
      setState(prev => ({ ...prev, serverStatus: prev.serverStatus === "disconnected" ? "connected" : prev.serverStatus }));
    } catch (e) {
      console.error("Health check failed:", e);
    }
  };

  const loadSystemInfo = async () => {
    try {
      const data = await comfyuiApi.getSystemInfo();
      setState(prev => ({
        ...prev,
        version: data.version,
        gpuName: (data.gpu_info as any).name || null,
        vramTotalGb: (data.gpu_info as any).vram_total_mb ? ((data.gpu_info as any).vram_total_mb / 1024) : null,
        vramUsedGb: (data.gpu_info as any).vram_used_mb ? Math.round(((data.gpu_info as any).vram_used_mb / 1024) * 100) / 100 : null,
      }));
    } catch (e) {
      console.error("Failed to load system info:", e);
    }
  };

  const loadQueueData = async () => {
    try {
      const data = await comfyuiApi.getQueueStatus();
      setQueueData(data);
    } catch (e) {
      console.error("Failed to load queue data:", e);
    }
  };

  const loadWorkflows = async () => {
    try {
      const data = await comfyuiApi.getWorkflowHistory(historyLimit);
      setState(prev => ({
        ...prev,
        workflows: (data.workflows || []).map((w: any) => ({
          id: w.id,
          filename: w.filename,
          status: w.status,
        })),
      }));
    } catch (e) {
      console.error("Failed to load workflow history:", e);
    }
  };

  const submitWorkflow = async (workflowJson: string) => {
    try {
      const result = await comfyuiApi.submitWorkflow(workflowJson, {});
      
      if (result.success && result.job_id) {
        alert(`Workflow submitted! Job ID: ${result.job_id}`);
      } else {
        alert(`Failed to submit workflow: ${result.error_message || "Unknown error"}`);
      }
    } catch (e: any) {
      alert(`Error submitting workflow: ${e.message || e}`);
    }
  };

  const handleWorkflowSelect = async (workflowId: string) => {
    try {
      const details = await comfyuiApi.getJobDetails(workflowId);
      if (details.success) {
        setSelectedWorkflow(details.workflow);
      }
    } catch (e) {
      console.error("Failed to select workflow:", e);
    }
  };

  const handleWorkflowRun = async (workflowId: string) => {
    try {
      const details = await comfyuiApi.getJobDetails(workflowId);
      if (details.success) {
        alert(`To run this workflow, you need to extract its JSON and submit it via POST /api/v1/dashboard/comfyui/submit`);
      } else {
        throw new Error("Could not get workflow details");
      }
    } catch (e) {
      console.error("Failed to run workflow:", e);
      alert(`Error: ${e}`);
    }
  };

  return (
    <div className="comfyui-manager">
      <h1>ComfyUI Manager</h1>

      {/* Server Status */}
      <div className="server-status-section">
        <h2>Server Status</h2>
        <div className="status-grid">
          <div className="status-item">
            <span className="label">Connected</span>
            <StatusBadge status={state.serverStatus || "disconnected"} />
          </div>
          <div className="status-item">
            <span className="label">URL</span>
            <span className="value">{state.serverUrl}</span>
          </div>
          <div className="status-item">
            <span className="label">Version</span>
            <span className="value">{state.version || "N/A"}</span>
          </div>
          <div className="status-item">
            <span className="label">Response Time</span>
            <span className="value">{state.responseTimeMs?.toFixed(2) ?? "0"} ms</span>
          </div>
        </div>

        {/* GPU Information */}
        <div className="gpu-section">
          <h3>GPU Information</h3>
          <div className="info-grid">
            <div className="info-item">
              <span className="label">GPU Name</span>
              <span className="value">{state.gpuName || "N/A"}</span>
            </div>
            <div className="info-item">
              <span className="label">VRAM Total</span>
              <span className="value">{state.vramTotalGb?.toFixed(2) || 0} GB</span>
            </div>
            <div className="info-item">
              <span className="label">VRAM Used</span>
              <span className="value">{state.vramUsedGb || 0} GB</span>
            </div>
          </div>
        </div>
      </div>

      {/* Queue Monitoring */}
      <div className="queue-section">
        <h2>Queue</h2>
        <div className="status-bar">
          <span>Running: <strong>{state.totalRunning}</strong></span>
          <span>Pending: <strong>{state.totalPending}</strong></span>
          <span>Completed: <strong>{state.totalCompleted}</strong></span>
          <span>Failed: <strong>{state.totalFailed}</strong></span>
        </div>

        {/* Running Jobs */}
        {queueData.running.length > 0 && (
          <div className="queue-list">
            <h3>Running Jobs</h3>
            <ul>
              {queueData.running.map((job: any) => (
                <li key={job.id} className="queue-item running">
                  <span className="title">{job.title}</span>
                  <span className="status-badge status-running">{job.status}</span>
                  <span className="progress">Progress: {job.progress || "N/A"}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Pending Jobs */}
        {queueData.pending.length > 0 && (
          <div className="queue-list">
            <h3>Pending Jobs</h3>
            <ul>
              {queueData.pending.map((job: any) => (
                <li key={job.id} className="queue-item pending">
                  <span className="title">{job.title}</span>
                  <span className="status-badge status-pending">{job.status}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Workflow History */}
      <div className="workflows-section">
        <h2>Workflow History</h2>
        
        <div className="workflow-actions">
          <label className="limit-label">
            Show:
            <select 
              value={historyLimit} 
              onChange={(e) => setHistoryLimit(parseInt(e.target.value))}
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
          </label>
          <button onClick={loadWorkflows} className="refresh-btn">Refresh Workflows</button>
        </div>

        {state.workflows.length > 0 ? (
          <div className="workflows-list">
            {state.workflows.map((wf: any) => (
              <div key={wf.id} className="workflow-item" onClick={() => handleWorkflowSelect(wf.id)}>
                <span className="workflow-id">{wf.id}</span>
                <span className="workflow-filename">{wf.filename}</span>
                <StatusBadge status={wf.status} />
              </div>
            ))}
          </div>
        ) : (
          <p className="no-workflows">No workflows in history yet.</p>
        )}
      </div>
    </div>
  );
};

export default ComfyUIManagerPage;
