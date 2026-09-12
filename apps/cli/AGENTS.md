# apps/cli

Unified Typer entry point. Registers every sub-app under one `thesis` command; owns registration only, no business logic.

## Module map

| Path | Responsibility |
|---|---|
| `cli/main.py` | `app = typer.Typer(name="thesis")`, the no-argument home callback, the `version` command, and the six `_register_*` functions that lazily add every sub-app |
| `cli/home.py` | `print_home()`: the state view `thesis` prints with no arguments: cluster state, predictor health, latest bundle and verdict, next commands. Bounded and guarded; every failure degrades to a line of text, never a traceback or hang |

## Module direction

- **May import:** every workspace package, but only lazily inside a `_register_*` function's `try` block (plus `typer` at module level; `rich` and `cli.home` import lazily inside their commands). This is the top of the importlinter layer contract; nothing else may import `cli`.
- **Must never import:** nothing is above it to forbid. The structural rule instead: no business logic and no eager app imports in this package. A missing optional package must degrade to a silently skipped sub-app, never an import error.
- **Where new code goes:**
  - New sub-app from another package → a `_register_<name>()` function following the existing pattern, called in the registration block at the bottom of `main.py`. The commands themselves belong in the owning package (the prediction `serve`/`train` commands defined inline in `_register_prediction` are the exception, not the pattern to copy).

## Tests

`apps/cli/tests/`; hermetic, no live tier. `test_home.py` pins the home view's degrade-to-a-line contract; `test_docs_commands.py` is a documentation drift guard that resolves every `uv run thesis ...` invocation written in the repo's markdown against the real CLI. Run with:

```bash
uv run python -m pytest apps/cli/tests -q
```

## Commands it contributes

`thesis` (root command) plus the six registered sub-apps, verified against `thesis --help`:

| Sub-app | Source |
|---|---|
| `experiment` | `experiment.cli:app` |
| `routing` | `routing.daemon.cli:app` |
| `prediction` | defined inline in `main.py::_register_prediction` (`serve`, `train`) |
| `infra` | `infra.cli:app` (from `libs/infra`, not an apps/ package) |
| `dashboard` | `dashboard.cli:app` |
| `analysis` | `analysis_cli.cli:app` |

Plus the builtin `version` command. With no arguments, `thesis` prints the home view (`cli/home.py`): cluster state, predictor health, the latest bundle's verdict, and the next commands to run.


```bash
uv run thesis --help
uv run thesis version
```

## Entry points

- `thesis` → `cli.main:app` (unified)
- Service-specific entry points stay for deployment: `thesis-prediction-server` (`prediction.server:cli_app`), `thesis-routing-daemon` (`routing.daemon.cli:app`), `thesis-experiment` (`experiment.cli:app`)

## Invariants

- Registration is lazy: each `_register_*` wraps its import in `try/except ImportError: pass`, so the CLI works in partial deployments. Keep that shape for every new sub-app.
- `typer` is the only module-level import in `main.py`; `rich` and `cli.home` arrive lazily inside their commands. Keep it that way: the unified CLI must import fast and survive a missing optional package.
- Every `uv run thesis ...` invocation written in repo markdown must resolve against the real CLI; `apps/cli/tests/test_docs_commands.py` fails when one drifts. Write only commands that exist.
