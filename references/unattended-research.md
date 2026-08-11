# Unattended research with Hermes cron

Use native Hermes cron plus file checkpoints. Do not create a daemon, supervisor, process registry, lock protocol, heartbeat, worker runner, outbox, or standalone CLI.

## Exact pattern

1. In the interactive parent session, create an absolute run directory and initialize it:

```bash
python3 /absolute/skill/dir/scripts/research_state.py \
  init "/absolute/run/dir" \
  --query "The full research question" \
  --mode deep \
  --axis "Axis one" \
  --axis "Axis two"
```

2. Put the mode planning ceilings, logical waves, and `next_actions` in `state.json`. Reserve at least 20% of the total planning budget for parent integration, source rechecks, conflict analysis, and synthesis. Use a bounded repeat count.
3. Create one recurring or fixed-repeat LLM cron job attached to the skill. In a live Hermes session, use the `cronjob` tool with this shape:

```text
action="create"
name="Deep research: <short topic>"
schedule="every 20m"
repeat=10
deliver="origin"
skills=["hermes-deep-research"]
attach_to_session=true
enabled_toolsets=["web", "file", "terminal"]
prompt="<self-contained tick prompt containing the absolute run directory>"
```

The repeat count and interval are planning choices, not protocol fields. A cron tick is a runtime work unit, not a logical wave; multiple ticks may advance one wave. Size each tick so it can finish one research, review, integration, or synthesis step comfortably. The reserved final ticks must synthesize a terminal `completed` or `partial` report rather than leave useful findings nonterminal.

Cron completes research and synthesis only. If the user explicitly requested a final report document or PDF, the interactive parent applies the two-stage documentation workflow in SKILL.md after the terminal report returns; do not attach, copy, or invoke Bookforge from the cron tick.

4. Use a self-contained prompt like this:

```text
Continue the attached hermes-deep-research run at /absolute/run/dir.
Read SKILL.md, references/unattended-research.md, state.json, sources.json,
and existing notes before acting. If state was terminal at tick start, emit
only [SILENT]. Otherwise perform exactly one bounded next action using normal
web and file tools: research one pending coverage lane, review/integrate one saved note,
resolve one material contradiction, or synthesize/recover the report. Open
original pages for evidence and update sources.json. Write the note or report
artifact before atomically checkpointing state.json. Record the completed step
in waves and choose concrete next_actions.

If an interrupted prior tick left no saved note or artifact, narrow and redo that action;
do not claim the interrupted attempt resumed. If a useful report can be
finished and required breadth has converged, write report.md and set status to
completed. If the budget or maximum wave is reached without convergence, write
the useful report and set status to partial rather than failed.
Validate the run. Emit only [SILENT] while nonterminal. On the tick that first
makes the report terminal, return the report contents as the final response so
cron delivers it to origin. Never create, edit, pause, resume, or remove cron
jobs from inside the tick.
```

Do not rely on relative paths or conversation memory in the tick prompt. Name the run directory and intended research question explicitly.

Unattended ticks do the bounded work directly with their attached web and file tools. Do not launch background `delegate_task` children from a cron tick: the cron session must durably write its own artifact and checkpoint before it ends.

## Checkpoint cadence

Checkpoint:

- before dispatching or starting a bounded action;
- after a note or source-ledger update is durably written;
- after integrating each note;
- before synthesis;
- after writing and validating the terminal report.

Keep the pending action unchanged until its artifact exists. If a restart occurs between the artifact write and state integration, the next tick should integrate the saved artifact rather than repeat the search.

## Restart semantics

Gateway and cron persistence cause a later tick to continue from files after restart. They do not resume the interrupted model or tool call. Work without a saved note or artifact is lost and must be redone. A saved artifact is recoverable even if the corresponding state update was interrupted.

`attach_to_session=true` makes the origin delivery continuable for user follow-up. It is not the persistence mechanism. `deliver="origin"` routes the first terminal report back to the originating conversation.

Every nonterminal tick must return exactly `[SILENT]`. If the state is already terminal when a later scheduled tick starts, it must also return `[SILENT]` to avoid duplicate report delivery.

## No self-scheduling

Cron cannot mutate itself. A tick must never create, extend, edit, pause, resume, or delete its job. The interactive parent chooses the bounded repeat count up front. If the run ends `partial`, the user or parent may explicitly schedule a new bounded continuation later.

Persistent Goals may help same-session iteration when the user invokes `/goal`, but they do not replace state files or cron for restart-resilient unattended work.
