# Project Guidelines

## Plan Tracking

When working through steps in a PLAN.md, mark a step as done (✅) when the user explicitly agrees the step is complete and asks to commit the changes.

## Commit Messages

Follow this pattern: `[project-name] brief description (Step N)`

Example: `[claude-code-metrics] bootstrap script, main.tf provider/backend config, variables (Step 2)`

## Python Testing

When asserting mock calls, prefer a single `assert_called_once_with(...)` (or `assert_called_with(...)`) with the full expected payload over multiple individual field assertions.
