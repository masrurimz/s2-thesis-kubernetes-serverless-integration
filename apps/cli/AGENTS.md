# apps/cli — Unified CLI Entry Point

## What This Is

Unified Typer CLI that aggregates subcommands from all apps. Provides a single `thesis` command.

## Commands

```
thesis experiment run --phase full --runs 5 --duration 300
thesis experiment analyze --results-file path/to/results.csv
thesis experiment preflight
thesis routing daemon --scenario s4-hybrid-predictive
thesis prediction serve --port 8090
thesis prediction train --data synthetic
thesis version
```

## Architecture

Sub-apps are registered lazily — if a package isn't installed, its subcommands are silently skipped. This allows the CLI to work in partial deployments.

## Dependencies

- `shared` (config)
- typer, rich

## Entry Points

- `thesis` → `cli.main:app` (unified)
- Service-specific entry points remain for deployment:
  - `thesis-prediction-server` → `prediction.server:cli_app`
  - `thesis-routing-daemon` → `routing.daemon.cli:app`
  - `thesis-experiment` → `experiment.cli:app`
