#!/usr/bin/env python3
"""
Response Parser for Sanskriti AI Studio Vision Service.

This module provides a reusable parser to convert Vision model responses
into a standardized runtime object structure.

Standardized Response Schema:
{
  "status": "success | error | warning",
  "summary": "Brief summary of findings",
  "model_used": "Model identifier used",
  "latency_ms": Request duration in milliseconds,
  "components": [{"type": "...", "description": "..."}],
  "ocr": "Extracted text content",
  "issues": [{"type": "...", "severity": "...", "message": "..."}],
  "warnings": ["Warning message 1", "Warning message 2"],
  "confidence": "High | Medium | Low",
  "suggested_fixes": ["Fix suggestion 1", "Fix suggestion 2"]
}

This parser normalizes responses from:
- General analysis
- Component detection
- OCR extraction
- Error detection
- Layout analysis
- UI verification
- Visual regression

Version: 1.0
Last Updated: 2026-08-06
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

# Configure logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("response_parser")


class ParseError(Exception):
    """Exception raised when response parsing fails."""
    pass


class VisionResponseParser:
    """
    Parser for normalizing Vision model responses into standardized format.
    
    The parser handles:
    - JSON responses from model
    - Text-based responses with structured extraction
    - Mixed content with code blocks
    - Error responses
    
    It extracts and normalizes fields:
    - Summary
    - Components
    - OCR text
    - Issues (errors/problems)
    - Warnings
    - Confidence level
    - Suggested fixes
    """
    
    # Field extraction patterns
    SUMMARY_PATTERN = r"(?:summary|overall|analysis|description)[,\.\s]+([\'\"\[\]\:\w\s.]+\n?)*"
    COMPONENTS_PATTERN = r"(?:detected|found|identified)\s*(?:components?|elements?|ui elements)?[:,\s]+([^\n]+)"
    OCR_PATTERN = r"(?:extracted|text|content|ocr)[,\.\s]+([\'\"\[\]\:\w\s.]+\n)*"
    ISSUES_PATTERN = r"(?:issue|problem|error|warning|alert|failure)[,\.\s]+([\'\"\[\]\:\w\s.]+\n?)+|\*\*(.+?)\*\*"
    WARNING_PATTERN = r"(?:warning|note|caution|attention)[,\.\s]+([\'\"\[\]\:\w\s.]+\n?)+(\d+)"
    SUGGESTED_FIXES_PATTERN = r"(?:recommend|suggest|fix|solution|improve)[,\.\s]+([\'\"\[\]\:\w\s.]+\n?)+(\d+)"
    CONFIDENCE_PATTERN = r"(?:confidence|certainty)\s*:?\s*(high|medium|low|confident|uncertain)"
    
    def __init__(self):
        """Initialize the response parser."""
        self._parse_count: int = 0
    
    @property
    def parse_count(self) -> int:
        """Get total number of parses performed."""
        return self._parse_count
    
    def parse(
        self,
        raw_response: Dict[str, Any],
        task_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Parse a vision model response into standardized format.
        
        Args:
            raw_response: Raw API response from Vision model
            task_type: Type of task performed (general, component_detection, etc.)
            
        Returns:
            Standardized response dictionary
            
        Raises:
            ParseError: If parsing fails completely
        """
        self._parse_count += 1
        
        try:
            # Check for empty response
            if not raw_response:
                raise ParseError("Response is empty or None")
            
            choices = raw_response.get("choices", [])
            
            if not choices:
                raise ParseError("No choices in model response")
            
            content = choices[0].get("message", {}).get("content", "")
            
            if not content:
                raise ParseError("No content in model message")
            
            # Try JSON parsing first
            parsed_json = None
            try:
                parsed_json = json.loads(content)
            except (json.JSONDecodeError, TypeError):
                pass
            
            if isinstance(parsed_json, dict):
                # Normalize JSON response to standard format
                return self._normalize_json_response(parsed_json, task_type or "general")
            
            # Fall back to structured extraction from text
            return self._extract_from_text(content, task_type or "general")
            
        except ParseError:
            raise
        except Exception as e:
            logger.error(f"[RESPONSE-PARSER] Unexpected error parsing response: {e}")
            raise ParseError(f"Response parsing failed: {str(e)}")
    
    def _normalize_json_response(
        self,
        parsed_data: Dict[str, Any],
        task_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Normalize any model JSON response to standard schema.
        
        Args:
            parsed_data: Parsed JSON response from model
            task_type: Type of task performed
            
        Returns:
            Standardized response dictionary
        """
        summary = parsed_data.get("summary", "")
        
        # Initialize standard structure
        normalized = {
            "status": self._determine_status(parsed_data, task_type),
            "task_type": task_type or "general",
            "model_used": parsed_data.get("model", parsed_data.get("id", "unknown")),
            "summary": str(summary)[:5000] if summary else "",
            "components": [],
            "ocr": "",
            "issues": [],
            "warnings": [],
            "confidence": "High",  # Default
            "suggested_fixes": [],
        }
        
        # Extract components if present
        for key in ["detected_components", "components", "found_components", "elements"]:
            if key in parsed_data:
                normalized["components"] = parsed_data[key]
                break
        
        # Extract OCR/text content if present
        for key in ["ocr_text", "text", "extracted_text", "content"]:
            if key in parsed_data:
                normalized["ocr"] = str(parsed_data[key])[:5000]
                break
        
        # Extract issues/errors if present
        for key in ["errors", "issues", "problems", "errors_found"]:
            if key in parsed_data:
                normalized["issues"] = self._clean_list(parsed_data[key])
                break
        
        # Extract warnings if present
        if "warnings" in parsed_data:
            normalized["warnings"] = self._clean_list(parsed_data["warnings"])
        
        # Extract suggested fixes/recommendations if present
        for key in ["suggested_fixes", "recommendations", "fixes", "recommendations"]:
            if key in parsed_data:
                normalized["suggested_fixes"] = self._clean_list(parsed_data[key])
                break
        
        # Extract alignment issues if present
        if "alignment_issues" in parsed_data:
            normalized["issues"].extend(self._clean_list(parsed_data["alignment_issues"]))
        
        # Extract missing components
        if "missing_components" in parsed_data:
            normalized["components"] = self._append_list(
                normalized["components"], 
                [{"type": "MISSING", "description": f"Missing: {m}" } for m in parsed_data["missing_components"]]
            )
        
        # Extract missing elements
        if "missing_elements" in parsed_data:
            normalized["issues"].extend(self._clean_list(parsed_data["missing_elements"]))
        
        # Set confidence based on status and content quality
        if normalized["status"] == "error":
            normalized["confidence"] = "Low"
        elif len(str(summary or "")) > 100:
            normalized["confidence"] = "High"
        else:
            normalized["confidence"] = "Medium"
        
        # Log parsing for audit
        logger.debug(f"[RESPONSE-PARSER] Normalized JSON - Task: {task_type}, Status: {normalized['status']}")
        
        return normalized
    
    def _extract_from_text(
        self,
        text: str,
        task_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract structured information from unstructured text response.
        
        Args:
            text: Raw text response from model
            task_type: Type of task performed
            
        Returns:
            Standardized response dictionary with extracted fields
        """
        # Initialize all fields as empty for type safety
        result = {
            "status": "success",
            "task_type": task_type or "general",
            "summary": (text[:1000] if text else ""),
            "model_used": self._extract_model_from_text(text),
            "components": [],
            "ocr": "",
            "issues": [],
            "warnings": [],
            "confidence": "Medium",
            "suggested_fixes": [],
        }
        
        # Extract components
        comp_match = re.search(self.COMPONENTS_PATTERN, text, re.IGNORECASE)
        if comp_match:
            detected_components = self._extract_list_from_match(comp_match.group(1))
            result["components"] = detected_components
        
        # Extract OCR/text content
        text_patterns = [
            (self.OCR_PATTERN, "ocr"),
            (r"(?:all|visible)\s*text[:,\s]+([^\n]+)", "ocr"),
        ]
        
        for pattern, field in text_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and match.group(1):
                result[field] = match.group(1).strip()[:5000]
                break
        
        # Extract errors - each tuple has (pattern, field_name)
        error_patterns = [
            (r"(?:error|fail)[,\s]+([^\n]+)", "issues"),  # Capturing group for error text
            (r"(?:warning)[,\s]+([^\n]+)", "warnings"),  # Capturing group for warning text
        ]
        
        for pattern, field in error_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # With single capturing group, findall returns strings directly (not tuples)
                result[field] = self._clean_list([m.strip() for m in matches[:5]])
        
        # Extract recommendations/fixes
        fix_pattern = r"(?:recommend|suggest|fix)[,\s]+([^\n]+)"
        fixes = re.findall(fix_pattern, text, re.IGNORECASE)
        if fixes:
            result["suggested_fixes"] = self._clean_list([f.strip() for f in fixes[:5]])
        
        # Extract issues from markdown code blocks
        code_blocks = re.findall(r"```(?:json)?([^`]+)```", text, re.DOTALL)
        for block in code_blocks:
            try:
                parsed = json.loads(block)
                if "errors" in parsed:
                    result["issues"].extend(self._clean_list(parsed["errors"]))
                if "warnings" in parsed:
                    result["warnings"].extend(self._clean_list(parsed["warnings"]))
                if "suggested_fixes" in parsed or "recommendations" in parsed:
                    fixes_key = "suggested_fixes" if "suggested_fixes" in parsed else "recommendations"
                    result["suggested_fixes"].extend(self._clean_list(parsed[fixes_key]))
            except json.JSONDecodeError:
                continue
        
        # Determine status based on content
        status_indicators = [
            "error", "fail", "failed", "exception", "bug", "broken",
            "warning", "caution", "attention", "note", "issue", "problem",
            "missing", "not found", "invalid", "incorrect",
        ]
        
        for indicator in status_indicators:
            if re.search(rf"{indicator}[:\s]", text, re.IGNORECASE):
                result["status"] = "warning" if "error" not in str(text).lower() else "error"
                break
        
        # Log parsing for audit
        logger.debug(f"[RESPONSE-PARSER] Extracted from text - Task: {task_type}, Status: {result['status']}")
        
        return result
    
    def _determine_status(
        self,
        parsed_data: Dict[str, Any],
        task_type: Optional[str] = None,
    ) -> str:
        """Determine response status based on content."""
        if parsed_data.get("status"):
            return str(parsed_data["status"]).lower()
        
        # Check for explicit error markers
        status_keywords = ["error", "fail", "exception"]
        summary = str(parsed_data.get("summary") or "")
        
        for keyword in status_keywords:
            if keyword in summary.lower():
                return "error"
        
        return "success"
    
    def _extract_list_from_match(self, match_text: str) -> List[Dict[str, Any]]:
        """Extract list items from a matched text string."""
        # Handle bullet points or numbered lists
        items = re.split(r'[\n\-•\*]', match_text.strip())
        
        components = []
        for item in items[:10]:  # Limit to first 10
            if item.strip():
                try:
                    parsed = json.loads(item)
                    if isinstance(parsed, dict):
                        components.append(parsed)
                    else:
                        components.append({"type": "unknown", "description": str(parsed)[:200]})
                except json.JSONDecodeError:
                    # Parse as plain description
                    parts = item.split(":")
                    if len(parts) == 2:
                        components.append({
                            "type": parts[0].strip(),
                            "description": parts[1].strip()[:200],
                        })
                    else:
                        components.append({"type": "unknown", "description": item.strip()[:200]})
        
        return components
    
    def _extract_model_from_text(self, text: str) -> str:
        """Extract model name from text response."""
        patterns = [
            r"model\s*:\s*([^\n]+)",
            r"used\s+(?:by|for)\s*[:\s]+([^\n]+)",
            r"\*\*(.+?)\*\*",  # Markdown bold
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                model_name = match.group(1).strip()
                if "qwen" in model_name.lower():
                    return model_name
                
        return "unknown"
    
    def _clean_list(self, items: List[Any]) -> List[str]:
        """Clean and deduplicate a list of items."""
        cleaned = []
        seen = set()
        
        for item in items[:10]:  # Limit to first 10
            if isinstance(item, (str, dict)):
                text = str(item).strip()
                if text and text not in seen:
                    seen.add(text)
                    cleaned.append(text)
        
        return cleaned
    
    def _append_list(
        self,
        existing: List[Dict[str, Any]],
        new_items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Append unique items to an existing list."""
        seen = {str(tuple(sorted(i.items()))) for i in existing}
        
        result = list(existing)
        for item in new_items[:10]:
            key = str(tuple(sorted(item.items())))
            if key not in seen:
                seen.add(key)
                result.append(item)
        
        return result
    
    def normalize_for_logging(
        self,
        response: Dict[str, Any],
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Normalize response for logging purposes.
        
        Args:
            response: Parsed response dictionary
            request_id: Request identifier for correlation
            
        Returns:
            Logging-friendly dictionary with truncated values
        """
        loggable = {
            "request_id": request_id or self._generate_request_id(),
            "status": response.get("status"),
            "task_type": response.get("task_type", "unknown"),
            "summary": response.get("summary", "")[:500],  # Truncate summary
            "model_used": response.get("model_used", "unknown"),
            "has_issues": len(response.get("issues", [])) > 0,
            "issue_count": len(response.get("issues", [])),
            "warning_count": len(response.get("warnings", [])),
            "confidence": response.get("confidence", "Unknown"),
        }
        
        if loggable["status"] == "error":
            loggable["errors"] = response.get("issues", [])[:5]
        
        return loggable
    
    def _generate_request_id(self) -> str:
        """Generate a request ID for logging when one is not provided."""
        import uuid
        return f"req_{uuid.uuid4().hex[:8]}"


# Export public interface
__all__ = [
    "VisionResponseParser",
    "ParseError",
]
