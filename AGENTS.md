# AGENTS.md

Agent instructions for this repository. For project overview and research context, see [CLAUDE.md](./CLAUDE.md).

## Issue Tracking

This project uses **bd (beads)** for issue tracking.
Run `bd prime` for workflow context, or install hooks (`bd hooks install`) for auto-injection.

**Quick reference:**
- `bd ready` - Find unblocked work
- `bd create "Title" --type task --priority 2` - Create issue
- `bd close <id>` - Complete work
- `bd sync` - Sync with git (run at session end)

For full workflow details: `bd prime`

---

## 🧠 LLM Workflow Standards

### 🔑 Core Principles

- **NO HIGH-LEVEL BULLSHIT** – Show real code, not vague suggestions.
- **Terse, expert-level, casual communication** – Get to the point.
- **Anticipate needs** – Offer solutions they haven't asked for yet.
- **LLM-AWARE DEVELOPMENT** – Use burst implementation + validation cycles, not human time estimates.

---

### 📋 Task Management

- Use `bd` for multi-session work with complex dependencies.
- Use `TodoWrite` / `TodoRead` for single-session linear tasks.
- Break tasks into concrete, actionable items.
- **LLM Planning**: Estimate in "execution blocks" (15-30 min) not hours/days.
- **Context Batching**: Group related tasks by domain/component for parallel execution.

---

### 🔍 Search & Analysis

- Use `Task` tool for multi-round open-ended investigation.
- **Batch** search operations (esp. Bash) to minimize latency.
- Prefer `rg` (ripgrep) over `grep`, `fd` over `find`, etc.
- Read and diff multiple files at once where analysis demands it.

---

### 🧬 Code Changes

- Match existing code patterns – review similar files before adding new logic.
- Add comments only where the logic isn't self-evident.
- Don't touch unrelated files – surgical edits only.

---

### 🗃️ Git Workflow

- Commit at _logical checkpoints_ with clear commit messages.
- Format commit messages: `feat:`, `fix:`, `refactor:`, `chore:`, etc. + short summary
- Do **not** squash – user will squash and rename commits later.
- Never push unless explicitly instructed.
- Don't run deployment scripts unless told to.

---

### 📁 File Ops

- CREATE markdown files to document implemented logic.
- ALWAYS edit existing files if possible.
- NEVER delete MongoDB data without explicit confirmation.

---

### 🛠️ Tool Usage

- Batch all independent operations into single calls.
- Use absolute paths.
- Parallelize wherever possible: `&` in Bash, `xargs -P`, background jobs.
- Use optimized tools (`rg`, `fd`, etc.) over slower legacy ones.
- **LLM Optimization**: Create 5-10 related files simultaneously in burst implementation.
- **Validation Cycles**: Plan explicit human testing phases between implementation bursts.

---

### 💬 Response Style

- Lead with the solution. Explain later, only if necessary.
- Show only relevant code (a few lines before/after).
- Reference files with format: `path/to/file.ts:42`
- Split large responses cleanly.
- No fluff. No filler.

---

### 🚫 What NOT to Do

- ❌ Don't update Git config
- ❌ Don't push to remote unless told to
- ❌ Don't deploy unless told to
- ❌ Don't touch unrelated DB entries
- ❌ Don't use human time estimates (hours/days) for LLM-capable tasks
- ❌ Don't plan sequential tasks that can be executed in parallel batches

---

## 🚀 LLM Development Guidelines

### Core LLM Approach

- **Execution Blocks**: 15-30 minute focused implementation bursts
- **Context Batching**: Group related tasks (configs, docs, scripts) together
- **Burst + Validate**: Implementation → Human Testing → Feedback → Next Burst
- **Parallel Creation**: Generate 5-10 related files simultaneously

### LLM Strengths (Leverage)

- Configuration generation (YAML, JSON, configs)
- Pattern-based implementation following existing conventions
- Documentation created simultaneously with code
- Parallel execution of related tasks

### LLM Limitations (Account For)

- Complex multi-system debugging requires human feedback
- Integration validation needs real-world testing
- Performance optimization requires iterative measurement
- Domain expertise and business logic validation

### Estimation Framework

- **Simple**: 1 execution block (single component, docs, scripts)
- **Medium**: 2-3 execution blocks (multi-component integration)
- **Complex**: Multiple burst + validation cycles (system-wide changes)

Always plan with LLM reality: Sprint 1 = 1 day actual (not 5 days traditional)

---

## 🤝 User-LLM Validation Collaboration

### Role Separation

**LLM Role**:
- Code validation, syntax checking, import testing
- Analysis of user feedback and error messages
- Configuration generation and pattern implementation
- Documentation updates and logic verification

**User Role**:
- Execute long-running services (servers, monitoring, prediction engines)
- Integration testing and performance measurement
- Manual verification of system behavior
- Resource management and process monitoring

### Handoff Protocol

**Phase 1 (LLM Implementation)**:
- LLM provides specific commands for user execution
- Clear step-by-step instructions with expected outputs
- Error handling guidance and troubleshooting steps

**Phase 2 (User Execution)**:
- User executes services and reports results
- Captures logs, error messages, and performance metrics
- Tests integration points and validates behavior

**Phase 3 (Collaborative Analysis)**:
- User reports findings back to LLM with specific details
- LLM analyzes feedback and provides next steps
- Iterative refinement based on real-world testing

---

## 📦 UV Package Management Usage

### Core UV Commands

```bash
# Project setup and dependency management
uv sync                    # Install dependencies from pyproject.toml
uv lock                    # Update dependency lock file
uv add package-name        # Add new dependency
uv remove package-name     # Remove dependency

# Script execution patterns
uv run script.py                    # Run Python script
uv run -m module.name              # Run module directly
uv run prediction-server           # Run defined script from pyproject.toml
```

### Common Patterns

- **Development**: `uv run` for all script execution
- **Testing**: `uv run -m pytest` or `uv run test-script`
- **Services**: Use project scripts for long-running services
- **Environment**: `uv sync` before each development session

---

## 🔄 Subagent Context Management

### When to Use Subagents

- **Large File Updates**: Multi-file documentation, extensive refactoring
- **Extensive Research**: Multi-round system architecture analysis
- **Context-Heavy Tasks**: When main conversation context approaches limits

### Delegation Patterns

```
Research Subagents → Summary report for main conversation
Implementation Subagents → Ready-to-execute implementation plan
Analysis Subagents → Specific optimization recommendations
```

---

## ✅ Sprint Validation Workflow

### Validation Phase Structure

**Phase 1: Code Validation (LLM)**
```bash
uv run -m intelligent_router.prediction_engine  # Import test
uv run -m pytest tests/test_prediction.py       # Unit tests
```

**Phase 2: Service Execution (User)**
```bash
uv run prediction-server --port 8000 &
uv run routing-controller --interval 30 &
```

**Phase 3: Performance Analysis (Collaborative)**
```bash
curl http://localhost:9090/api/v1/query?query=prediction_accuracy
kubectl top pods
docker stats
```

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
