"""Base stage protocol and abstract class for composable pipeline stages.

Every pipeline stage inherits from BaseStage and implements _run().
The base class handles timing, error handling, and dry-run support.
"""

from abc import ABC
from typing import Protocol, runtime_checkable

from shared.models.pipeline import PipelineContext, StageResult


@runtime_checkable
class Stage(Protocol):
    """Protocol for a composable experiment pipeline stage."""

    name: str

    def execute(self, ctx: PipelineContext) -> StageResult: ...

    def dry_run(self, ctx: PipelineContext) -> StageResult: ...


class BaseStage(ABC):
    """Abstract base class with common stage functionality.

    Subclasses implement _run(ctx) with the actual stage logic.
    The base class wraps it with timing, error handling, and dry-run support.
    """

    name: str = "base"

    def execute(self, ctx: PipelineContext) -> StageResult:
        import time

        t0 = time.time()
        try:
            self._run(ctx)
            return StageResult(
                stage_name=self.name,
                success=True,
                duration_sec=time.time() - t0,
            )
        except Exception as e:
            return StageResult(
                stage_name=self.name,
                success=False,
                duration_sec=time.time() - t0,
                error=str(e),
            )

    def dry_run(self, ctx: PipelineContext) -> StageResult:
        return StageResult(stage_name=self.name, success=True, duration_sec=0.0)

    def _run(self, ctx: PipelineContext) -> None:
        raise NotImplementedError
