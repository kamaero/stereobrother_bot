"""
Minimal audio utilities for testing purposes.
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple


class AudioUtils:
    """Minimal audio utilities for testing."""

    @staticmethod
    def get_audio_info(file_path: str) -> Dict:
        """Get basic audio file information."""
        path = Path(file_path)

        if not path.exists():
            return {"error": f"File not found: {file_path}", "exists": False}

        # Return mock audio info for testing
        return {
            "file_path": str(path),
            "file_size": path.stat().st_size,
            "duration_seconds": 180.5,  # Mock duration
            "sample_rate": 44100,  # Mock sample rate
            "channels": 2,  # Mock channels
            "bit_depth": 16,  # Mock bit depth
            "bitrate": 320,  # Mock bitrate in kbps
            "format": path.suffix.lower().lstrip("."),
            "exists": True,
        }

    @staticmethod
    def load_audio_file(file_path: str) -> Tuple[bool, str]:
        """Load audio file (mock implementation)."""
        path = Path(file_path)

        if not path.exists():
            return False, f"File not found: {file_path}"

        # Check file extension
        valid_extensions = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"}
        if path.suffix.lower() not in valid_extensions:
            return False, f"Unsupported audio format: {path.suffix}"

        # Check file size (max 100MB)
        max_size = 100 * 1024 * 1024  # 100MB
        if path.stat().st_size > max_size:
            return (
                False,
                f"File too large: {path.stat().st_size} bytes (max: {max_size})",
            )

        return True, "Audio loaded successfully"

    @staticmethod
    def save_audio_file(audio_data: Dict, output_path: str) -> bool:
        """Save audio file (mock implementation)."""
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            # Create a dummy file for testing
            with open(output_path, "wb") as f:
                f.write(b"Mock audio data")

            return True
        except Exception:
            return False

    @staticmethod
    def convert_audio_format(
        input_path: str,
        output_path: str,
        output_format: str = "mp3",
        sample_rate: Optional[int] = None,
        bitrate: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """Convert audio format (mock implementation)."""
        input_path_obj = Path(input_path)

        if not input_path_obj.exists():
            return False, f"Input file not found: {input_path}"

        # Validate output format
        valid_formats = {"mp3", "wav", "flac", "ogg"}
        if output_format.lower() not in valid_formats:
            return False, f"Unsupported output format: {output_format}"

        # Create output directory if needed
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        # Mock conversion by copying the file (or creating dummy)
        try:
            with open(output_path, "wb") as f:
                f.write(b"Converted audio data")
            return True, f"Converted to {output_format}"
        except Exception as e:
            return False, f"Conversion failed: {e}"

    @staticmethod
    def normalize_audio(
        input_path: str, output_path: str, target_level: float = -1.0
    ) -> Tuple[bool, str]:
        """Normalize audio level (mock implementation)."""
        if not Path(input_path).exists():
            return False, f"Input file not found: {input_path}"

        try:
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)

            # Create normalized file
            with open(output_path, "wb") as f:
                f.write(b"Normalized audio data")

            return True, f"Normalized to {target_level} dB"
        except Exception as e:
            return False, f"Normalization failed: {e}"

    @staticmethod
    def trim_audio(
        input_path: str,
        output_path: str,
        start_time: float = 0.0,
        end_time: Optional[float] = None,
    ) -> Tuple[bool, str]:
        """Trim audio (mock implementation)."""
        if not Path(input_path).exists():
            return False, f"Input file not found: {input_path}"

        try:
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)

            # Create trimmed file
            with open(output_path, "wb") as f:
                f.write(b"Trimmed audio data")

            duration = f"{start_time}-{end_time if end_time else 'end'}"
            return True, f"Trimmed to {duration} seconds"
        except Exception as e:
            return False, f"Trimming failed: {e}"

    @staticmethod
    def merge_audio_files(input_paths: list, output_path: str) -> Tuple[bool, str]:
        """Merge audio files (mock implementation)."""
        # Check all input files exist
        for input_path in input_paths:
            if not Path(input_path).exists():
                return False, f"Input file not found: {input_path}"

        try:
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)

            # Create merged file
            with open(output_path, "wb") as f:
                f.write(b"Merged audio data")

            return True, f"Merged {len(input_paths)} files"
        except Exception as e:
            return False, f"Merging failed: {e}"

    @staticmethod
    def create_temp_audio_file(
        content: bytes = b"temp_audio", suffix: str = ".wav"
    ) -> str:
        """Create a temporary audio file for testing."""
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_file.write(content)
            return temp_file.name

    @staticmethod
    def cleanup_temp_file(file_path: str) -> bool:
        """Clean up a temporary file."""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
            return True
        except Exception:
            return False


# Create a default instance for convenience
default_audio_utils = AudioUtils()
