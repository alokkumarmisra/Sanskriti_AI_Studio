import React, { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import axios from "axios";

// ============================================
// TYPE IMPORTS
// ============================================

type Scene = {
  id: string;
  project_id?: string;
  lyrics_id: string;
  scene_number: number;
  lyric_section?: string;
  title: string;
  description?: string;
  characters?: Array<{ name: string; description?: string }>;
  location_name?: string;
  visual_prompt?: string;
  negative_prompt?: string;
  duration_seconds: number;
  status: "draft" | "ready" | "generating" | "generated" | "failed" | "approved";
};

type Character = {
  id: string;
  character_name: string;
  appearance?: string;
  role?: string;
};

type Location = {
  id: string;
  location_name: string;
  description?: string;
  time_of_day?: string;
};

type LyricAnalysisResult = {
  analysis_id: string;
  lyrics_id: string;
  project_id?: string;
  verses: Array<{ section: string; text: string }>;
  chorus?: string;
  bridge?: string;
  characters: Array<{ name: string; description: string }>;
  locations: Array<{ name: string; description: string }>;
  events: Array<{ event: string; description: string }>;
  emotions: string[];
  themes: string[];
  visual_moments: Array<{ moment: string; description: string }>;
  recommended_scene_count?: number;
};

type GeneratedScenes = {
  scenes: Scene[];
  used_characters: Character[];
  used_locations: Location[];
};

const PLACEHOLDER_ID = "{{id}}";

// ============================================
// API CLIENTS
// ============================================

const BASE_URL = "/api/v1/projects";

const getLyricsAnalysis = async (lyricsId: string): Promise<LyricAnalysisResult> => {
  const res = await axios.get(`${BASE_URL}/lyrics/${lyricsId}/analysis`);
  if (!res.data.success) throw new Error(res.data.message || "Failed to fetch analysis");
  return res.data.data;
};

const submitLyricAnalysis = async (
  lyricsId: string, 
  project_id?: string,
  target_scene_count?: number
): Promise<LyricAnalysisResult> => {
  const url = project_id 
    ? `${BASE_URL}/${project_id}/lyrics/${lyricsId}/analysis`
    : `${BASE_URL}/lyrics/${lyricsId}/analysis`;

  const res = await axios.post(url, { target_scene_count });
  if (!res.data.success) throw new Error(res.data.message || "Failed to submit analysis");
  return res.data.data;
};

const getProjectScenes = async (projectId: string): Promise<Scene[]> => {
  const res = await axios.get(`${BASE_URL}/${projectId}/content/scenes`);
  if (!res.data.success) throw new Error(res.data.message || "Failed to fetch scenes");
  return res.data.data;
};

const createScene = async (projectId: string, payload: Partial<Scene>): Promise<Scene> => {
  const res = await axios.post(`${BASE_URL}/${projectId}/content/scenes`, payload);
  if (!res.data.success) throw new Error(res.data.message || "Failed to create scene");
  return res.data.data;
};

const updateScene = async (id: string, payload: Partial<Scene>): Promise<Scene> => {
  const res = await axios.put(`${BASE_URL}/content/scenes/${id}`, payload);
  if (!res.data.success) throw new Error(res.data.message || "Failed to update scene");
  return res.data.data;
};

const deleteScene = async (id: string): Promise<void> => {
  const res = await axios.delete(`${BASE_URL}/content/scenes/${id}`);
  if (!res.data.success) throw new Error(res.data.message || "Failed to delete scene");
};

const getProjectCharacters = async (projectId: string): Promise<Character[]> => {
  const res = await axios.get(`${BASE_URL}/${projectId}/content/characters`);
  if (!res.data.success) throw new Error(res.data.message || "Failed to fetch characters");
  return res.data.data;
};

const getProjectLocations = async (projectId: string): Promise<Location[]> => {
  const res = await axios.get(`${BASE_URL}/${projectId}/content/locations`);
  if (!res.data.success) throw new Error(res.data.message || "Failed to fetch locations");
  return res.data.data;
};

// ============================================
// MAIN COMPONENT
// ============================================

export default function ScenePlanningWorkspacePage({ projectId }: { projectId?: string }) {
  const [lyricsId, setLyricsId] = useState<string | undefined>(undefined);
  const [analysisResult, setAnalysisResult] = useState<LyricAnalysisResult | null>(null);
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);

  // Lyrics text state
  const [lyricsText, setLyricsText] = useState<string>("");
  
  // Target scene count
  const [targetSceneCount, setTargetSceneCount] = useState<number>(8);
  
  // Analysis status
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [generationStatus, setGenerationStatus] = useState<{ [key: string]: "idle" | "generating" | "complete" }>({});

  // Fetch scenes when project ID changes or lyricsId is set
  useEffect(() => {
    if (projectId) {
      const fetchScenes = async () => {
        try {
          if (lyricsId) {
            const fetchedScenes = await getProjectScenes(projectId);
            setScenes(fetchedScenes);
          } else {
            setScenes([]);
          }
        } catch (error) {
          console.error("Failed to fetch scenes:", error);
        }
      };
      fetchScenes();
    }
  }, [projectId, lyricsId]);

  // Fetch characters and locations when project ID changes
  useEffect(() => {
    if (projectId) {
      const fetchCharacters = async () => {
        try {
          const chars = await getProjectCharacters(projectId);
          setCharacters(chars);
        } catch (error) {
          console.error("Failed to fetch characters:", error);
        }
      };

      const fetchLocations = async () => {
        try {
          const locs = await getProjectLocations(projectId);
          setLocations(locs);
        } catch (error) {
          console.error("Failed to fetch locations:", error);
        }
      };

      fetchCharacters();
      fetchLocations();
    }
  }, [projectId]);

  // Handle analysis submission
  const handleAnalyze = async () => {
    if (!lyricsId) return;
    
    setIsAnalyzing(true);
    try {
      const result = await submitLyricAnalysis(lyricsId, projectId, targetSceneCount);
      setAnalysisResult(result);
    } catch (error) {
      console.error("Failed to analyze:", error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Handle scene generation
  const handleGenerateScenes = async () => {
    if (!lyricsId) return;
    
    setGenerationStatus(prev => ({ ...prev, [lyricsId]: "generating" }));
    
    try {
      const result = await submitLyricAnalysis(lyricsId, projectId, targetSceneCount);
      setAnalysisResult(result);
      
      // Create scenes from analysis
      const newScenes: Scene[] = Array.from({ length: result.recommended_scene_count || 4 }, (_, i) => ({
        id: `scene-${Date.now()}-${i}`,
        lyrics_id: lyricsId,
        scene_number: i + 1,
        title: `Scene ${i + 1}: ${result.visual_moments[i]?.moment || `Scene ${i + 1}`}`,
        description: result.visual_moments[i]?.description || "",
        visual_prompt: generateVisualPrompt(
          result.visual_moments[i]?.description,
          result.characters[i]?.description,
          result.locations[i]?.description
        ),
        duration_seconds: 8,
        status: "draft",
      }));

      // Add to local state (would need backend call to actually create)
      console.log("Generated scenes:", newScenes);
    } catch (error) {
      console.error("Failed to generate scenes:", error);
    } finally {
      setGenerationStatus(prev => ({ ...prev, [lyricsId]: "idle" }));
    }
  };

  // Generate visual prompt helper
  const generateVisualPrompt = (description?: string, charDesc?: string, locDesc?: string): string => {
    const parts: string[] = [];
    
    if (description) {
      parts.push(description);
    }
    
    if (charDesc) {
      parts.push(`A ${charDesc}`);
    }
    
    if (locDesc) {
      parts.push(`in a ${locDesc}`);
    }
    
    // Add consistent camera and lighting suggestions
    parts.push("cinematic shot, detailed composition");
    
    return parts.join(", ");
  };

  // Handle scene creation via API
  const handleCreateScene = async (newScene: Partial<Scene>) => {
    if (!projectId) return;
    try {
      await createScene(projectId, newScene);
      // Refetch scenes
      if (lyricsId) {
        const fetchedScenes = await getProjectScenes(projectId);
        setScenes(fetchedScenes);
      }
    } catch (error) {
      console.error("Failed to create scene:", error);
    }
  };

  // Handle scene update via API
  const handleUpdateScene = async (sceneId: string, updates: Partial<Scene>) => {
    if (!projectId) return;
    try {
      await updateScene(sceneId, updates);
      if (lyricsId) {
        const fetchedScenes = await getProjectScenes(projectId);
        setScenes(fetchedScenes);
      }
    } catch (error) {
      console.error("Failed to update scene:", error);
    }
  };

  // Handle scene deletion via API
  const handleDeleteScene = async (sceneId: string) => {
    if (!projectId) return;
    try {
      await deleteScene(sceneId);
      if (lyricsId) {
        const fetchedScenes = await getProjectScenes(projectId);
        setScenes(fetchedScenes);
      }
    } catch (error) {
      console.error("Failed to delete scene:", error);
    }
  };

  // Handle scene reordering via API
  const handleReorderScenes = async (orderList: Array<{ scene_id: string; position: number }>) => {
    if (!projectId) return;
    try {
      await axios.post(`${BASE_URL}/${projectId}/content/scenes/reorder`, orderList);
      if (lyricsId) {
        const fetchedScenes = await getProjectScenes(projectId);
        setScenes(fetchedScenes);
      }
    } catch (error) {
      console.error("Failed to reorder scenes:", error);
    }
  };

  // Handle character creation via API
  const handleCreateCharacter = async (payload: Partial<Character>) => {
    if (!projectId) return;
    try {
      await axios.post(`${BASE_URL}/${projectId}/content/characters`, payload);
    } catch (error) {
      console.error("Failed to create character:", error);
    }
  };

  // Handle location creation via API
  const handleCreateLocation = async (payload: Partial<Location>) => {
    if (!projectId) return;
    try {
      await axios.post(`${BASE_URL}/${projectId}/content/locations`, payload);
    } catch (error) {
      console.error("Failed to create location:", error);
    }
  };

  // Export scene plan
  const handleExport = () => {
    const exportData = {
      project_id: projectId,
      lyrics_id: lyricsId,
      analysis: analysisResult,
      scenes,
      characters,
      locations,
      exported_at: new Date().toISOString(),
    };
    
    // Download as JSON
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `scene-plan-${lyricsId?.substring(0, 8)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Check scene readiness
  const checkSceneReadiness = (scene: Scene): boolean => {
    return (
      !!scene.title &&
      !!scene.visual_prompt &&
      scene.duration_seconds > 0
    );
  };

  // Get status badge class
  const getStatusBadgeClass = (status: Scene["status"]) => {
    const classes: Record<string, string> = {
      draft: "bg-gray-200 text-gray-800",
      ready: "bg-green-100 text-green-800",
      generating: "bg-yellow-100 text-yellow-800",
      generated: "bg-blue-100 text-blue-800",
      failed: "bg-red-100 text-red-800",
      approved: "bg-purple-100 text-purple-800",
    };
    return classes[status] || classes.draft;
  };

  // Render lyrics editor section
  const renderLyricsEditor = () => (
    <div className="border rounded-lg p-6 mb-6 bg-white">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">Lyrics Input</h3>
      
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Song Title
        </label>
        <input
          type="text"
          placeholder="Enter song title"
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Artist/Creator Name
        </label>
        <input
          type="text"
          placeholder="Enter artist name"
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Language
        </label>
        <input
          type="text"
          defaultValue="English"
          placeholder="Enter language"
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Lyrics Content
        </label>
        <textarea
          value={lyricsText}
          onChange={(e) => setLyricsText(e.target.value)}
          placeholder="Paste or type your lyrics here..."
          className="w-full h-48 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
        />
      </div>

      <div className="flex gap-3">
        <button
          onClick={() => {
            setLyricsText("");
          }}
          className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
        >
          Clear
        </button>

        <button
          onClick={async () => {
            if (!lyricsId) return;
            const result = await submitLyricAnalysis(lyricsId, projectId, targetSceneCount);
            setAnalysisResult(result);
          }}
          disabled={!lyricsId || isAnalyzing}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {isAnalyzing ? "Analyzing..." : "Run AI Lyric Analysis"}
        </button>
      </div>

      {/* Analysis Results Display */}
      {analysisResult && (
        <div className="mt-6 border-t pt-4">
          <h4 className="text-md font-semibold mb-3 text-gray-800">AI Analysis Results</h4>
          
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <span className="text-sm text-gray-600">Emotions:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {analysisResult.emotions.map((emotion, i) => (
                  <span key={i} className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">{emotion}</span>
                ))}
              </div>
            </div>
            
            <div>
              <span className="text-sm text-gray-600">Themes:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {analysisResult.themes.map((theme, i) => (
                  <span key={i} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">{theme}</span>
                ))}
              </div>
            </div>

            {analysisResult.recommended_scene_count && (
              <div>
                <span className="text-sm text-gray-600">Recommended Scenes:</span>
                <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded ml-2">{analysisResult.recommended_scene_count}</span>
              </div>
            )}
          </div>

          <div className="bg-gray-50 p-4 rounded">
            <span className="text-sm font-medium text-gray-700">Visual Moments:</span>
            <ul className="mt-2 space-y-1">
              {analysisResult.visual_moments.map((moment, i) => (
                <li key={i} className="text-sm text-gray-600">
                  <span className="font-medium">{moment.moment}</span>: {moment.description}
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-4 flex gap-3">
            <button
              onClick={handleGenerateScenes}
              disabled={!lyricsId || generationStatus[lyricsId] === "generating"}
              className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
            >
              Generate Scenes
            </button>

            <button
              onClick={handleExport}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            >
              Export Scene Plan
            </button>
          </div>
        </div>
      )}
    </div>
  );

  // Render scene list section
  const renderSceneList = () => (
    <div className="border rounded-lg p-6 mb-6 bg-white">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Scenes</h3>
        <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
          {scenes.length} scenes
        </span>
      </div>

      {scenes.length === 0 ? (
        <p className="text-gray-500 text-center py-4">No scenes yet. Generate scenes from lyrics analysis.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-3 py-2 text-left">#</th>
                <th className="px-3 py-2 text-left">Title</th>
                <th className="px-3 py-2 text-left">Lyric Section</th>
                <th className="px-3 py-2 text-left">Duration</th>
                <th className="px-3 py-2 text-left">Status</th>
                <th className="px-3 py-2 text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {scenes.map((scene) => (
                <tr key={scene.id} className="border-b hover:bg-gray-50">
                  <td className="px-3 py-2">{scene.scene_number}</td>
                  <td className="px-3 py-2 max-w-xs truncate" title={scene.title}>
                    {scene.title}
                  </td>
                  <td className="px-3 py-2">
                    <span className="px-2 py-1 bg-gray-100 rounded text-xs">{scene.lyric_section || "—"}</span>
                  </td>
                  <td className="px-3 py-2">{scene.duration_seconds}s</td>
                  <td className="px-3 py-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadgeClass(scene.status)}`}>
                      {scene.status}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-center">
                    <div className="flex justify-center gap-2">
                      <button className="text-blue-600 hover:underline" onClick={() => {}}>Edit</button>
                      <button className="text-red-600 hover:underline" onClick={() => handleDeleteScene(scene.id)}>Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  // Render character panel
  const renderCharacterPanel = () => (
    <div className="border rounded-lg p-6 mb-6 bg-white">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">Characters</h3>
      
      {characters.length === 0 ? (
        <p className="text-gray-500">No characters defined yet. Create reusable character definitions for continuity.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {characters.map((char) => (
            <div key={char.id} className="border rounded p-3 bg-gray-50">
              <h4 className="font-medium text-gray-800">{char.character_name}</h4>
              <p className="text-sm text-gray-600 mt-1">
                {char.role || char.appearance || "—"}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  // Render location panel
  const renderLocationPanel = () => (
    <div className="border rounded-lg p-6 mb-6 bg-white">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">Locations</h3>
      
      {locations.length === 0 ? (
        <p className="text-gray-500">No locations defined yet. Create reusable location definitions for continuity.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {locations.map((loc) => (
            <div key={loc.id} className="border rounded p-3 bg-gray-50">
              <h4 className="font-medium text-gray-800">{loc.location_name}</h4>
              <p className="text-sm text-gray-600 mt-1">
                {loc.time_of_day || loc.description || "—"}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  // Render scene editor
  const renderSceneEditor = (scene: Scene) => (
    <div className="border rounded-lg p-6 bg-gray-50 mb-6">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">Edit Scene {scene.scene_number}</h3>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Scene Title</label>
          <input
            type="text"
            value={scene.title}
            onChange={(e) => handleUpdateScene(scene.id, { title: e.target.value })}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Duration (seconds)</label>
          <input
            type="number"
            value={scene.duration_seconds}
            onChange={(e) => handleUpdateScene(scene.id, { duration_seconds: parseInt(e.target.value) })}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="mt-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
        <textarea
          value={scene.description || ""}
          onChange={(e) => handleUpdateScene(scene.id, { description: e.target.value })}
          placeholder="Enter scene description..."
          className="w-full h-24 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
        />
      </div>

      <div className="mt-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">Visual Prompt</label>
        <textarea
          value={scene.visual_prompt || ""}
          onChange={(e) => handleUpdateScene(scene.id, { visual_prompt: e.target.value })}
          placeholder="Enter AI image generation prompt..."
          className="w-full h-32 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-mono"
        />
      </div>

      <div className="mt-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">Negative Prompt</label>
        <textarea
          value={scene.negative_prompt || ""}
          onChange={(e) => handleUpdateScene(scene.id, { negative_prompt: e.target.value })}
          placeholder="Enter negative prompt for image generation..."
          className="w-full h-24 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-mono"
        />
      </div>

      <div className="mt-4 flex gap-3">
        <button
          onClick={async () => {
            await handleUpdateScene(scene.id, { status: "ready" });
          }}
          disabled={scene.status === "ready"}
          className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 text-sm"
        >
          Mark as Ready
        </button>

        <button
          onClick={async () => {
            await handleUpdateScene(scene.id, { status: "draft" });
          }}
          disabled={scene.status === "draft"}
          className="px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50 text-sm"
        >
          Mark as Draft
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen p-6 bg-gray-100">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold mb-6 text-gray-800">Content & Scene Planning Workspace</h1>

        {/* Top actions bar */}
        <div className="flex gap-3 mb-6">
          {projectId && (
            <button className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700">
              New Scene
            </button>
          )}

          {projectId && (
            <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
              Duplicate Scene
            </button>
          )}

          <button className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">
            Delete Selected
            <span className="ml-2">(delete scene)</span>
          </button>
        </div>

        {/* Lyrics Editor Section */}
        {renderLyricsEditor()}

        {/* Scene List Section */}
        {scenes.length > 0 && renderSceneList()}

        {/* Character Continuity Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {renderCharacterPanel()}
          {renderLocationPanel()}
        </div>

        {/* Scene Editor (for editing) */}
        {scenes.length > 0 && renderSceneEditor(scenes[0])}

        {/* Footer notes about future pipeline */}
        <div className="mt-8 p-4 bg-yellow-50 border rounded-lg text-sm text-gray-700">
          <p><strong>Future Pipeline Preparation:</strong> This scene plan output is structured for future image/video generation steps.</p>
          <p className="mt-2">
            Flow: Lyrics → Scene Planning → Scene Validation → Image Generation → Image Validation → Video Generation → Video Validation → Editing
          </p>
        </div>

        {/* API endpoint documentation */}
        <div className="mt-6 p-4 bg-gray-800 text-gray-300 rounded-lg text-sm font-mono">
          <h4 className="font-semibold mb-2 text-white">Available Endpoints:</h4>
          {projectId && (
            <code>GET /api/v1/projects/{projectId}/content/scenes</code>
          )}
          <br />
          {projectId && (
            <code>POST /api/v1/projects/{projectId}/content/scenes</code>
          )}
          <br />
          <code>PUT /api/v1/content/scenes/{PLACEHOLDER_ID}</code>
          <br />
          <code>DELETE /api/v1/content/scenes/{PLACEHOLDER_ID}</code>
        </div>
      </div>
    </div>
  );
}
