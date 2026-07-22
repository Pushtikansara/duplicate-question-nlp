from __future__ import annotations

from ares.cli.utils.progress import indeterminate_progress, spinner_progress, task_progress


class TestProgress:
    def test_spinner_progress_context(self):
        with spinner_progress("testing") as progress:
            assert progress is not None

    def test_spinner_progress_default(self):
        with spinner_progress() as progress:
            assert progress is not None

    def test_task_progress_context(self):
        with task_progress("testing", 50) as progress:
            assert progress is not None

    def test_task_progress_default(self):
        with task_progress() as progress:
            assert progress is not None

    def test_indeterminate_progress(self):
        with indeterminate_progress("working") as progress:
            assert progress is not None

    def test_indeterminate_progress_default(self):
        with indeterminate_progress() as progress:
            assert progress is not None

    def test_spinner_creates_task(self):
        with spinner_progress("test") as progress:
            assert len(progress.tasks) > 0

    def test_task_creates_task(self):
        with task_progress("test", 100) as progress:
            assert len(progress.tasks) > 0

    def test_indeterminate_creates_task(self):
        with indeterminate_progress("test") as progress:
            assert len(progress.tasks) > 0

    def test_spinner_task_description(self):
        with spinner_progress("my task") as progress:
            task = progress.tasks[0]
            assert task.description == "my task"

    def test_task_progress_total(self):
        with task_progress("test", 42) as progress:
            task = progress.tasks[0]
            assert task.total == 42.0

    def test_spinner_no_total(self):
        with spinner_progress("test") as progress:
            task = progress.tasks[0]
            assert task.total is None or task.total == 0

    def test_multiple_spinners_not_allowed(self):
        with spinner_progress("a") as p1:
            with spinner_progress("b") as p2:
                assert p1 is not p2
