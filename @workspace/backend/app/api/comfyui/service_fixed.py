"""ComfyUI Manager Service for Sanskriti AI Studio."""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import requests


class ComfyUIManager:
    """
    Manager for ComfyUI local server communication and workflow management.
    
    This service communicates with the local ComfyUI server (default: 127.0.0.1:8188)
    to manage workflows, queue monitoring, job execution, and output retrieval.
    
    Architecture:
        Sanskriti_AI_Studio
            ↓
        Existing ComfyUI Service
            ↓
        ComfyUI API
            ↓
        Workflow
            ↓
        Queue
            ↓
        Generation
            ↓
        Output
    """

    def __init__(self):
        """Initialize ComfyUI manager with configuration from environment."""
        self._base_url = self._get_env("COMFYUI_BASE_URL", "http://127.0.0.1:8188")
        self._text_model = self._get_env("CODING_MODEL", "")
        self._vision_model = self._get_env("VISION_MODEL", "")
        
        # Connection state
        self._connected: bool = False
        self._last_error: Optional[str] = None
        self._response_time_ms: float = 0.0
        self._last_health_check: Optional[datetime] = None
    
    def _get_env(self, variable: str, default: Any = None) -> Any:
        """Get environment variable value or return default."""
        env_var = f"COMFYUI_{variable.upper()}"
        value = os.environ.get(env_var, default)
        if variable.upper() in ["CODING_MODEL", "VISION_MODEL"]:
            return value if value else default
        return value if value is not None else default

    def set_base_url(self, url: str) -> None:
        """Set custom base URL for ComfyUI."""
        self._base_url = url.rstrip("/")

    def set_text_model(self, model_name: str) -> None:
        """Set text-only model name (e.g., Qwen 3.5)."""
        os.environ['COMFYUI_CODING_MODEL'] = model_name
        self._text_model = model_name

    def set_vision_model(self, model_name: str) -> None:
        """Set vision model name (e.g., Qwen-VL-8B)."""
        os.environ['COMFYUI_VISION_MODEL'] = model_name
        self._vision_model = model_name

    @property
    def base_url(self) -> str:
        """Get the ComfyUI base URL."""
        return self._base_url.rstrip("/") + "/api"

    @property
    def server_url(self) -> str:
        """Get the full server URL without /api suffix."""
        return self._base_url.rstrip("/")

    @property
    def text_model(self) -> Optional[str]:
        """Get configured text-only model name."""
        return self._text_model if self._text_model else None

    @property
    def vision_model(self) -> Optional[str]:
        """Get configured vision model name."""
        return self._vision_model if self._vision_model else None

    def is_connected(self) -> bool:
        """Check if ComfyUI server is reachable and responsive."""
        try:
            response = requests.get(
                f"{self._base_url}/system_stats",
                timeout=10,
                allow_redirects=True
            )

            if response.status_code in [200, 404]:
                self._connected = True
                self._last_error = None
                return True
            else:
                self._connected = False
                self._last_error = f"HTTP {response.status_code} from /system_stats"

        except requests.exceptions.ConnectionError:
            self._connected = False
            self._last_error = "Connection refused"
        except requests.exceptions.Timeout:
            self._connected = False
            self._last_error = "Connection timeout"
        except Exception as e:
            self._connected = False
            self._last_error = str(e)

        return False

    def get_response_time(self) -> Optional[float]:
        """Get the last response time in seconds."""
        return 0.0  # Placeholder - actual implementation would track timing

    def set_last_health_check(self, now: Optional[datetime] = None) -> None:
        """Update last health check timestamp."""
        if now is None:
            now = datetime.now(timezone.utc)
        self._last_health_check = now

    def get_response_time_ms(self) -> float:
        """Get response time in milliseconds."""
        return 0.0  # Placeholder - actual implementation would track timing

    # ===========================================
    # System Information (Phase 3)
    # ===========================================

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system information from ComfyUI."""
        try:
            response = requests.get(
                f"{self._base_url}/system_stats",
                timeout=10,
                allow_redirects=False
            )

            if response.status_code == 200:
                stats = response.json()
                
                gpu_info = stats.get("gpu_info") or {}
                memory = stats.get("memory") or {}
                version = stats.get("version") or ""
                
                return {
                    "success": True,
                    "version": version,
                    "gpu_info": {
                        "name": gpu_info.get("name", "Unknown"),
                        "compute_capability": gpu_info.get("compute_capability"),
                        "vram_total_mb": gpu_info.get("vram_total_mb"),
                        "vram_used_mb": gpu_info.get("vram_used_mb"),
                        "vram_available_mb": gpu_info.get("vram_available_mb"),
                        "utilization": gpu_info.get("utilization_percent") or 0,
                    },
                    "memory_info": {
                        "total_mb": memory.get("total_mb"),
                        "used_mb": memory.get("used_mb"),
                        "available_mb": memory.get("available_mb"),
                    },
                }

            return {"success": True, "version": "", "gpu_info": {}, "memory_info": {}}

        except Exception as e:
            return {
                "success": False,
                "version": "",
                "error_message": f"Failed to get system stats: {str(e)}",
            }

    # ===========================================
    # Queue Monitoring (Phase 4)
    # ===========================================

    def _count_active_jobs(self, queue_data: Dict) -> int:
        """Count active jobs in queue."""
        count = 0
        for item in queue_data.get("queue", []):
            prompt = item.get("prompt", {}) or {}
            if prompt.get("executing") or prompt.get("pending"):
                count += 1
        return count

    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status information."""
        try:
            response = requests.get(
                f"{self._base_url}/promptQueue",
                timeout=10,
                allow_redirects=False
            )

            if response.status_code == 200:
                data = response.json()
                
                running_jobs: List[Dict[str, Any]] = []
                pending_jobs: List[Dict[str, Any]] = []
                history_items: List[Dict[str, Any]] = []
                
                # Parse queue items
                for item in data.get("queue", []):
                    prompt = item.get("prompt") or {}
                    
                    if prompt.get("executing"):
                        job_info = {
                            "id": str(item.get("prompt") or ""),
                            "title": item.get("prompt_data", {}).get("client_id") or "Unknown",
                            "status": "RUNNING",
                            "queue_position": len(data.get("queue", [])) - self._count_active_jobs(data),
                            "progress": item.get("prompt_data", {}).get("outputs"),
                        }
                        running_jobs.append(job_info)
                    elif prompt.get("submitted"):
                        job_info = {
                            "id": str(item.get("prompt") or ""),
                            "title": item.get("prompt_data", {}).get("client_id") or "Unknown",
                            "status": "PENDING",
                            "queue_position": 0,
                            "progress": None,
                        }
                        pending_jobs.append(job_info)
                    else:
                        job_info = {
                            "id": str(item.get("prompt") or ""),
                            "title": item.get("prompt_data", {}).get("client_id") or "Unknown",
                            "status": prompt.get("failed") and "FAILED" or 
                                      prompt.get("completed") and "COMPLETED" or
                                      "UNKNOWN",
                            "queue_position": 0,
                            "progress": None,
                        }
                        history_items.append(job_info)

                # Parse history for completed/failed jobs
                completed_jobs: List[Dict[str, Any]] = []
                failed_jobs: List[Dict[str, Any]] = []
                
                for h in data.get("history", []):
                    status = h.get("status") or "unknown"
                    
                    job_info = {
                        "id": str(h.get("prompt") or ""),
                        "title": h.get("client_id") or "Unknown",
                        "status": status,
                        "start_time": h.get("start_time"),
                        "duration": h.get("duration"),
                        "outputs": h.get("outputs"),
                    }
                    
                    if status == "SUCCESS":
                        completed_jobs.append(job_info)
                    elif status in ["FAILED", "ERROR", "INTERRUPTED"]:
                        failed_jobs.append(job_info)

                return {
                    "success": True,
                    "queue": data.get("queue"),
                    "running": running_jobs,
                    "pending": pending_jobs,
                    "completed": completed_jobs[-10:] if len(completed_jobs) > 0 else [],  # Last 10 completed
                    "failed": failed_jobs[-10:] if len(failed_jobs) > 0 else [],          # Last 10 failed
                    "total_running": len(running_jobs),
                    "total_pending": len(pending_jobs),
                    "total_completed": len([h for h in data.get("history", []) if h.get("status") == "SUCCESS"]),
                    "total_failed": len([h for h in data.get("history", []) if h.get("status") in ["FAILED", "ERROR", "INTERRUPTED"]]),
                }

            return {
                "success": True,
                "queue": [],
                "running": [],
                "pending": [],
                "completed": [],
                "failed": [],
                "total_running": 0,
                "total_pending": 0,
                "total_completed": 0,
                "total_failed": 0,
            }

        except Exception as e:
            return {
                "success": False,
                "queue": [],
                "running": [],
                "pending": [],
                "completed": [],
                "failed": [],
                "total_running": 0,
                "total_pending": 0,
                "total_completed": 0,
                "total_failed": 0,
                "error_message": f"Failed to get queue status: {str(e)}",
            }

    def get_queue_position(self, job_id: str) -> Dict[str, Any]:
        """Get position of a specific job in the queue."""
        try:
            response = requests.get(
                f"{self._base_url}/promptQueue",
                timeout=10,
                allow_redirects=False
            )

            if response.status_code == 200:
                data = response.json()
                
                active_count = self._count_active_jobs(data)
                
                for item in data.get("queue", []):
                    if str(item.get("prompt")) == job_id:
                        return {
                            "success": True,
                            "job_id": job_id,
                            "position": len(data.get("queue", [])) - active_count,
                            "status": item.get("prompt") and item.get("prompt", {}).get("executing") and "RUNNING" or
                                       item.get("prompt") and item.get("prompt", {}).get("pending") and "PENDING" or
                                       item.get("prompt") and item.get("prompt", {}).get("failed") and "FAILED" or
                                       item.get("prompt") and item.get("prompt", {}).get("submitted") and "SUBMITTED" or
                                       "UNKNOWN",
                        }

                return {
                    "success": True,
                    "job_id": job_id,
                    "position": None,
                    "status": "NOT_FOUND",
                    "error_message": f"Job {job_id} not found in queue",
                }

            return {
                "success": False,
                "job_id": job_id,
                "position": None,
                "status": "ERROR",
                "error_message": f"Failed to get queue position: HTTP {response.status_code}",
            }

        except Exception as e:
            return {
                "success": False,
                "job_id": job_id,
                "position": None,
                "status": "ERROR",
                "error_message": f"Failed to get queue position: {str(e)}",
            }

    # ===========================================
    # Workflow Management (Phase 6)
    # ===========================================

    def get_workflow_history(self, limit: int = 20) -> Dict[str, Any]:
        """Get history of executed workflows."""
        try:
            response = requests.get(
                f"{self._base_url}/history",
                timeout=10
            )

            if response.status_code == 200:
                history_data = response.json()
                
                workflows = []
                for item in history_data.get("items", [])[:limit]:
                    workflow_info = {
                        "id": str(item.get("prompt") or ""),
                        "filename": item.get("filename") or "unknown",
                        "status": item.get("status") or "",
                        "start_time": item.get("start_time"),
                        "end_time": item.get("end_time"),
                        "duration": item.get("duration"),
                        "outputs": item.get("outputs_count") or 0,
                        "errors": item.get("errors"),
                    }
                    workflows.append(workflow_info)

                return {
                    "success": True,
                    "workflows": workflows,
                    "count": len(workflows),
                }

            return {
                "success": True,
                "workflows": [],
                "count": 0,
            }

        except Exception as e:
            return {
                "success": False,
                "workflows": [],
                "count": 0,
                "error_message": f"Failed to get workflow history: {str(e)}",
            }

    def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """Get details of a specific job."""
        try:
            response = requests.get(
                f"{self._base_url}/history/{job_id}",
                timeout=10
            )

            if response.status_code == 200:
                history_data = response.json()
                
                return {
                    "success": True,
                    "job_id": str(history_data.get("prompt") or ""),
                    "workflow": history_data.get("filename") or "",
                    "status": history_data.get("status") or "",
                    "start_time": history_data.get("start_time"),
                    "end_time": history_data.get("end_time"),
                    "duration": history_data.get("duration"),
                    "outputs": history_data.get("outputs", []),
                    "errors": history_data.get("errors"),
                }

            return {
                "success": False,
                "job_id": job_id,
                "workflow": "",
                "status": "ERROR",
                "error_message": f"Failed to get job details: HTTP {response.status_code}",
            }

        except Exception as e:
            return {
                "success": False,
                "job_id": job_id,
                "workflow": "",
                "status": "ERROR",
                "error_message": f"Failed to get job details: {str(e)}",
            }

    def get_job_output_files(self, job_id: str) -> Dict[str, Any]:
        """Get list of output files for a completed job."""
        try:
            response = requests.get(
                f"{self._base_url}/history/{job_id}",
                timeout=10
            )

            if response.status_code == 200:
                history_data = response.json()
                
                outputs = []
                for output in history_data.get("outputs", []):
                    filename = output.get("filename") or "unknown"
                    
                    try:
                        file_response = requests.get(
                            f"{self._base_url}/view?filename={filename.replace(' ', '%20')}",
                            timeout=5
                        )
                        
                        if file_response.status_code == 200:
                            content_type = file_response.headers.get("content-type", "")
                            size_bytes = int(file_response.headers.get("content-length", 0)) or len(file_response.content)
                            
                            outputs.append({
                                "filename": filename,
                                "type": self._detect_file_type(filename),
                                "size_bytes": size_bytes,
                                "content_type": content_type,
                            })
                        else:
                            outputs.append({
                                "filename": filename,
                                "type": "unknown",
                                "size_bytes": 0,
                            })
                    except:
                        outputs.append({
                            "filename": filename,
                            "type": "unknown",
                            "size_bytes": 0,
                        })

                return {
                    "success": True,
                    "job_id": job_id,
                    "outputs": outputs,
                    "count": len(outputs),
                }

            return {
                "success": False,
                "job_id": job_id,
                "outputs": [],
                "count": 0,
                "error_message": f"Failed to get output files: HTTP {response.status_code}",
            }

        except Exception as e:
            return {
                "success": False,
                "job_id": job_id,
                "outputs": [],
                "count": 0,
                "error_message": f"Failed to get output files: {str(e)}",
            }

    def _detect_file_type(self, filename: str) -> str:
        """Detect file type from extension."""
        ext = os.path.splitext(filename)[1].lower()
        
        image_extensions = [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"]
        video_extensions = [".mp4", ".avi", ".mov", ".mkv", ".webm"]

        if any(ext in filename.lower() for ext in image_extensions):
            return "IMAGE"
        elif any(ext in filename.lower() for ext in video_extensions):
            return "VIDEO"
        else:
            return "OTHER"

    # ===========================================
    # Workflow Execution (Phase 7)
    # ===========================================

    def submit_workflow(self, workflow: str, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Submit a workflow to ComfyUI for execution."""
        try:
            response = requests.post(
                f"{self._base_url}/history",
                json={
                    "workflow": workflow,
                    "inputs": inputs or {},
                },
                timeout=30
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "status": "submitted",
                    "job_id": str(response.json().get("prompt") or ""),
                    "message": "Workflow submitted to queue",
                }

            if response.status_code == 302:
                return {
                    "success": True,
                    "status": "submitted",
                    "job_id": str(response.json().get("prompt") or ""),
                    "message": "Workflow submitted to queue",
                }

            return {
                "success": False,
                "status": "failed",
                "job_id": None,
                "error_message": f"Failed to submit workflow: HTTP {response.status_code}",
            }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "status": "timeout",
                "job_id": None,
                "error_message": "Submission timeout. Server may be overloaded.",
            }

        except requests.exceptions.ConnectionError as e:
            return {
                "success": False,
                "status": "disconnected",
                "job_id": None,
                "error_message": f"Connection error: {str(e)}",
            }

        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "job_id": None,
                "error_message": f"Failed to submit workflow: {str(e)}",
            }

    def submit_workflow_from_file(self, filepath: str) -> Dict[str, Any]:
        """Submit a workflow from file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                workflow = f.read().strip()

            try:
                workflow_data = json.loads(workflow) if len(workflow) < 10 * 1024 * 1024 else {}
            except json.JSONDecodeError:
                workflow_data = {}

            return self.submit_workflow(workflow, workflow_data)

        except FileNotFoundError:
            return {
                "success": False,
                "status": "error",
                "job_id": None,
                "error_message": f"Workflow file not found: {filepath}",
            }

        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "job_id": None,
                "error_message": f"Failed to submit workflow from file: {str(e)}",
            }

    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """Cancel a running job."""
        try:
            response = requests.post(
                f"{self._base_url}/interrupt/{job_id}",
                timeout=10
            )

            if response.status_code in [200, 204]:
                return {
                    "success": True,
                    "status": "cancelled",
                    "job_id": job_id,
                    "message": f"Job {job_id} cancelled successfully",
                }

            return {
                "success": False,
                "status": "failed",
                "job_id": job_id,
                "error_message": f"Failed to cancel job: HTTP {response.status_code}",
            }

        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "job_id": job_id,
                "error_message": f"Failed to cancel job: {str(e)}",
            }

    # ===========================================
    # Output Management (Phase 8)
    # ===========================================

    def get_output_preview(self, filename: str, output_index: int = 0) -> Optional[Dict[str, Any]]:
        """Get preview of an output file."""
        try:
            view_url = f"{self._base_url}/view?filename={filename.replace(' ', '%20')}"
            
            response = requests.head(view_url, timeout=5)

            if response.status_code == 200:
                content_length = response.headers.get("content-length", "0")
                
                return {
                    "success": True,
                    "filename": filename,
                    "view_url": view_url,
                    "content_length": int(content_length) if content_length else 0,
                    "preview_available": True,
                }

            return None

        except Exception:
            return None

    def download_output(self, filename: str, save_path: Optional[str] = None) -> Dict[str, Any]:
        """Download an output file."""
        try:
            view_url = f"{self._base_url}/view?filename={filename.replace(' ', '%20')}"
            
            response = requests.get(view_url, timeout=120, stream=True)

            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                
                ext = os.path.splitext(filename)[1].lower()
                is_image = ext in [".png", ".jpg", ".jpeg", ".webp"]
                
                file_info = {
                    "filename": filename,
                    "content_type": content_type,
                    "size_bytes": len(response.content),
                    "is_image": is_image,
                    "is_video": ext in [".mp4", ".mov", ".avi"],
                }

                if save_path:
                    with open(save_path, "wb") as f:
                        f.write(response.content)
                
                return {
                    "success": True,
                    "file_info": file_info,
                    "message": f"Downloaded {filename} ({file_info['size_bytes']} bytes)",
                }

            return {
                "success": False,
                "file_info": {"filename": filename, "size_bytes": 0},
                "error_message": f"Failed to download file: HTTP {response.status_code}",
            }

        except Exception as e:
            return {
                "success": False,
                "file_info": {"filename": filename, "size_bytes": 0},
                "error_message": f"Failed to download output: {str(e)}",
            }

    # ===========================================
    # Health Monitoring (Phase 10)
    # ===========================================

    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        return {
            "server_reachable": self.is_connected(),
            "api_available": self._check_api_endpoint("/system_stats"),
            "queue_accessible": self._check_api_endpoint("/promptQueue"),
            "workflow_accessible": self.get_workflow_history(limit=0)["success"],
            "generation_available": True,
        }

    def _check_api_endpoint(self, endpoint: str) -> bool:
        """Check if an API endpoint is accessible."""
        try:
            response = requests.get(
                f"{self._base_url}{endpoint}",
                timeout=5,
                allow_redirects=False
            )
            return response.status_code in [200, 404]
        except Exception:
            return False

    def get_vram_info(self) -> Dict[str, Any]:
        """Get detailed VRAM information from ComfyUI."""
        stats = self.get_system_stats()
        
        if not stats.get("success"):
            return {
                "gpu_name": "Unknown",
                "vram_total_gb": 0,
                "vram_used_gb": 0,
                "vram_available_gb": 0,
                "utilization_percent": 0,
            }

        gpu_info = stats.get("gpu_info") or {}
        
        vram_mb = gpu_info.get("vram_total_mb") or 12000
        used_mb = gpu_info.get("vram_used_mb") or 0
        available_mb = gpu_info.get("vram_available_mb") or (vram_mb - used_mb)

        return {
            "gpu_name": gpu_info.get("name", "Unknown"),
            "gpu_compute_capability": gpu_info.get("compute_capability"),
            "vram_total_gb": round((vram_mb / 1024), 2),
            "vram_used_gb": round((used_mb / 1024), 2),
            "vram_available_gb": round((available_mb / 1024), 2),
            "utilization_percent": gpu_info.get("utilization_percent") or 0,
        }

    # ===========================================
    # Error Handling (Phase 9)
    # ===========================================

    def handle_error(self, error_type: str, job_id: Optional[str] = None, 
                     workflow: Optional[Dict] = None, inputs: Optional[Dict] = None) -> Dict[str, Any]:
        """Handle common ComfyUI errors."""
        error_messages = {
            "missing_model": "One or more required models are not loaded. Please load them in LM Studio or ComfyUI.",
            "missing_node": "Workflow contains missing nodes. Check your workflow JSON for errors.",
            "out_of_vram": f"VRAM usage too high. Current: {self.get_vram_info().get('vram_used_gb', 0)}GB / Total: {self.get_vram_info().get('vram_total_gb', 12)}GB",
            "timeout": "Generation took too long. Check your workflow or increase timeout.",
            "invalid_workflow": "Workflow JSON is invalid or contains errors.",
        }

        return {
            "success": False,
            "error_type": error_type,
            "job_id": job_id,
            "message": error_messages.get(error_type, f"Unknown error: {error_type}"),
            "workflow_error": workflow if workflow else None,
            "input_error": inputs if inputs else None,
        }


# Export for API routes
__all__ = ["ComfyUIManager"]
