---
name: manage-project-backlog
description: Manage Markdown/YAML backlog tasks in this repository. Use when creating, splitting, prioritizing, scheduling, updating, reviewing, closing, reporting, or preparing commits for backlog tasks; when identifying the next eligible task, blockers, dependencies, readiness gates, or parallel work; and when answering project-status questions from files under backlog/.
---

# Manage Project Backlog

Manage repository backlog files consistently while keeping Markdown/YAML as the source of truth. Do not require a project-management script or Odoo unless the user explicitly requests them.

## Load context

1. Read `backlog/README.md` before creating or changing metadata.
2. Read each target backlog completely.
3. Read referenced parent, predecessor and readiness tasks before deciding order, eligibility or completion.
4. Read `backlog/13_08_2026/backlog_56_odoo_project_gantt_progress_reporting.md` when applying its scheduling, dependency, parallelism or readiness rules.
5. Inspect Git diff/status before editing or preparing a commit. Preserve unrelated user changes.

## Treat metadata as canonical

- Keep YAML front matter and Markdown body in one backlog file.
- Do not add `owner`.
- Do not maintain manually edited JSON as a second source of truth.
- Update `updated_at` whenever metadata or scope changes.
- Preserve existing IDs and filenames unless the user explicitly requests a rename.
- Use parent initiatives for grouping; do not report a parent and its children as duplicate executable work.

## Apply dependency rules

- Allow at most one active predecessor for each executable task.
- Treat dependency and readiness as stronger constraints than `priority_rank`.
- Use `priority_rank` only to order tasks that are otherwise eligible.
- Do not infer dependency from rank, workstream, assignee, technology, repository, or shared resources.
- Create a dependency only when the successor requires an artifact, decision, environment, data, schema, API, or accepted result from the predecessor.
- Use a readiness checklist when a task needs outputs from multiple independent tasks; do not create a fake dependency chain.
- Allow one predecessor to have multiple successors.
- Detect direct and indirect dependency before classifying tasks as parallel.
- Classify tasks as parallel candidates only when no dependency path connects them and neither consumes the unfinished output of the other.
- Treat resource conflicts as scheduling warnings, not business dependencies.

When structured scheduling metadata exists, support `FS`, `SS`, `FF`, `SF`, lag, and working-day units according to the target backlog. When legacy `dependencies` arrays exist, report incompatibilities with the one-predecessor rule instead of silently rewriting historical metadata.

## Select the next task

When asked for the next task:

1. Exclude `done`, `dropped`, blocked tasks, and parent initiatives without an independently executable deliverable.
2. Exclude tasks whose predecessor is not done.
3. Exclude tasks whose required readiness items are incomplete.
4. Prefer `ready`, then eligible `backlog` tasks.
5. Sort by priority `P0` through `P3`, then ascending `priority_rank`.
6. Return one primary task and list independent parallel candidates separately.
7. Cite the predecessor, readiness and priority evidence used.

Do not claim a task is executable merely because it has the smallest rank.

## Update status and progress

- Set `ready` only when predecessor and readiness conditions are satisfied.
- Set `in_progress` only when implementation has actually started.
- Set `blocked` only for a concrete impediment and record the reason in the backlog body or supported metadata.
- Set `done` only when progress is 100, acceptance criteria are met, and relevant tests or other evidence have been verified.
- Keep progress between 0 and 100 and consistent with status.
- Do not modify production implementation while performing a backlog-only request.

## Create or split backlog

- Assign a unique ID and an unambiguous title.
- Keep each child focused on one testable deliverable.
- Include objective, scope, exclusions, acceptance criteria, and expected outcome.
- Put implementation-specific tests in the implementing child task instead of deferring all tests to a final task.
- Give each child at most one direct predecessor.
- Split independent branches after their shared contract or foundation stabilizes.
- Mark parallel branches with `execution_mode` and `parallel_with`.
- Use the same `priority_rank` for tasks intentionally starting in the same execution wave when needed.
- Add a final readiness checkpoint only for integration, release evidence and runbook work.

## Review task closure

Verify all applicable evidence:

- Acceptance criteria map to concrete implementation or documentation.
- Relevant tests pass and their scope is sufficient.
- Configuration/runtime checks succeed when applicable.
- No required readiness item remains open.
- No unresolved blocker contradicts completion.
- Git diff and commits support the claimed scope.

Report missing evidence explicitly. Do not implement a production business-logic fix unless separately authorized.

## Prepare backlog commits

1. Identify backlog files that are actually complete or explicitly requested.
2. Inspect their diff and related evidence.
3. State the exact files and scope before committing.
4. Exclude unrelated working-tree changes.
5. Commit only after an explicit user request.
6. Report the resulting commit hash and any remaining uncommitted backlog changes.

## Report results

Lead with the selected task, status conclusion, or files changed. Explain dependency and readiness decisions briefly. Link repository files with absolute paths when handing work back in Codex.
