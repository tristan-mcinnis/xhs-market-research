"""Progress tracking utilities"""

from typing import Optional, Any
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.console import Console


class ProgressTracker:
    """Centralized progress tracking"""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.progress = None
        self.tasks = {}

    def __enter__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeRemainingColumn(),
            console=self.console
        )
        self.progress.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.progress:
            self.progress.__exit__(exc_type, exc_val, exc_tb)

    def add_task(self, description: str, total: int = 100, **kwargs) -> Any:
        """Add a new task to track"""
        if self.progress:
            task_id = self.progress.add_task(description, total=total, **kwargs)
            self.tasks[description] = task_id
            return task_id
        return None

    def update(self, task_id: Any = None, description: str = None, **kwargs):
        """Update task progress"""
        if self.progress:
            if description and description in self.tasks:
                task_id = self.tasks[description]
            if task_id is not None:
                self.progress.update(task_id, **kwargs)

    def complete(self, task_id: Any = None, description: str = None):
        """Mark task as complete"""
        if self.progress:
            if description and description in self.tasks:
                task_id = self.tasks[description]
            if task_id is not None:
                total = self.progress.tasks[task_id].total
                self.progress.update(task_id, completed=total)