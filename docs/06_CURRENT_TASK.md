# Sanskriti AI Studio — Current Task

**Version:** 1.3  
**Status:** Active  
**Last Updated:** 2026-08-13  

## STEP 24.7 — Content & Scene Planning Workspace

### Implementation Status: IN PROGRESS

The Content & Scene Planning Workspace has been implemented to provide a complete workflow for AI-powered content creation from song lyrics. This workspace allows users to input lyrics, analyze them with AI, generate scenes, manage visual prompts, and export the scene plan for future image/video generation.

---

## Implementation Summary

### Completed Components

#### Phase 1 — Requirements Discovery
- ✓ Explored existing architecture (Project Workspace, LM Studio Manager, API patterns)
- ✓ Identified reusable components (Project model, Lyrics model, database structure)
- ✓ Confirmed Qwen 3.5 TEXT-ONLY constraint for AI analysis

#### Phase 19a — Backend Models
- ✓ Created `backend/app/models/scenes.py` with:
  - **Scene** model: Main scene entity with all visual prompt fields
  - **Character** model: Reusable character definitions for continuity
  - **Location** model: Reusable location definitions for continuity  
  - **ScenePrompt** model: Prompt history for AI regeneration/versioning
  - **Response models**: SceneRead, CharacterRead, LocationRead, SceneCreate

- ✓ Updated `backend/app/models/project.py` to include scene relationship
- ✓ Updated `backend/app/models/__init__.py` to export new models

#### Phase 19b — Backend Services  
- ✓ Created `backend/app/services/scenes_service.py` with:
  - CRUD operations for Scenes, Characters, Locations
  - Scene reordering functionality
  - Prompt history management for AI regeneration

#### Phase 19c — API Routes
- ✓ Created `backend/app/api/projects/scenes.py` with endpoints:
  - **Scenes**: GET/POST/PUT/DELETE `/content/scenes/*`
  - **Reorder**: POST `/content/scenes/reorder`
  - **Characters**: GET/POST/PUT/DELETE `/content/characters/*`
  - **Locations**: GET/POST/PUT/DELETE `/content/locations/*`
  - **Prompt History**: GET/POST `/content/scenes/*/prompts/*`

#### Phase 19d — Database Migration
- ✓ Created `backend/alembic/versions/2026_08_13_add_scene_planning_models.py` with:
  - CREATE TABLE scenes
  - CREATE TABLE characters  
  - CREATE TABLE locations
  - CREATE TABLE scene_prompts
  - Foreign keys and indexes

#### Phase 19e — Routes Registration
- ✓ Updated `backend/app/api/projects/__init__.py` to register new routes

#### Phase 20a — Frontend Types
- ✓ Created `frontend/src/types/scenes.ts` with:
  - Scene, Character, Location interfaces
  - LyricAnalysisResult, GeneratedScenes interfaces
  - SceneStatus type union
  - All payload types for API clients

#### Phase 20b — Frontend API Clients
- ✓ Created `frontend/src/api/scenes.ts` with:
  - useLyricAnalysisQuery / useSubmitLyricAnalysisMutation
  - useProjectScenesQuery / useCreateSceneMutation / etc.
  - useReorderScenesMutation
  - useProjectCharactersQuery / useProjectLocationsQuery
  - useCreatePromptHistoryMutation / useScenePromptHistoryQuery

#### Phase 20c — Content Planning Workspace Component
- ✓ Created `frontend/src/components/scenes/ScenePlanningWorkspacePage.tsx` with:
  - Lyrics Input section (title, artist, language, content)
  - AI Lyric Analysis button and results display
  - Scene List table with status badges
  - Character continuity panel
  - Location continuity panel
  - Scene Editor with all fields editable
  - Export functionality (JSON download)
  - Future pipeline preparation notes

---

## Files Created/Modified

### Backend Files

**Created:**
- `backend/app/models/scenes.py` (529 lines)
- `backend/app/services/scenes_service.py` (371 lines)  
- `backend/app/api/projects/scenes.py` (246 lines)
- `backend/alembic/versions/2026_08_13_add_scene_planning_models.py` (185 lines)

**Modified:**
- `backend/app/models/__init__.py`
- `backend/app/models/project.py`
- `backend/app/api/projects/__init__.py`

### Frontend Files

**Created:**
- `frontend/src/types/scenes.ts` (246 lines)
- `frontend/src/api/scenes.ts` (398 lines)
- `frontend/src/components/scenes/ScenePlanningWorkspacePage.tsx` (900+ lines)

---

## API Endpoints Summary

### Content & Scene Planning Routes:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/projects/{id}/content/scenes` | List scenes |
| POST | `/api/v1/projects/{id}/content/scenes` | Create scene |
| PUT | `/api/v1/content/scenes/{id}` | Update scene |
| DELETE | `/api/v1/content/scenes/{id}` | Delete scene |
| POST | `/api/v1/projects/{id}/content/scenes/reorder` | Reorder scenes |
| GET | `/api/v1/projects/{id}/content/characters` | List characters |
| POST | `/api/v1/projects/{id}/content/characters` | Create character |
| PUT | `/api/v1/content/characters/{id}` | Update character |
| DELETE | `/api/v1/content/characters/{id}` | Delete character |
| GET | `/api/v1/projects/{id}/content/locations` | List locations |
| POST | `/api/v1/projects/{id}/content/locations` | Create location |
| PUT | `/api/v1/content/locations/{id}` | Update location |
| DELETE | `/api/v1/content/locations/{id}` | Delete location |
| POST | `/api/v1/content/scenes/{sceneId}/prompts` | Create prompt history |
| GET | `/api/v1/content/scenes/{sceneId}/prompts/history` | Get prompt history |

### Analysis Routes (LM Studio Integration):

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/projects/{id}/lyrics/{lyricsId}/analysis` | Submit for AI analysis |
| POST | `/api/v1/content/scenes/generate` | Generate scenes from analysis |

---

## Scene Model Fields

Each Scene contains:

**Core Fields:**
- `id`: UUID string
- `project_id`: Reference to project
- `lyrics_id`: Reference to lyrics
- `scene_number`: Ordering integer

**Lyric Association:**
- `lyric_section`: Verse/Chorus/Bridge identifier
- `lyric_text`: Actual lyric text segment

**Content Fields:**
- `title`: Scene title (required)
- `description`: Scene description

**Character Information:**
- `characters`: JSON array of character objects with name/description

**Location Information:**
- `location_name`: Location name
- `location_description`: Location details

**Scene Attributes:**
- `time_period`: Time period/era
- `emotion`: Emotion (e.g., "joy", "melancholy")
- `action`: Action description

**Visual Prompt Fields:**
- `visual_theme`: Visual theme/style
- `visual_prompt`: Main prompt for image generation
- `negative_prompt`: Negative prompt fields

**Camera/Lighting:**
- `camera_angle`: Camera angle specification
- `lighting`: Lighting conditions
- `composition`: Composition notes

**Duration:**
- `duration_seconds`: Scene duration (default 8s)

**Continuity:**
- `continuity_notes`: Additional continuity information

**Status:**
- `status`: "draft" | "ready" | "generating" | "generated" | "failed" | "approved"

---

## Future Pipeline Preparation

The output of this workspace is structured to support the future workflow:

```
Lyrics Input → AI Analysis → Scene Generation → Scene Editing → 
Scene Validation → Image Generation → Image Validation → 
Video Generation → Video Validation → Editing/Finalization
```

This workspace implements phases 1-3 (Lyrics, Scene Planning, Validation) and prepares the output structure for future image/video generation steps.

---

## Known Issues & TODOs

### Backend:
- [ ] LM Studio integration for actual lyric analysis needs completion
- [ ] Need to add analysis routes to main API router registration

### Frontend:
- [ ] Need to fix TypeScript errors in ScenePlanningWorkspacePage.tsx (lyricsId undefined handling)
- [ ] ESLint warning about `any` type in handleCreateScene
- [ ] Integration with Project Workspace Dashboard navigation not yet implemented

### Database:
- [ ] Migration needs to be applied after implementation

---

## Testing Requirements

Phase 21 - Testing Checklist:
- [x] Backend models can be imported without errors
- [ ] Database migration applies successfully
- [ ] API endpoints respond correctly
- [ ] Frontend components render without errors  
- [ ] Lyrics analysis endpoint works (via LM Studio)
- [ ] Scene creation/deletion works
- [ ] Character/location CRUD works
- [ ] Scene reordering works
- [ ] Prompt history creation works
- [ ] Export functionality produces valid JSON

Phase 22 - Browser Validation:
- [x] Component can be mounted
- [ ] Navigation integration to complete

Phase 23 - Vision Validation:
- [ ] Screenshot capture of workspace UI
- [ ] UI analysis via Vision Agent

Phase 24 - UI Validation:
- [ ] Layout and styling matches project theme
- [ ] Responsive design works on tablet/mobile
- [ ] All interactive elements accessible

---

## Next Steps

1. Fix remaining TypeScript errors in ScenePlanningWorkspacePage.tsx
2. Complete LM Studio integration for actual lyric analysis
3. Register routes in main application router
4. Apply database migration
5. Integration with Project Workspace Dashboard navigation
6. Run full testing cycle (Phases 21-24)
7. Update documentation files (Phase 26)
8. Prepare for Phase 27 - Regression Testing

---

**Status:** Implementation Complete — Awaiting Documentation Update and Final Validation  
**Ready for Approval:** False (pending final validation steps)
