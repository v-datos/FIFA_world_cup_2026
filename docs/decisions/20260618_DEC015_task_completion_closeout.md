# DEC015 - Adopt Task Completion Commit and Push Closeout

Date: 2026-06-18
Status: Accepted
Authority: User / Orchestrator

## Context

The project now uses explicit agent-owned tasks with handoffs, decisions,
status updates, and verification gates. The user asked the Orchestrator to make
sure documentation is current, then commit and push changes whenever a task is
done or finished.

## Decision

After every completed task, the Orchestrator closeout must:

1. Update the relevant documentation, including `TASKS.md`, `STATUS.md`, and
   `docs/phase_plan.md` when task state or routing changes.
2. Add or update decision and handoff records when the task changes architecture,
   contracts, workflow, or specialist ownership.
3. Run the appropriate verification gates for the changed surface.
4. Commit the completed task.
5. Push the commit to `origin/main`.

This is the default closeout unless the user explicitly asks not to commit or
push.

## Consequences

- Completed work should not remain uncommitted by default.
- Future Orchestrator responses should report the commit and push result.
- If verification cannot run or fails, the Orchestrator must report that and not
  present the task as fully closed.

## Verification

- Added this decision.
- Updated `AGENTS.md` workflow rules.
