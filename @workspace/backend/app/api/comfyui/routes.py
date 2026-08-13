"""ComfyUI Manager API routes."""

import json
import os
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from app.api.comfyui.service import ComfyUIManager


router = APIRouter(prefix="/api/v1/dashboard/comfyui", tags=["ComfyUI Manager"])


def _get_comfyui_manager() -> ComfyUIManager:
    """Get a new instance of ComfyUI manager."""
    return ComfyUIManager()


@router.get("/status")
async def get_comfyui_status() -> Dict[str, Any]:
    """Get ComfyUI server status and health information."""
    comfyui_manager = _get_comfyui_manager()

    try:
        is_connected = comfyui_manager.is_connected()

        if not is_connected:
            return {
                "success": True,
                "server_status": "disconnected",
                "server_url": comfyui_manager.server_url,
                "comfyui_version": None,
                "response_time_ms": None,
                "last_health_check": None,
                "error_message": None,
            }

        response_time = comfyui_manager.get_response_time()
        last_health_check = comfyui_manager._last_health_check.isoformat() if comfyui_manager._last_health_check else None

        return {
            "success": True,
            "server_status": "connected",
            "server_url": comfyui_manager.server_url,
            "comfyui_version": None,
            "response_time_ms": comfyui_manager.get_response_time_ms(),
            "last_health_check": last_health_check,
            "error_message": None,
        }

    except Exception as e:
        return {
            "success": True,
            "server_status": "unavailable",
            "server_url": comfyui_manager.server_url,
            "comfyui_version": None,
            "response_time_ms": None,
            "last_health_check": None,
            "error_message": f"Server unavailable: {str(e)}",
        }


@router.get("/system")
async def get_system_info() -> Dict[str, Any]:
    """Get system information from ComfyUI."""
    comfyui_manager = _get_comfyui_manager()

    try:
        stats = comfyui_manager.get_system_stats()

        return {
            "success": True,
            "version": stats.get("version") if isinstance(stats, dict) and stats.get("success") else None,
            "gpu_info": stats.get("gpu_info", {}) if isinstance(stats, dict) else {},
            "memory_info": stats.get("memory_info", {}) if isinstance(stats, dict) else {},
            "error_message": stats.get("error_message") if isinstance(stats, dict) else None,
        }

    except Exception as e:
        return {
            "success": True,
            "version": None,
            "gpu_info": {},
            "memory_info": {},
            "error_message": f"Failed to get system info: {str(e)}",
        }


@router.get("/queue")
async def get_queue_status() -> Dict[str, Any]:
    """Get queue status information."""
    comfyui_manager = _get_comfyui_manager()

    try:
        queue_data = comfyui_manager.get_queue_status()

        return {
            "success": True,
            "running": queue_data.get("running", []) if isinstance(queue_data, dict) else [],
            "pending": queue_data.get("pending", []) if isinstance(queue_data, dict) else [],
            "completed": (queue_data.get("completed") or [])[-10:] if isinstance(queue_data, dict) else [],
            "failed": (queue_data.get("failed") or [])[-10:] if isinstance(queue_data, dict) else [],
            "total_running": queue_data.get("total_running", 0) if isinstance(queue_data, dict) else 0,
            "total_pending": queue_data.get("total_pending", 0) if isinstance(queue_data, dict) else 0,
            "total_completed": queue_data.get("total_completed", 0) if isinstance(queue_data, dict) else 0,
            "total_failed": queue_data.get("total_failed", 0) if isinstance(queue_data, dict) else 0,
            "error_message": queue_data.get("error_message") if isinstance(queue_data, dict) else None,
        }

    except Exception as e:
        return {
            "success": True,
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


@router.get("/queue/position/{job_id}")
async def get_queue_position(job_id: str) -> Dict[str, Any]:
    """Get position of a specific job in the queue."""
    comfyui_manager = _get_comfyui_manager()

    try:
        position_data = comfyui_manager.get_queue_position(job_id)

        return {
            "success": True,
            "job_id": job_id,
            "position": position_data.get("position") if isinstance(position_data, dict) else None,
            "status": position_data.get("status") if isinstance(position_data, dict) else None,
            "error_message": position_data.get("error_message") if isinstance(position_data, dict) else None,
        }

    except Exception as e:
        return {
            "success": True,
            "job_id": job_id,
            "position": None,
            "status": "ERROR",
            "error_message": f"Failed to get queue position: {str(e)}",
        }


@router.get("/history")
async def get_workflow_history(limit: int = 20) -> Dict[str, Any]:
    """Get history of executed workflows."""
    comfyui_manager = _get_comfyui_manager()

    try:
        history_data = comfyui_manager.get_workflow_history(limit)

        return {
            "success": True,
            "workflows": history_data.get("workflows", []) if isinstance(history_data, dict) else [],
            "count": history_data.get("count", 0) if isinstance(history_data, dict) else 0,
            "error_message": history_data.get("error_message") if isinstance(history_data, dict) else None,
        }

    except Exception as e:
        return {
            "success": True,
            "workflows": [],
            "count": 0,
            "error_message": f"Failed to get workflow history: {str(e)}",
        }


@router.get("/history/{job_id}")
async def get_job_details(job_id: str) -> Dict[str, Any]:
    """Get details of a specific job."""
    comfyui_manager = _get_comfyui_manager()

    try:
        details_data = comfyui_manager.get_job_details(job_id)

        return {
            "success": True,
            "job_id": job_id if details_data.get("success") else None,
            "workflow": details_data.get("workflow", "") if isinstance(details_data, dict) else "",
            "status": details_data.get("status", "") if isinstance(details_data, dict) else "",
            "start_time": details_data.get("start_time") if isinstance(details_data, dict) else None,
            "end_time": details_data.get("end_time") if isinstance(details_data, dict) else None,
            "duration": details_data.get("duration") if isinstance(details_data, dict) else None,
            "outputs": details_data.get("outputs", []) if isinstance(details_data, dict) else [],
            "errors": details_data.get("errors") if isinstance(details_data, dict) else None,
            "error_message": details_data.get("error_message") if isinstance(details_data, dict) else None,
        }

    except Exception as e:
        return {
            "success": True,
            "job_id": job_id,
            "workflow": "",
            "status": "ERROR",
            "start_time": None,
            "end_time": None,
            "duration": None,
            "outputs": [],
            "errors": None,
            "error_message": f"Failed to get job details: {str(e)}",
        }


@router.get("/history/{job_id}/outputs")
async def get_job_outputs(job_id: str) -> Dict[str, Any]:
    """Get list of output files for a completed job."""
    comfyui_manager = _get_comfyui_manager()

    try:
        outputs_data = comfyui_manager.get_job_output_files(job_id)

        return {
            "success": True,
            "job_id": job_id,
            "outputs": outputs_data.get("outputs", []) if isinstance(outputs_data, dict) else [],
            "count": outputs_data.get("count", 0) if isinstance(outputs_data, dict) else 0,
            "error_message": outputs_data.get("error_message") if isinstance(outputs_data, dict) else None,
        }

    except Exception as e:
        return {
            "success": True,
            "job_id": job_id,
            "outputs": [],
            "count": 0,
            "error_message": f"Failed to get output files: {str(e)}",
        }


@router.post("/submit")
async def submit_workflow(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Submit a workflow to ComfyUI for execution."""
    comfyui_manager = _get_comfyui_manager()

    try:
        workflow = payload.get("workflow")
        inputs = payload.get("inputs", {}) or {}

        if not workflow:
            return {
                "success": False,
                "status": "error",
                "job_id": None,
                "message": "No workflow provided in request body.",
                "error_message": "Workflow is required for submission.",
            }

        # Handle file paths or JSON strings
        if isinstance(workflow, str) and len(workflow) <= 1024 * 1024:
            try:
                parsed = json.loads(workflow)
                if isinstance(parsed, dict):
                    workflow_str = json.dumps(parsed)
                    result = comfyui_manager.submit_workflow(workflow_str, inputs)
                else:
                    raise ValueError("Invalid workflow object")
            except Exception:
                if not os.path.exists(workflow):
                    return {
                        "success": False,
                        "status": "error",
                        "job_id": None,
                        "message": "Workflow file not found",
                        "error_message": f"Workflow file not found: {workflow}",
                    }
                workflow_str = open(workflow, "r").read()
                result = comfyui_manager.submit_workflow(workflow_str, inputs)
        else:
            result = comfyui_manager.submit_workflow(workflow, inputs)

        return result

    except Exception as e:
        return {
            "success": False,
            "status": "error",
            "job_id": None,
            "message": f"Failed to submit workflow: {str(e)}",
            "error_message": str(e),
        }


@router.post("/submit/file")
async def submit_workflow_from_file(filepath: Optional[str] = None, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Submit a workflow from file."""
    comfyui_manager = _get_comfyui_manager()

    try:
        result: Optional[Dict[str, Any]] = None

        if filepath:
            result = comfyui_manager.submit_workflow_from_file(filepath)
        elif payload and isinstance(payload, dict):
            if "workflow" in payload:
                workflow = payload["workflow"]
                inputs = payload.get("inputs", {}) or {}

                if isinstance(workflow, str) and len(workflow) <= 1024 * 1024:
                    try:
                        parsed = json.loads(workflow)
                        if isinstance(parsed, dict):
                            workflow_str = json.dumps(parsed)
                            result = comfyui_manager.submit_workflow(workflow_str, inputs)
                        else:
                            raise ValueError("Invalid workflow object")
                    except Exception as parse_e:
                        return {
                            "success": False,
                            "status": "error",
                            "job_id": None,
                            "message": "Failed to parse workflow JSON",
                            "error_message": str(parse_e),
                        }
                else:
                    result = comfyui_manager.submit_workflow(workflow, inputs)
        else:
            return {
                "success": False,
                "status": "error",
                "job_id": None,
                "message": "No filepath or workflow provided in request body.",
                "error_message": "Provide either 'filepath' parameter or 'workflow' in payload.",
            }

        return result or {
            "success": False,
            "status": "error",
            "job_id": None,
            "message": "Failed to process workflow submission",
            "error_message": "No valid workflow provided",
        }

    except Exception as e:
        return {
            "success": False,
            "status": "error",
            "job_id": None,
            "message": f"Failed to submit workflow from file: {str(e)}",
            "error_message": str(e),
        }


@router.post("/cancel/{job_id}")
async def cancel_job(job_id: str) -> Dict[str, Any]:
    """Cancel a running job."""
    comfyui_manager = _get_comfyui_manager()

    try:
        result = comfyui_manager.cancel_job(job_id)

        return {
            "success": True,
            "status": result.get("status", "") if isinstance(result, dict) else "",
            "job_id": job_id,
            "message": result.get("message") if isinstance(result, dict) else None,
            "error_message": result.get("error_message") if isinstance(result, dict) else None,
        }

    except Exception as e:
        return {
            "success": False,
            "status": "error",
            "job_id": job_id,
            "message": f"Failed to cancel job: {str(e)}",
            "error_message": str(e),
        }


@router.get("/output/{filename}")
async def get_output_preview(filename: str) -> Dict[str, Any]:
    """Get preview of an output file."""
    comfyui_manager = _get_comfyui_manager()

    try:
        preview_data = comfyui_manager.get_output_preview(filename)

        if not preview_data:
            return {
                "success": False,
                "filename": filename,
                "preview_url": None,
                "content_length": 0,
                "message": f"Preview unavailable for: {filename}",
            }

        return {
            "success": True,
            "filename": preview_data.get("filename") if isinstance(preview_data, dict) else filename,
            "view_url": preview_data.get("view_url") if isinstance(preview_data, dict) else None,
            "content_length": preview_data.get("content_length", 0) if isinstance(preview_data, dict) else 0,
            "preview_available": preview_data.get("preview_available") if isinstance(preview_data, dict) else False,
        }

    except Exception as e:
        return {
            "success": False,
            "filename": filename,
            "preview_url": None,
            "content_length": 0,
            "message": f"Failed to get preview: {str(e)}",
        }


@router.get("/download/{filename:path}")
async def download_output(filename: str) -> Dict[str, Any]:
    """Download an output file."""
    comfyui_manager = _get_comfyui_manager()

    try:
        download_data = comfyui_manager.download_output(filename)

        if not isinstance(download_data, dict):
            return {
                "success": False,
                "file_info": None,
                "message": f"Failed to download: {download_data}",
            }

        if not download_data.get("success"):
            error_msg = download_data.get("error_message") or "Unknown error"
            return {
                "success": False,
                "file_info": None,
                "message": f"Failed to download: {error_msg}",
            }

        file_info = download_data.get("file_info") or {}

        return {
            "success": True,
            "filename": file_info.get("filename", filename),
            "content_type": file_info.get("content_type", ""),
            "size_bytes": file_info.get("size_bytes", 0),
            "is_image": file_info.get("is_image", False),
            "is_video": file_info.get("is_video", False),
            "message": f"Downloaded {filename} ({file_info.get('size_bytes', 0)} bytes)",
        }

    except Exception as e:
        return {
            "success": False,
            "file_info": None,
            "message": f"Failed to download output: {str(e)}",
        }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Perform comprehensive health check."""
    comfyui_manager = _get_comfyui_manager()

    try:
        health_data = comfyui_manager.health_check()

        return {
            "success": True,
            "server_reachable": health_data.get("server_reachable") if isinstance(health_data, dict) else False,
            "api_available": health_data.get("api_available") if isinstance(health_data, dict) else False,
            "queue_accessible": health_data.get("queue_accessible") if isinstance(health_data, dict) else False,
            "workflow_accessible": health_data.get("workflow_accessible") if isinstance(health_data, dict) else False,
            "generation_available": health_data.get("generation_available") if isinstance(health_data, dict) else True,
        }

    except Exception as e:
        return {
            "success": True,
            "server_reachable": False,
            "api_available": False,
            "queue_accessible": False,
            "workflow_accessible": False,
            "generation_available": False,
            "error_message": f"Health check failed: {str(e)}",
        }


@router.get("/vram")
async def get_vram_info() -> Dict[str, Any]:
    """Get detailed VRAM information from ComfyUI."""
    comfyui_manager = _get_comfyui_manager()

    try:
        vram_data = comfyui_manager.get_vram_info()

        return {
            "success": True,
            "gpu_name": vram_data.get("gpu_name") if isinstance(vram_data, dict) else "Unknown",
            "vram_total_gb": vram_data.get("vram_total_gb") if isinstance(vram_data, dict) else 0,
            "vram_used_gb": vram_data.get("vram_used_gb") if isinstance(vram_data, dict) else 0,
            "vram_available_gb": vram_data.get("vram_available_gb") if isinstance(vram_data, dict) else 0,
            "utilization_percent": vram_data.get("utilization_percent") if isinstance(vram_data, dict) else 0,
        }

    except Exception as e:
        return {
            "success": True,
            "gpu_name": "Unknown",
            "vram_total_gb": 0,
            "vram_used_gb": 0,
            "vram_available_gb": 0,
            "utilization_percent": 0,
            "error_message": f"Failed to get VRAM info: {str(e)}",
        }


@router.post("/error")
async def handle_error(error_type: str, job_id: Optional[str] = None, 
                       workflow: Optional[Dict] = None, inputs: Optional[Dict] = None) -> Dict[str, Any]:
    """Handle common ComfyUI errors."""
    comfyui_manager = _get_comfyui_manager()

    try:
        error_result = comfyui_manager.handle_error(error_type, job_id, workflow, inputs)

        return {
            "success": True,
            "error_type": error_result.get("error_type") if isinstance(error_result, dict) else error_type,
            "job_id": error_result.get("job_id") if isinstance(error_result, dict) else job_id,
            "message": error_result.get("message") if isinstance(error_result, dict) else f"Unknown error: {error_type}",
            "workflow_error": error_result.get("workflow_error") if isinstance(error_result, dict) else None,
            "input_error": error_result.get("input_error") if isinstance(error_result, dict) else None,
        }

    except Exception as e:
        return {
            "success": True,
            "error_type": error_type,
            "job_id": job_id,
            "message": f"Error handling failed: {str(e)}",
            "workflow_error": workflow,
            "input_error": inputs,
        }
