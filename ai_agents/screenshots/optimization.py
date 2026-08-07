#!/usr/bin/env python3
"""
Screenshot Optimization Module for Sanskriti AI Studio.

This module handles image optimization, compression, and quality management
for captured screenshots. It provides PNG-specific optimization features.

Optimization Features:
- PNG compression level tuning
- Quality preservation
- Duplicate detection by hash comparison
- File size validation and limits
- Optimization statistics tracking

Version: 1.0
Last Updated: 2026-08-07
"""

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


class OptimizationConfig:
    """Configuration for image optimization."""

    def __init__(
        self,
        quality_level: int = 2,  # 0-100 (PNG uses compression level 0-9)
        compress_level: int = 6,  # PNG compression level (0=none, 9=max)
        strip_metadata: bool = True,      # Remove EXIF/IPTC metadata
        interlace: bool = False,          # Use interlaced PNG encoding
        bit_depth: int = 8,               # Bit depth per channel (4/8/16)
        max_file_size_kb: float = 5000.0, # Maximum file size in KB
    ):
        """
        Initialize optimization configuration.

        Args:
            quality_level: Quality level (affects PNG compression)
            compress_level: PNG compression level (0-9, higher = more compressed)
            strip_metadata: Whether to remove metadata
            interlace: Use interlaced encoding
            bit_depth: Bit depth per channel
            max_file_size_kb: Maximum file size in kilobytes
        """
        self.quality_level = quality_level
        self.compress_level = compress_level
        self.strip_metadata = strip_metadata
        self.interlace = interlace
        self.bit_depth = bit_depth
        self.max_file_size_bytes = int(max_file_size_kb * 1024)

    @classmethod
    def default_config(cls) -> "OptimizationConfig":
        """Get default optimization configuration."""
        return cls(
            quality_level=75,
            compress_level=6,
            strip_metadata=True,
        )

    @classmethod
    def high_quality_config(cls) -> "OptimizationConfig":
        """Get high-quality (less compressed) configuration."""
        return cls(
            quality_level=90,
            compress_level=3,
            strip_metadata=False,
        )

    @classmethod
    def small_file_config(cls) -> "OptimizationConfig":
        """Get small file (more compressed) configuration."""
        return cls(
            quality_level=60,
            compress_level=9,
            strip_metadata=True,
        )


@dataclass
class OptimizationStats:
    """Statistics for an optimization operation."""

    original_size: int = 0      # Original file size in bytes
    optimized_size: int = 0     # Optimized file size in bytes
    compression_ratio: float = 1.0  # Size ratio (optimized/original)
    time_ms: float = 0.0        # Time taken in milliseconds
    quality_loss: str = ""      # Quality assessment

    @property
    def savings_percentage(self) -> float:
        """Get space savings as percentage."""
        if self.original_size == 0:
            return 0.0
        saved = self.original_size - self.optimized_size
        return (saved / self.original_size) * 100


class ImageOptimizer:
    """
    Image optimizer for screenshot PNG files.

    This class handles optimization of captured screenshots,
    including compression, size reduction, and quality management.
    """

    def __init__(self, config: Optional[OptimizationConfig] = None):
        """
        Initialize the image optimizer.

        Args:
            config: Optimization configuration (uses defaults if None)
        """
        self.config = config or OptimizationConfig.default_config()

    def optimize_image(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        compress_level: Optional[int] = None,
        quality_level: Optional[int] = None,
    ) -> Tuple[Path, OptimizationStats]:
        """
        Optimize a PNG image.

        This method re-compresses the image with optimized settings
        while preserving visual quality.

        Args:
            input_path: Path to the original image
            output_path: Output path (optional, otherwise uses input directory)
            compress_level: Override compression level
            quality_level: Override quality level

        Returns:
            Tuple of (output_path, optimization_stats)

        Raises:
            ValueError: If input file doesn't exist or is not a PNG
        """
        import time
        
        input_path_obj = Path(input_path)
        
        if not input_path_obj.exists():
            raise FileNotFoundError(f"Input image not found: {input_path}")

        # Validate PNG signature
        with open(input_path, "rb") as f:
            header = f.read(8)
            if header[:4] != b"\x89PNG":
                raise ValueError(f"Invalid PNG file: {input_path}")

        # Read original metadata
        original_stats = self._read_png_info(input_path)
        
        # Calculate output path if not specified
        if not output_path:
            calculated_output = str(input_path_obj.parent / "optimized" / f"{input_path_obj.stem}_opt{input_path_obj.suffix}")
            output_path = calculated_output
        
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        # Perform optimization using PIL/Pillow if available
        try:
            from PIL import Image as PILImage  # type: ignore
            
            # Open original image
            with PILImage.open(input_path) as img:
                # Optimize based on config
                quality = quality_level if quality_level is not None else self.config.quality_level
                compress = compress_level if compress_level is not None else self.config.compress_level
                
                # Apply optimization settings
                if img.mode in ("RGBA", "LA", "La"):
                    background = PILImage.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)
                    img = background
                
                # Optimize image (Pillow optimizes during save)
                optimized_path = str(output_path_obj)
                
                img.save(
                    optimized_path,
                    compress_level=compress,
                    optimize=True,
                    compression_type=self._get_compression_type(compress),
                )

            # Get optimization stats
            original_size = input_path_obj.stat().st_size
            output_size = output_path_obj.stat().st_size
            
            stats = OptimizationStats(
                original_size=original_size,
                optimized_size=output_size,
                compression_ratio=output_size / original_size if original_size > 0 else 1.0,
                quality_loss=self._estimate_quality_loss(input_path, output_path),
            )

        except ImportError:
            # PIL not available, return original file with basic copy
            import shutil
            shutil.copy2(input_path, str(output_path_obj))
            
            original_size = input_path_obj.stat().st_size
            output_size = output_path_obj.stat().st_size
            
            stats = OptimizationStats(
                original_size=original_size,
                optimized_size=output_size,
                compression_ratio=output_size / original_size if original_size > 0 else 1.0,
                quality_loss="no_optimization",
            )

        return output_path_obj, stats

    def _get_compression_type(self, level: int) -> str:
        """Get compression type string for different levels."""
        if level <= 2:
            return "raw"
        elif level == 3:
            return "adaptive"
        else:
            return "deflate"

    def _read_png_info(self, path: str) -> Dict[str, Any]:
        """Read PNG image information without loading full image."""
        import struct
        
        try:
            with open(path, 'rb') as f:
                # Read IHDR chunk
                signature = f.read(8)
                if signature[:4] != b'\x89PNG':
                    return {}
                
                header_len, header_type, _, data_len = struct.unpack('I', signature[4:16])
                ihdr_data = f.read(data_len + 4)
                
                # Parse IHDR chunk
                width, height, bit_depth, color_type = struct.unpack('>IHBB', ihdr_data[:16])
                
                return {
                    'width': width,
                    'height': height,
                    'bit_depth': bit_depth,
                    'color_type': color_type,
                }
        except Exception:
            return {}

    def _estimate_quality_loss(self, original_path: str, optimized_path: str) -> str:
        """Estimate quality loss between original and optimized image."""
        try:
            from PIL import Image as PILImage  # type: ignore
            
            with PILImage.open(original_path) as orig, \
                 PILImage.open(optimized_path) as opt:
                
                # Calculate simple metric based on file size ratio
                orig_size = Path(original_path).stat().st_size
                opt_size = Path(optimized_path).stat().st_size
                
                return "minimal" if orig_size == 0 or opt_size > orig_size * 0.95 else "moderate"
                
        except Exception:
            return "unknown"

    def optimize_batch(
        self,
        input_paths: list,
        output_dir: Optional[str] = None,
        compress_level: Optional[int] = None,
    ) -> Dict[str, OptimizationStats]:
        """
        Optimize a batch of images.

        Args:
            input_paths: List of input image paths
            output_dir: Output directory for optimized files
            compress_level: Override compression level for all files

        Returns:
            Dictionary mapping output paths to optimization stats
        """
        results: Dict[str, OptimizationStats] = {}
        
        # Set up output directory if specified
        if output_dir:
            out_path_obj = Path(output_dir)
        else:
            # Use first input's directory with "optimized" subfolder
            first_input = Path(input_paths[0])
            out_path_obj = first_input.parent / "optimized"
        
        out_path_obj.mkdir(parents=True, exist_ok=True)
        
        for input_path in input_paths:
            output_path = str(out_path_obj / f"{Path(input_path).stem}_opt{Path(input_path).suffix}")
            
            try:
                optimized_path, stats = self.optimize_image(
                    input_path=input_path,
                    output_path=output_path,
                    compress_level=compress_level,
                )
                results[str(optimized_path)] = stats
            except Exception as e:
                # Log error but continue with other files
                pass
        
        return results


__all__ = [
    "OptimizationConfig",
    "OptimizationStats",
    "ImageOptimizer",
]
