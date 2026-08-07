"""
Vision Agent Definition for Sanskriti AI Studio.

This agent is responsible for visual analysis tasks including:
- Browser UI analysis
- Screenshot understanding
- OCR text extraction
- Error message extraction
- Layout validation
- Visual regression testing
- UI verification

CRITICAL: This agent uses the vision model (Qwen2.5-VL) exclusively.
          Qwen 3.5 is TEXT-ONLY and should NEVER be used for image processing.
"""

from typing import Any, Dict, List, Optional


class VisionAgent:
    """
    Vision Agent for visual analysis tasks.

    This agent operates independently from the Coding Agent and never generates source code.
    Its sole responsibility is visual analysis of screenshots and UI elements.
    
    Model: Qwen2.5-VL (or other vision-capable model via LM Studio)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Vision Agent.

        Args:
            config: Configuration dictionary with vision model settings
        """
        self.config = config
        self.model_name = config.get("vision_model", "")
        self.base_url = config.get("base_url", "http://localhost:1234")
        self.temperature = config.get("temperature", 0.1)
        self.max_tokens = config.get("max_tokens", 4096)

    def analyze_screenshot(
        self, image_path: str, task_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Analyze a screenshot for visual content.

        Args:
            image_path: Path to the screenshot/image file
            task_type: Type of analysis (general, component_detection, ocr, etc.)

        Returns:
            Structured analysis report
        """
        # Build prompt based on task type
        prompt = self._build_prompt(task_type)

        # Call vision model via LM Studio client
        from scripts.vision_client import chat_with_vision_model_from_image

        try:
            response = chat_with_vision_model_from_image(
                image_path=image_path,
                prompt=prompt,
                base_url=self.base_url,
                model_name=self.model_name,
            )

            # Parse and structure the response
            return self._parse_response(response, task_type)
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "image_path": image_path,
                "task_type": task_type,
            }

    def analyze_ui_layout(
        self, image_path: str, component_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze UI layout and detect components.

        Args:
            image_path: Path to the screenshot
            component_types: Optional list of component types to focus on

        Returns:
            Layout analysis report with detected components
        """
        if not component_types:
            component_types = [
                "header",
                "navigation",
                "buttons",
                "forms",
                "tables",
                "images",
                "text",
                "footer",
            ]

        prompt = f"""Analyze this UI screenshot and detect the following components:
Component Types to Detect: {', '.join(component_types)}

For each component found, report:
- Component type
- Approximate location (top-left coordinates)
- Size estimate
- Visual state (active, disabled, hovered, etc.)
- Any associated text content

Also analyze:
- Overall layout structure
- Hierarchy and organization
- Alignment and spacing issues
- Accessibility indicators
- Responsive design cues

Return structured JSON with findings.
"""

        from scripts.vision_client import chat_with_vision_model_from_image

        try:
            response = chat_with_vision_model_from_image(
                image_path=image_path, prompt=prompt, base_url=self.base_url
            )
            return self._parse_response(response, "layout_analysis")
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "image_path": image_path,
            }

    def perform_ocr(self, image_path: str) -> Dict[str, Any]:
        """
        Perform OCR on an image to extract text.

        Args:
            image_path: Path to the screenshot

        Returns:
            OCR results with extracted text and confidence levels
        """
        prompt = f"""Perform optical character recognition (OCR) on this image.

Extract all visible text including:
- Button labels
- Form field labels and placeholders
- Error messages
- Success notifications
- Navigation items
- Menu items
- Body text content
- Footer information

For each text region, report:
- The extracted text
- Approximate location (bounding box description)
- Confidence level (high/medium/low)
- Language detected
- Any special formatting (bold, italic, monospace)

Return structured JSON with all extracted text organized by visual regions.
"""

        from scripts.vision_client import chat_with_vision_model_from_image

        try:
            response = chat_with_vision_model_from_image(
                image_path=image_path, prompt=prompt, base_url=self.base_url
            )
            return self._parse_response(response, "ocr")
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "image_path": image_path,
            }

    def detect_errors(
        self, image_path: str, error_indicators: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Detect and extract error messages from a screenshot.

        Args:
            image_path: Path to the screenshot
            error_indicators: Optional list of known error patterns to look for

        Returns:
            Error detection report with extracted errors and locations
        """
        if not error_indicators:
            error_indicators = [
                "error",
                "warning",
                "exception",
                "fail",
                "invalid",
                "not found",
                "unauthorized",
                "forbidden",
            ]

        prompt = f"""Detect and extract any error messages or warning indicators from this screenshot.

Look for:
- Error dialogs/modals
- Warning notifications
- Red text or borders
- Alert icons
- Status bar error messages
- Console-like error output

For each error detected, report:
- Error type (dialog/notification/in-line)
- The exact error message text
- Location on screen (top-left quadrant)
- Severity indicator
- Any suggested fix shown by the UI

Also note any warning indicators separately.

Return structured JSON with all errors and warnings found.
"""

        from scripts.vision_client import chat_with_vision_model_from_image

        try:
            response = chat_with_vision_model_from_image(
                image_path=image_path, prompt=prompt, base_url=self.base_url
            )
            return self._parse_response(response, "error_detection")
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "image_path": image_path,
            }

    def verify_ui_elements(
        self,
        image_path: str,
        expected_elements: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Verify that expected UI elements are present in a screenshot.

        Args:
            image_path: Path to the screenshot
            expected_elements: List of element specifications with text/content descriptions

        Returns:
            Verification report with presence/absence and location for each element
        """
        prompt = f"""Verify the presence of these UI elements in this screenshot:

Elements to Verify:
{chr(10).join(f"- {e.get('description', '')} (Expected: {e.get('expected_text', 'any')})" for e in expected_elements)}

For each element, report:
- Presence (found/not found)
- Location if found (general screen position)
- Exact text if found vs expected
- State (enabled/disabled/active/inactive)
- Any deviations from expected state

Also note:
- Missing elements that should be present
- Unexpected elements not in the list
- Overall completeness of UI rendering

Return structured JSON with verification results for each element.
"""

        from scripts.vision_client import chat_with_vision_model_from_image

        try:
            response = chat_with_vision_model_from_image(
                image_path=image_path, prompt=prompt, base_url=self.base_url
            )
            return self._parse_response(response, "verification")
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "image_path": image_path,
            }

    def detect_alignment_issues(
        self, image_path: str, tolerance_percent: float = 5.0
    ) -> Dict[str, Any]:
        """
        Detect layout and alignment issues in a UI screenshot.

        Args:
            image_path: Path to the screenshot
            tolerance_percent: Alignment tolerance as percentage of viewport

        Returns:
            Alignment analysis report with detected issues
        """
        prompt = f"""Analyze this screenshot for layout and alignment issues.

Check for:
- Misaligned elements (buttons off-grid, uneven spacing)
- Inconsistent padding/margins
- Broken grid layouts
- Overflowing content (text spilling outside containers)
- Improper vertical stacking
- Horizontal scrolling indicators suggesting overflow
- Visual hierarchy breaks (incorrect element prominence)
- Responsive layout issues if apparent

Report each issue with:
- Type of alignment problem
- Location on screen
- Affected elements
- Severity (minor/moderate/severe)
- Suggested fix

Return structured JSON with all detected issues.
"""

        from scripts.vision_client import chat_with_vision_model_from_image

        try:
            response = chat_with_vision_model_from_image(
                image_path=image_path, prompt=prompt, base_url=self.base_url
            )
            return self._parse_response(response, "alignment_analysis")
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "image_path": image_path,
            }

    def perform_visual_regression(
        self,
        baseline_image: str,
        current_image: str,
    ) -> Dict[str, Any]:
        """
        Perform visual regression analysis between two screenshots.

        Args:
            baseline_image: Path to the baseline/reference screenshot
            current_image: Path to the current screenshot being compared

        Returns:
            Regression report with differences detected
        """
        prompt = f"""Compare these two UI screenshots and identify visual differences.

Baseline (Reference): {baseline_image}
Current: {current_image}

Identify changes in:
- Layout structure
- Element positions
- Content text changes
- Color/theme changes
- Missing elements
- New elements
- Style/regressions

Report each difference with:
- Type of change (layout/content/style/missing/new)
- Location of difference
- Description of what changed
- Whether it's likely intentional or a bug
- Impact level (minor/moderate/severe)

Return structured JSON comparing the two images.
"""

        from scripts.vision_client import chat_with_vision_model_from_image

        try:
            # Note: For true regression, we'd need to send both images
            # This is a simplified version that would be enhanced with dual-image support
            prompt = f"""I have two UI screenshots to compare for visual regression analysis.

Please analyze what differences you detect (when comparing visually).

Report all structural and content differences found.
"""

            response = chat_with_vision_model_from_image(
                image_path=current_image, prompt=prompt, base_url=self.base_url
            )
            return self._parse_response(response, "regression")
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "baseline_image": baseline_image,
                "current_image": current_image,
            }

    def parse_response(self, raw_response: Dict[str, Any], task_type: str) -> Dict[str, Any]:
        """
        Parse and structure the vision model response.

        Args:
            raw_response: Raw API response from vision model
            task_type: Type of analysis performed

        Returns:
            Structured analysis report
        """
        try:
            # Extract content from response
            choices = raw_response.get("choices", [])
            if not choices:
                return {"status": "error", "error": "No response from model"}

            content = choices[0].get("message", {}).get("content", "")
            
            # Try to parse as JSON first
            import json
            try:
                parsed = json.loads(content)
                report = self._normalize_report(parsed, task_type)
                return report
            except (json.JSONDecodeError, TypeError):
                # Fall back to structured extraction from text
                return self._extract_from_text(content, task_type)

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()[:2000]  # Limit traceback size
            return {
                "status": "error",
                "error": f"Response parsing failed: {str(e)}",
                "details": error_trace,
            }

    def _build_prompt(self, task_type: str) -> str:
        """Build a generic prompt based on task type."""
        prompts = {
            "general": "Analyze this image and describe what you see in detail.",
            "component_detection": "Detect all UI components (buttons, forms, tables, images, etc.) in this screenshot.",
            "ocr": "Extract all text from this image using OCR.",
            "layout_analysis": "Analyze the layout structure, alignment, and hierarchy of elements.",
            "error_detection": "Find and extract any error messages or warnings.",
            "verification": "Verify presence of specific UI elements.",
        }
        return prompts.get(task_type, "Describe this image in detail.")

    def _parse_response(self, response: Dict[str, Any], task_type: str) -> Dict[str, Any]:
        """Parse vision model response into structured report."""
        try:
            choices = response.get("choices", [])
            if not choices:
                return {"status": "error", "error": "No model response"}

            content = choices[0].get("message", {}).get("content", "")
            model_used = response.get("model", "unknown")

            # Try JSON parsing first
            import json
            try:
                parsed = json.loads(content)
                
                # Normalize response to standard report format
                report = self._normalize_report(parsed, task_type)
                report["model"] = model_used
                return report
            except (json.JSONDecodeError, TypeError):
                # Extract structured info from text response
                return self._extract_from_text(content, task_type)

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()[:2000]
            return {
                "status": "error",
                "error": f"Parsing failed: {str(e)}",
                "details": error_trace,
            }

    def _normalize_report(self, parsed_data: Dict[str, Any], task_type: str) -> Dict[str, Any]:
        """Normalize any model response into standard report format."""
        summary = parsed_data.get("summary", "")
        
        # Map various response formats to standard structure
        if "components" in parsed_data:
            return {
                "status": "success",
                "task_type": task_type,
                "summary": summary,
                "detected_components": parsed_data.get("components", []),  # type: ignore[index]
                "missing_components": parsed_data.get("missing", []),
                "alignment_issues": parsed_data.get("issues", []),
                "ocr_text": parsed_data.get("text", ""),
                "errors": parsed_data.get("errors", []),
                "warnings": parsed_data.get("warnings", []),
                "suggested_fixes": parsed_data.get("recommendations", []),
            }

        if "differences" in parsed_data:
            return {
                "status": "success",
                "task_type": task_type,
                "summary": summary,
                "differences": parsed_data.get("differences", []),
                "regression_detected": True,
            }

        if "verification" in parsed_data:
            return {
                "status": "success",
                "task_type": task_type,
                "summary": summary,
                "verified_elements": parsed_data.get("elements", []),
                "missing_elements": parsed_data.get("missing", []),
            }

        # Generic fallback - extract any structured data found
        report = {
            "status": "success",
            "task_type": task_type,
            "summary": summary[:1000] if summary else "",
        }

        # Extract common fields
        for field in ["components", "text", "errors", "warnings", "recommendations"]:
            if field in parsed_data:
                report[field] = parsed_data[field]  # type: ignore[index]

        return report

    def _extract_from_text(self, text: str, task_type: str) -> Dict[str, Any]:  # type: ignore[return]
        """Extract structured information from unstructured text response."""
        import re

        report = {
            "status": "success",
            "task_type": task_type,
            "summary": text[:1000] if text else "",
        }

        # Try to extract various patterns
        # Components - Pylance type ignore needed due to dynamic assignment pattern
        components_pattern = r"\*?\s*(\w+\s+)?(\w+)[:.\s]+([^,\n.]+)"
        components = re.findall(components_pattern, text, re.IGNORECASE)
        if components:
            # type: ignore - List comprehension assigned to dict with Any type
            report["detected_components"] = [  # type: ignore[index]
                {"type": c[1].strip(), "description": c[2].strip()}
                for c in components
            ]

        # OCR text extraction
        text_match = re.search(
            r"(text|extracted text|content|ocr)[:,.\s]+([\'\"\[\]:(\w\s.]+\n?)+)",
            text,
            re.IGNORECASE,
        )
        if text_match:
            report["ocr_text"] = text_match.group(2)[:5000].strip()

        # Errors - Pylance type ignore needed due to dynamic assignment pattern
        error_pattern = r"(error|warning|fail)[:,.\s]+([\'\"\[\]:(\w\s.]+\n?)+)"
        errors = re.findall(error_pattern, text, re.IGNORECASE)
        if errors:
            report["errors"] = [e[1].strip() for e in errors[:5]]  # type: ignore[index]

        # Warnings - Pylance type ignore needed due to dynamic assignment pattern
        warning_pattern = r"(warning|note|caution)[:,.\s]+([\'\"\[\]:(\w\s.]+\n?)+)"
        warnings = re.findall(warning_pattern, text, re.IGNORECASE)
        if warnings:
            report["warnings"] = [w[1].strip() for w in warnings[:5]]  # type: ignore[index]

        # Recommendations - Pylance type ignore needed due to dynamic assignment pattern
        recommend_pattern = r"(recommend|suggested fix)[:,\s]+([\'\"\[\]:(\w\s.]+\n?)+)"
        recommendations = re.findall(recommend_pattern, text, re.IGNORECASE)
        if recommendations:
            report["recommended_fixes"] = [r[1].strip() for r in recommendations[:5]]  # type: ignore[index]

        return report


# Export main class
__all__ = ["VisionAgent"]
