import { useState } from "react";
import { lmstudioApi, ModelInfo, LmStudioStatus } from "../../api/lmstudio";
import StatusBadge from "../dashboard/StatusBadge";

interface LMStudioModelCardProps {
  model: ModelInfo;
}

function LMStudioModelCard({ model }: LMStudioModelCardProps) {
  const statusColors: Record<string, string> = {
    TEXT: "bg-blue-100 text-blue-800 border-blue-300",
    VISION: "bg-purple-100 text-purple-800 border-purple-300",
    MULTIMODAL: "bg-pink-100 text-pink-800 border-pink-300",
    UNKNOWN: "bg-gray-100 text-gray-800 border-gray-300",
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4 border border-gray-200">
      <h3 className="text-lg font-semibold mb-2">{model.name || model.id}</h3>
      <p className="text-sm text-gray-600 mb-1">ID: {model.id}</p>
      <p className="text-sm text-gray-600 mb-1">Type: {model.type || "N/A"}</p>
      <p className="text-sm text-gray-500 mb-2">Organization: {model.organization || "N/A"}</p>
      
      <div className="flex items-center justify-between mt-3">
        <span className={`px-2 py-1 rounded text-xs font-medium border ${statusColors[model.classification || "UNKNOWN"]}`}>
          {model.classification || "UNKNOWN"}
        </span>
        {model.size_gb && (
          <span className="text-sm text-gray-500">{model.size_gb.toFixed(2)} GB</span>
        )}
      </div>
    </div>
  );
}

interface LMStudioLoadedModelCardProps {
  model: ModelInfo;
}

function LMStudioLoadedModelCard({ model }: LMStudioLoadedModelCardProps) {
  const statusColors: Record<string, string> = {
    TEXT: "bg-green-100 text-green-800 border-green-300",
    VISION: "bg-purple-100 text-purple-800 border-purple-300",
    MULTIMODAL: "bg-pink-100 text-pink-800 border-pink-300",
    UNKNOWN: "bg-gray-100 text-gray-800 border-gray-300",
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4 border border-green-200">
      <h3 className="text-lg font-semibold mb-2 flex items-center">
        {model.name || model.id}
        <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full font-medium border border-green-300">
          Loaded
        </span>
      </h3>
      <p className="text-sm text-gray-600 mb-1">ID: {model.id}</p>
      <p className="text-sm text-gray-600 mb-1">Type: {model.type || "N/A"}</p>
      <p className="text-sm text-gray-500 mb-2">Organization: {model.organization || "N/A"}</p>
      
      <div className="flex items-center justify-between mt-3">
        <span className={`px-2 py-1 rounded text-xs font-medium border ${statusColors[model.classification || "UNKNOWN"]}`}>
          {model.classification || "UNKNOWN"}
        </span>
        {model.size_gb && (
          <span className="text-sm text-gray-500">{model.size_gb.toFixed(2)} GB</span>
        )}
      </div>
    </div>
  );
}

export default function LMStudioManagerPage() {
  const [serverStatus, setServerStatus] = useState<LmStudioStatus>({
    success: true,
    server_status: "disconnected",
    server_url: "http://localhost:1234",
    response_time_ms: undefined,
    last_health_check: undefined,
    error_message: undefined,
  });

  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loadedModels, setLoadedModels] = useState<ModelInfo[]>([]);
  const [textTestResponse, setTextTestResponse] = useState<{ response?: string; error?: string }>({});
  const [visionTestResponse, setVisionTestResponse] = useState<{ response?: string; error?: string }>({});
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchStatus = async () => {
    try {
      const status = await lmstudioApi.getStatus();
      setServerStatus(status);
    } catch (err) {
      console.error("Failed to fetch LM Studio status:", err);
      setServerStatus({
        ...serverStatus,
        server_status: "unavailable",
        error_message: "Failed to connect to LM Studio API",
      });
    }
  };

  const fetchModels = async () => {
    try {
      const response = await lmstudioApi.getModels();
      setModels(response.models || []);
    } catch (err) {
      console.error("Failed to fetch models:", err);
    }
  };

  const fetchLoadedModels = async () => {
    try {
      const response = await lmstudioApi.getLoadedModels();
      setLoadedModels(response.loaded_models || []);
    } catch (err) {
      console.error("Failed to fetch loaded models:", err);
    }
  };

  const testTextModel = async () => {
    setIsRefreshing(true);
    try {
      const response = await lmstudioApi.testTextModel({
        prompt: "This is a text model test. Please confirm you received this message.",
      });
      
      setTextTestResponse({
        response: response.response || "",
        error: response.error_message,
      });
    } catch (err) {
      console.error("Failed to test text model:", err);
      setTextTestResponse({
        error: "Text model test failed",
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  const testVisionModel = async () => {
    setIsRefreshing(true);
    try {
      const response = await lmstudioApi.testVisionModel({
        image: "ai_agents/screenshots/test_ui_0.png",
        prompt: "Analyze this UI screenshot and describe what you see.",
      });
      
      setVisionTestResponse({
        response: response.response || "",
        error: response.error_message,
      });
    } catch (err) {
      console.error("Failed to test vision model:", err);
      setVisionTestResponse({
        error: "Vision model test failed",
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    await fetchStatus();
    await fetchModels();
    await fetchLoadedModels();
  };

  // Initial status fetch on mount (called via useEffect in main App or parent component)
  // NOTE: Individual calls to fetchStatus() can be triggered by user action or external events.

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">LM Studio Manager</h1>
          <p className="text-gray-600 mt-2">Monitor and manage your local LM Studio server and models.</p>
        </div>

        {/* Server Status */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6 border border-gray-200">
          <h2 className="text-xl font-semibold mb-4">Server Status</h2>
          
          <div className="flex items-center gap-4 mb-4">
            <StatusBadge status={serverStatus.server_status} />
            <div>
              <p className="font-medium">
                {serverStatus.server_status === "connected" 
                  ? "Connected" 
                  : serverStatus.server_status === "disconnected"
                  ? "Disconnected"
                  : "Unavailable"}
              </p>
              <p className="text-sm text-gray-500">{serverStatus.server_url || "N/A"}</p>
            </div>
          </div>

          {serverStatus.response_time_ms !== undefined && serverStatus.response_time_ms > 0 && (
            <div className="text-sm text-gray-600">
              Response Time: {(serverStatus.response_time_ms).toFixed(2)} ms
            </div>
          )}
          
          {serverStatus.last_health_check && (
            <div className="text-sm text-gray-500 mt-1">
              Last Health Check: {new Date(serverStatus.last_health_check!).toLocaleString()}
            </div>
          )}

          {serverStatus.error_message && (
            <div className="mt-3 p-3 bg-yellow-50 text-yellow-800 rounded text-sm border border-yellow-200">
              {serverStatus.error_message}
            </div>
          )}
        </div>

        {/* Models Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          
          {/* Available Models */}
          <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <span className="mr-2">📦</span> Available Models
            </h2>
            <p className="text-sm text-gray-500 mb-4">All models installed on LM Studio server.</p>
            
            {models.length === 0 ? (
              <div className="text-gray-500 text-sm">No models detected yet. Load a model in LM Studio first.</div>
            ) : (
              <div className="space-y-3">
                {models.slice(0, 10).map((model) => (
                  <LMStudioModelCard key={model.id} model={model} />
                ))}
                {models.length > 10 && (
                  <div className="text-sm text-gray-500 text-center">
                    And {models.length - 10} more models...
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Loaded Models */}
          <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <span className="mr-2">🟢</span> Currently Loaded
            </h2>
            <p className="text-sm text-gray-500 mb-4">Models currently loaded into memory.</p>
            
            {loadedModels.length === 0 ? (
              <div className="text-gray-500 text-sm">No models currently loaded. Click "Refresh" to check again.</div>
            ) : (
              <div className="space-y-3">
                {loadedModels.slice(0, 10).map((model) => (
                  <LMStudioLoadedModelCard key={model.id} model={model} />
                ))}
                {loadedModels.length > 10 && (
                  <div className="text-sm text-gray-500 text-center">
                    And {loadedModels.length - 10} more models...
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Model Test Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          
          {/* Text Model Test */}
          <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <span className="mr-2">📝</span> Text Model Test (Qwen 3.5)
            </h2>
            <p className="text-sm text-gray-500 mb-4">Send a simple text prompt to the configured text model.</p>
            
            <div className="flex items-center gap-3 mb-4">
              <button
                onClick={testTextModel}
                disabled={isRefreshing}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isRefreshing ? "Testing..." : "Test Text Model"}
              </button>
            </div>

            {textTestResponse.response && (
              <div className="mt-4 p-3 bg-gray-50 rounded text-sm border border-gray-200">
                <p className="font-medium mb-1">Response:</p>
                <p className="whitespace-pre-wrap">{textTestResponse.response}</p>
              </div>
            )}
            
            {textTestResponse.error && (
              <div className="mt-4 p-3 bg-red-50 text-red-800 rounded text-sm border border-red-200">
                {textTestResponse.error}
              </div>
            )}

            <div className="mt-4 p-3 bg-blue-50 text-blue-800 rounded text-xs border border-blue-200">
              💡 Note: Qwen 3.5 is TEXT-ONLY. Never send images to this model.
            </div>
          </div>

          {/* Vision Model Test */}
          <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <span className="mr-2">👁️</span> Vision Model Test (Qwen-VL)
            </h2>
            <p className="text-sm text-gray-500 mb-4">Send an image plus prompt to the vision model.</p>
            
            <div className="flex items-center gap-3 mb-4">
              <button
                onClick={testVisionModel}
                disabled={isRefreshing}
                className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isRefreshing ? "Testing..." : "Test Vision Model"}
              </button>
            </div>

            {visionTestResponse.response && (
              <div className="mt-4 p-3 bg-gray-50 rounded text-sm border border-gray-200">
                <p className="font-medium mb-1">Response:</p>
                <p className="whitespace-pre-wrap">{visionTestResponse.response}</p>
              </div>
            )}
            
            {visionTestResponse.error && (
              <div className="mt-4 p-3 bg-red-50 text-red-800 rounded text-sm border border-red-200">
                {visionTestResponse.error}
              </div>
            )}

            <div className="mt-4 p-3 bg-purple-50 text-purple-800 rounded text-xs border border-purple-200">
              💡 Use this model for UI/image analysis. Qwen-VL or similar vision models only.
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4 mb-6">
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Refresh
          </button>
        </div>

        {/* Logs */}
        <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <span className="mr-2">📋</span> Event Logs
          </h2>
          <p className="text-sm text-gray-500 mb-4">Recent LM Studio-related events.</p>
          
          {serverStatus.server_status === "connected" && (
            <div className="text-sm text-gray-600 p-3 bg-green-50 border border-green-200 rounded">
              ✓ Server is healthy and responding to requests.
            </div>
          )}

          {serverStatus.server_status === "disconnected" && (
            <div className="text-sm text-gray-600 p-3 bg-yellow-50 border border-yellow-200 rounded">
              ⚠ Server appears to be disconnected. Check if LM Studio is running.
            </div>
          )}

          {serverStatus.server_status === "unavailable" && (
            <div className="text-sm text-gray-600 p-3 bg-red-50 border border-red-200 rounded">
              ✗ Server unavailable. Please verify LM Studio installation and configuration.
            </div>
          )}

          {loadedModels.length > 0 && (
            <div className="text-sm text-gray-600 mt-2 p-3 bg-blue-50 border border-blue-200 rounded">
              ✓ {loadedModels.length} model(s) loaded into memory.
            </div>
          )}

          {models.length > 0 && (
            <div className="text-sm text-gray-600 mt-2 p-3 bg-purple-50 border border-purple-200 rounded">
              ✓ {models.length} model(s) available on server.
            </div>
          )}

          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-sm">
            <div className="p-3 bg-gray-50 rounded border border-gray-200">
              <strong className="block text-gray-700">Text Model:</strong> 
              {serverStatus.text_model || "Qwen 3.5 (default)"}
            </div>
            <div className="p-3 bg-gray-50 rounded border border-gray-200">
              <strong className="block text-gray-700">Vision Model:</strong> 
              {serverStatus.vision_model || "Qwen-VL (default)"}
            </div>
            <div className="p-3 bg-gray-50 rounded border border-gray-200">
              <strong className="block text-gray-700">Base URL:</strong> {serverStatus.server_url || "http://localhost:1234"}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
