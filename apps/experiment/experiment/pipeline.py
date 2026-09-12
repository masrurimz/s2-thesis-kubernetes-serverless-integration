"""Pipeline orchestrator: threads PipelineContext through ordered stages.

The pipeline is a thin coordinator (~80 lines) that chains composable
pipeline stages, fails fast on stage failure, and supports dry-run mode.
"""

from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console

import structlog
from shared.models.pipeline import PipelineContext, StageResult

from experiment.stages.base import Stage

logger = structlog.get_logger(__name__)


class Pipeline:
    """Threads PipelineContext through ordered stages.

    Usage:
        ctx = PipelineContext(batch_id="b1", scenario="s1-k8s-only", run_id=1, config=config)
        stages = [PlanStage(), PreflightStage(), ...]
        pipeline = Pipeline(stages, ctx)
        results = pipeline.run()
    """

    def __init__(self, stages: Sequence[Stage], ctx: PipelineContext):
        self.stages = stages
        self.ctx = ctx
        self.results: list[StageResult] = []

    def run(self) -> list[StageResult]:
        """Execute all stages sequentially. Fail fast on first failure."""
        self.results = []
        for stage in self.stages:
            logger.info("pipeline_stage_start", stage=stage.name)
            result = stage.execute(self.ctx)
            self.results.append(result)

            if not result.success:
                logger.error(
                    "pipeline_stage_failed",
                    stage=stage.name,
                    error=result.error,
                    duration=result.duration_sec,
                )
                break

            logger.info(
                "pipeline_stage_complete",
                stage=stage.name,
                duration=result.duration_sec,
            )
        return self.results

    def dry_run(self) -> list[StageResult]:
        """Simulate full pipeline without side effects."""
        self.results = []
        for stage in self.stages:
            result = stage.dry_run(self.ctx)
            self.results.append(result)
        return self.results

    @property
    def success(self) -> bool:
        """True if all stages completed successfully."""
        return all(r.success for r in self.results)

    @property
    def total_duration(self) -> float:
        """Total wall-clock duration of all stages."""
        return sum(r.duration_sec for r in self.results)

    def summary(self) -> str:
        """Human-readable summary of pipeline execution."""
        lines = [f"Pipeline: {len(self.results)}/{len(self.stages)} stages"]
        for r in self.results:
            status = "✅" if r.success else "❌"
            lines.append(f"  {status} {r.stage_name}: {r.duration_sec:.1f}s" + (f" ({r.error})" if r.error else ""))
        if not self.success:
            failed = [r.stage_name for r in self.results if not r.success]
            lines.append(f"Failed at: {', '.join(failed)}")
        else:
            lines.append(f"Total: {self.total_duration:.1f}s")
        return "\n".join(lines)

    def rich_summary(self, console: "Console") -> None:
        """Print a rich table summary of pipeline execution."""
        from rich.table import Table

        table = Table(title=f"Pipeline: {len(self.results)}/{len(self.stages)} stages", show_lines=False)
        table.add_column("Stage", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Duration", justify="right")
        table.add_column("Error")

        for r in self.results:
            status = "[green]✓[/green]" if r.success else "[red]✗[/red]"
            table.add_row(
                r.stage_name,
                status,
                f"{r.duration_sec:.1f}s",
                r.error or "",
            )

        if self.success:
            table.caption = f"Total: {self.total_duration:.1f}s"
        else:
            failed = [r.stage_name for r in self.results if not r.success]
            table.caption = f"[red]Failed at: {', '.join(failed)}[/red]"

        console.print(table)
