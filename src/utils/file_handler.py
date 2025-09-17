"""File handling utilities"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class FileHandler:
    """Centralized file operations handler"""

    @staticmethod
    def read_json(file_path: Path) -> Optional[Any]:
        """
        Read JSON file safely

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed JSON data or None if error
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            return None

    @staticmethod
    def write_json(data: Any, file_path: Path, indent: int = 2) -> bool:
        """
        Write data to JSON file

        Args:
            data: Data to write
            file_path: Output path
            indent: JSON indentation

        Returns:
            True if successful
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
            return True
        except Exception as e:
            return False

    @staticmethod
    def find_files(directory: Path, pattern: str) -> List[Path]:
        """
        Find files matching pattern

        Args:
            directory: Search directory
            pattern: Glob pattern

        Returns:
            List of matching file paths
        """
        if not directory.exists():
            return []
        return list(directory.glob(pattern))

    @staticmethod
    def get_recent_folders(base_dir: Path, limit: int = 5) -> List[Path]:
        """
        Get most recent date folders

        Args:
            base_dir: Base directory
            limit: Number of folders to return

        Returns:
            List of folder paths sorted by date
        """
        if not base_dir.exists():
            return []

        date_folders = [
            d for d in base_dir.iterdir()
            if d.is_dir() and d.name.isdigit() and len(d.name) == 8
        ]

        # Sort by folder name (date format YYYYMMDD)
        date_folders.sort(reverse=True)
        return date_folders[:limit]

    @staticmethod
    def ensure_directory(path: Path) -> Path:
        """
        Ensure directory exists

        Args:
            path: Directory path

        Returns:
            Path object
        """
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def read_text(file_path: Path) -> Optional[str]:
        """
        Read text file

        Args:
            file_path: Path to text file

        Returns:
            File contents or None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None

    @staticmethod
    def write_text(content: str, file_path: Path) -> bool:
        """
        Write text to file

        Args:
            content: Text content
            file_path: Output path

        Returns:
            True if successful
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False

    @staticmethod
    def get_file_stats(file_path: Path) -> Dict[str, Any]:
        """
        Get file statistics

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file stats
        """
        if not file_path.exists():
            return {}

        stat = file_path.stat()
        return {
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "is_file": file_path.is_file(),
            "is_dir": file_path.is_dir(),
            "extension": file_path.suffix if file_path.is_file() else None
        }