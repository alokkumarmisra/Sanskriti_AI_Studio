import { useState, useEffect } from "react";
import { modelManagementApi } from "../../api/model-management";

interface ModelInfo {
  id: string;
  name: string;
  type?: string;
  classification: string;
  size_gb?: number | null;
  organization?: string;
  format?: string;
  quantization?: string;
  source: "lmstudio" | "comfyui";
  application: "LM Studio" | "ComfyUI";
  status?: string;
  capabilities?: string[];
}

interface ModelCardProps {
  model: ModelInfo;
  onOpenDetails?: (model: ModelInfo) => void;
}

function ModelCard({ model, onOpenDetails }: ModelCardProps) {
  const statusColors: Record<string, string> = {
    TEXT: "bg-blue-100 text-blue-800 border-blue-300",
    VISION: "bg-purple-100 text-purple-800 border-purple-300",
    MULTIMODAL: "bg-pink-100 text-pink-800 border-pink-300",
    IMAGE_GENERATION: "bg-green-100 text-green-800 border-green-300",
    CHECKPOINT: "bg-orange-100 text-orange-800 border-orange-300",
    LORA: "bg-indigo-100 text-indigo-800 border-indigo-300",
    UNKNOWN: "bg-gray-100 text-gray-800 border-gray-300",
  };

  const typeColors: Record<string, string> = {
    lmstudio: "text-blue-600",
    comfyui: "text-purple-600",
  };

  return (
    <div onClick={() => onOpenDetails?.(model)} className="bg-white rounded-lg shadow-md p-4 border border-gray-200 hover:shadow-lg transition-shadow cursor-pointer">
      <h3 className="text-lg font-semibold mb-1 truncate">{model.name || model.id}</h3>
      <p className="text-sm text-gray-500 mb-1">ID: {model.id}</p>
      <div className="flex items-center gap-2 mb-2">
        <span className={`px-2 py-0.5 rounded text-xs font-medium border ${statusColors[model.classification] || statusColors.UNKNOWN}`}>{model.classification}</span>
        <span className={`text-xs px-2 py-0.5 rounded font-medium border ${typeColors[model.source]}`}>{model.application}</span>
      </div>
      <p className="text-sm text-gray-600 mb-1">Type: {model.type || "N/A"}</p>
      <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
        {model.organization && <span>Org: {model.organization}</span>}
        {model.size_gb && <span>{(model.size_gb / 1024).toFixed(2)} GB</span>}
      </div>
      {model.status === "loaded" && (
        <span className="inline-flex items-center gap-1 mt-2 px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full font-medium border border-green-300">✓ Loaded</span>
      )}
    </div>
  );
}

export default function ModelManagementPage() {
  const [inventory, setInventory] = useState<ModelInfo[]>([]);
  const [textModels, setTextModels] = useState<ModelInfo[]>([]);
  const [visionModels, setVisionModels] = useState<ModelInfo[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedModel, setSelectedModel] = useState<ModelInfo | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await modelManagementApi.getInventory(100);
        if (response.success && response.models) {
          setInventory(response.models as ModelInfo[]);
          const models = response.models as ModelInfo[];
          setTextModels(models.filter((m: ModelInfo) => m.classification === "TEXT" || m.source === "lmstudio"));
          setVisionModels(models.filter((m: ModelInfo) => m.classification === "VISION" || m.id.toLowerCase().includes("vision")));
        }
      } catch (err) {
        console.error("Failed to fetch inventory:", err);
      }
    };
    fetchStatus();
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const response = await modelManagementApi.getInventory(100);
      if (response.success && response.models) setInventory(response.models as ModelInfo[]);
      const textResp = await modelManagementApi.getTextModels();
      if (textResp.success && textResp.models) setTextModels(textResp.models as ModelInfo[]);
      const visionResp = await modelManagementApi.getVisionModels();
      if (visionResp.success && visionResp.models) setVisionModels(visionResp.models as ModelInfo[]);
    } catch (err) {
      console.error("Failed to refresh:", err);
    } finally {
      setIsRefreshing(false);
    }
  };

  const testTextModel = async () => {
    setIsRefreshing(true);
    try {
      const response = await modelManagementApi.testTextModel({ prompt: "This is a text model test. Please confirm you received this message." });
      alert(response.response || response.error_message || "");
    } catch (err) {
      console.error("Failed to test text model:", err);
    } finally {
      setIsRefreshing(false);
    }
  };

  const testVisionModel = async () => {
    setIsRefreshing(true);
    try {
      const response = await modelManagementApi.testVisionModel({ image: "ai_agents/screenshots/test_ui_0.png", prompt: "Analyze this UI screenshot and describe what you see." });
      alert(response.response || response.error_message || "");
    } catch (err) {
      console.error("Failed to test vision model:", err);
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">AI Model Management</h1>
          <p className="text-gray-600 mt-2">Unified view of all AI models used by LM Studio and ComfyUI.</p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200 mb-6">
          <h2 className="text-xl font-semibold mb-4">Configuration</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
            <div className="p-3 bg-gray-50 rounded border border-gray-200"><strong className="block text-gray-700">LM Studio:</strong>{' '}
              {inventory.length > 0 ? <span className="text-green-600">Connected</span> : <span className="text-red-600">Disconnected</span>}</div>
            <div className="p-3 bg-gray-50 rounded border border-gray-200"><strong className="block text-gray-700">Text Model:</strong>{' '}Qwen 3.5 (default)</div>
            <div className="p-3 bg-gray-50 rounded border border-gray-200"><strong className="block text-gray-700">Vision Model:</strong>{' '}Qwen-VL (default)</div>
          </div>
          <div className="mt-4 p-3 bg-purple-50 rounded border border-purple-200 text-sm"><strong>Total Models:</strong> {inventory.length} available</div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
            <h2 className="text-xl font-semibold mb-4">📦 Available Models</h2>
            <p className="text-sm text-gray-500 mb-4">All models installed on LM Studio server.</p>
            {inventory.length === 0 ? (
              <div className="text-gray-500 text-sm">No models detected yet. Load a model in LM Studio first.</div>
            ) : (
              <div className="space-y-3 max-h-[600px] overflow-y-auto">{inventory.slice(0, 20).map((model) => (<ModelCard key={model.id} model={model} onOpenDetails={setSelectedModel} />))}{inventory.length > 20 && (<div className="text-sm text-gray-500 text-center">And {inventory.length - 20} more...</div>)}</div>
            )}
          </div>

          <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
            <h2 className="text-xl font-semibold mb-4">📝 Text Models</h2>
            <p className="text-sm text-gray-500 mb-4">Models for text generation and coding.</p>
            {textModels.length === 0 ? (
              <div className="text-gray-500 text-sm">No text models detected yet.</div>
            ) : (
              <div className="space-y-3">{textModels.slice(0, 10).map((model) => (<ModelCard key={model.id} model={model} onOpenDetails={setSelectedModel} />))}</div>
            )}
          </div>

          <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
            <h2 className="text-xl font-semibold mb-4">👁️ Vision Models</h2>
            <p className="text-sm text-gray-500 mb-4">Models capable of visual analysis.</p>
            {visionModels.length === 0 ? (
              <div className="text-gray-500 text-sm">No vision models detected yet.</div>
            ) : (
              <div className="space-y-3">{visionModels.slice(0, 10).map((model) => (<ModelCard key={model.id} model={model} onOpenDetails={setSelectedModel} />))}</div>
            )}
          </div>

          <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
            <h2 className="text-xl font-semibold mb-4">📝 Text Model Test (Qwen 3.5)</h2>
            <p className="text-sm text-gray-500 mb-4">Send a simple text prompt to the configured text model.</p>
            <div className="flex items-center gap-3 mb-4">
              <button onClick={testTextModel} disabled={isRefreshing} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">{isRefreshing ? "Testing..." : "Test Text Model"}</button>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
            <h2 className="text-xl font-semibold mb-4">👁️ Vision Model Test (Qwen-VL)</h2>
            <p className="text-sm text-gray-500 mb-4">Send an image plus prompt to the vision model.</p>
            <div className="flex items-center gap-3 mb-4">
              <button onClick={testVisionModel} disabled={isRefreshing} className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed">{isRefreshing ? "Testing..." : "Test Vision Model"}</button>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
            <h2 className="text-xl font-semibold mb-4">↻ Actions</h2>
            <div className="flex gap-4 mb-4">
              <button onClick={handleRefresh} disabled={isRefreshing} className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed">Refresh Models</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
