from typing import Dict, Optional

class ProgressService:
    def __init__(self):
        self.tasks: Dict[str, float] = {}
        self._current_task: Optional[str] = None

    def start_task(self, task_id: str, total: int):
        self.tasks[task_id] = 0.0
        self._current_task = task_id

    def update_progress(self, task_id: str, progress: float):
        if task_id in self.tasks:
            self.tasks[task_id] = min(progress, 1.0)

    def get_progress(self, task_id: str) -> float:
        return self.tasks.get(task_id, 0.0)

    def end_task(self, task_id: str):
        if task_id in self.tasks:
            del self.tasks[task_id]

progress_service = ProgressService()
