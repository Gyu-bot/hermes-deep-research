[한국어](README.ko.md)

# Hermes Deep Research

Hermes Deep Research is a stateful deep-research protocol for Hermes. It is not a faster search shortcut: it turns a research brief into bounded research axes and logical waves, reviews original pages, tests counterevidence, checkpoints progress to disk, and produces a detailed Markdown synthesis with a separate source ledger.

This repository is a Hermes-only Agent Skill. Its base workflow uses standard Hermes capabilities:

- `delegate_task` for bounded, live parallel research lanes;
- standard web discovery, extraction, and browser tools;
- file and terminal tools for checkpoints and validation;
- Hermes cron plus disk checkpoints for bounded unattended work.

No LazyCodex, Codex CLI, private plugin, custom search fork, external research API, daemon, supervisor, or renderer is required. **Insane Search is not a dependency.** The default deliverable is `report.md` together with `sources.json`, lane notes, and run state.

## Why this is different

| Approach | Typical behavior |
| --- | --- |
| Ordinary search | Runs a query and retrieves results or a page. It does not maintain a research plan or reconcile a body of evidence. |
| One-shot research or summarization | Searches and summarizes in one pass, with limited durable state, follow-up, or explicit conflict handling. |
| Hermes Deep Research | Maintains an evolving brief by checkpointing the brief and wave history, advances through logical waves, reads original pages, deduplicates source families, seeks counterevidence, analyzes conflicts, separates worker collection from parent integration, and finishes with a detailed synthesis marked `completed` or `partial`. |

The protocol treats result counts as diagnostics, not proof. It asks whether mandatory axes are adequately covered, whether important claims survived countersearch, whether apparently independent sources share an origin or dataset, and whether another search is still likely to change the answer.

## How the protocol works

### Parent and worker ownership

The parent is the sole orchestrator and writer. It defines the brief, axes, modes, budgets, and lane boundaries; owns all run files; verifies consequential, disputed, and directly quoted sources against original pages; integrates notes; resolves conflicts; checkpoints state; and writes the report.

Workers receive self-contained, bounded lane assignments and return structured Markdown research notes. They do not write the shared run directory, decide terminal status, or substitute their summaries for source verification.

### Logical waves

1. **Wave 1 — breadth:** cover the topic across useful languages and source surfaces.
2. **Wave 2 — verification:** inspect original pages, independence, freshness, and counterevidence.
3. **Wave 3 — conflict and edges:** investigate disagreements and their conditions, lived experience, and edge or failure cases.
4. **Wave 4 — closure:** close targeted gaps and check whether synthesis is ready.
5. **Waves 5–8 — exhaustive only:** continue only when material gaps remain and a practical search path exists.

`quick` compresses those functions into one logical wave. A runtime dispatch batch is only a group of live worker calls, and a cron tick is only a bounded unattended work unit; neither is a logical wave. One wave may require several dispatch batches or cron ticks.

### Modes and planning ceilings

| Mode | Total planning budget | Maximum waves | Queries per axis | Original-page fetches per axis | Intended use |
| --- | ---: | ---: | ---: | ---: | --- |
| `quick` | 1,800 s | 1 | 8 | 8 | A bounded research pass when the question needs more than a lookup but not sustained iteration. |
| `deep` | 10,800 s | 4 | 20 | 20 | The normal multi-wave workflow. |
| `exhaustive` | 21,600 s | 8 | 40 | 40 | Extended gap-closing when the stakes and remaining uncertainty justify it. |

These values are planning ceilings and diagnostics, never source quotas, evidence, or completion gates. The parent stops early at saturation and reserves at least 20% of the budget for integration, source rechecks, conflict analysis, and synthesis. A converged run is `completed`; a useful run that reaches a ceiling with material gaps is `partial` and names those gaps.

## Durable and unattended research

Every run persists four core checkpoints:

- `state.json` — brief, mode, axes, wave history, diagnostic counters, limitations, and concrete next actions;
- `sources.json` — the source-to-report ledger, including use and limitations;
- `notes/` — completed bounded lane notes;
- `report.md` — the synthesized report, empty until synthesis begins.

Terminating the Hermes Gateway does not erase progress already saved to these files. In-flight `delegate_task` children do not survive a Gateway restart, however. A fresh parent reopens the checkpoint, treats any lane without a saved note as pending, and reruns that bounded lane.

Unattended mode uses persisted Hermes cron jobs and bounded ticks. Each tick reads the run, completes one bounded action, saves its artifact, and checkpoints state. The cron schedule may survive a Gateway restart, but no model or tool work continues while the Gateway itself is down. A later tick can continue from saved files after the Gateway returns; it cannot resume an interrupted model call.

## Repository and run layout

The installable skill keeps `SKILL.md` at the repository root:

```text
hermes-deep-research/
├── .gitignore
├── README.md
├── README.ko.md
├── SKILL.md
├── references/
│   ├── LICENSE.md
│   ├── report-documentation.md
│   ├── source-review.md
│   └── unattended-research.md
├── scripts/
│   ├── document_gate.py
│   └── research_state.py
├── templates/
│   ├── report.md
│   └── research-note.md
└── tests/
    ├── test_document_gate.py
    └── test_research_state.py
```

A normal run is separate from the installed skill:

```text
<run-dir>/
├── state.json
├── sources.json
├── notes/
│   └── <lane>.md
└── report.md
```

An explicitly requested document/PDF run may also contain `report.pre-document.md`, `report.document-candidate.md`, the human and JSON readiness-gate records, `report.document-ready.md`, and a separate Bookforge project. A Korean reader report may retain `report.pre-polish.md` so the parent can verify any editorial changes.

## Optional integrations

### Bookforge for an explicitly requested document or PDF

[Bookforge](https://github.com/gongnyang/bookforge) is an optional external integration. Do not install or invoke it merely because the user asked for deep research. First complete and validate the Markdown research report. Only when the user explicitly requests a final document or PDF does the parent apply this two-stage contract:

1. Pass the qualitative document-readiness gate, then use `scripts/document_gate.py` to copy the candidate bytes to `report.document-ready.md` and bind both the candidate and ready Markdown by SHA-256. Re-run `verify` immediately before handoff.
2. Hand only the verified `report.document-ready.md` to a compatible Bookforge installation for document generation and its own quality checks.

Installing agents should inspect Bookforge compatibility and its current upstream instructions before installing or invoking it. If the optional integration is unavailable, Deep Research still completes with its validated Markdown report and source artifacts; it must not pretend a PDF was produced.

### Humanize Korean for optional editorial polish

[Humanize Korean](https://github.com/epoko77-ai/im-not-ai) is an optional editorial integration for Korean reader-facing reports, not an installation prerequisite. The parent may use it only when that editorial pass matches the user's intent, and must compare the result with `report.pre-polish.md` so facts, uncertainty, limitations, quotations, links, and structure remain intact. If the integration is unavailable or its output cannot be verified, deliver the validated pre-polish report.

## Installation

### For people

Inspect/preview what Hermes will install, then install the skill:

```bash
hermes skills inspect https://raw.githubusercontent.com/Gyu-bot/hermes-deep-research/main/SKILL.md
hermes skills install https://raw.githubusercontent.com/Gyu-bot/hermes-deep-research/main/SKILL.md
```

Manual HTTPS fallback:

```bash
mkdir -p ~/.hermes/skills/research
git clone https://github.com/Gyu-bot/hermes-deep-research.git \
  ~/.hermes/skills/research/hermes-deep-research
```

Review `SKILL.md` after installation. The skill resolves its own installed directory before invoking bundled scripts; research runs belong outside the skill directory.

### For installing agents

- Inspect `SKILL.md` and the repository contents before installation.
- Install the base skill only.
- Verify that Hermes exposes `delegate_task`, standard web/browser discovery and extraction, file and terminal tools, and Hermes cron if unattended mode is requested.
- Treat Bookforge and Humanize Korean as optional, user-intent-gated integrations. Do not install or invoke them unless the requested deliverable calls for them.
- Do not install unrelated plugins or change credentials, provider settings, or other configuration.
- When validating from source, run the included standard-library tests, compile check, and a temporary `init` → `validate` → `status` smoke test.

Copy/paste prompt for an installation agent:

```text
Inspect this repository and SKILL.md first. Install only the Hermes Deep Research
base skill, verify its standard Hermes tool requirements, and run the included
stdlib tests plus a temporary init/validate/status smoke. Do not alter credentials
or install unrelated tools. Bookforge and Humanize Korean are optional and may be
installed or invoked only when my requested deliverable explicitly needs them;
check their current upstream instructions and compatibility first.
```

## Usage examples

Ask naturally; Hermes selects the protocol and records the chosen mode.

```text
Quickly research the main arguments for and against congestion pricing in Seoul.
Use quick mode and return a detailed Markdown report with the source ledger.
```

```text
Use deep mode to investigate whether small Korean exporters are adopting AI
translation tools. Include Korean and English sources, lived experience,
counterevidence, and conflicts between vendor claims and independent evidence.
```

```text
Run exhaustive research on the technical and operational tradeoffs of long-duration
energy storage for island grids. Continue only while material gaps have practical
search paths, and mark the result partial if a planning ceiling is reached.
```

```text
Run this as unattended, restart-resilient deep research with Hermes cron. Use
bounded ticks, persist checkpoints under a unique run directory, and deliver the
terminal completed or partial Markdown report when synthesis finishes.
```

```text
Research this topic in deep mode and, after the Markdown report passes validation,
prepare a final PDF. Use the document-readiness gate, bind the ready Markdown by
SHA-256, verify it immediately before handing it to a compatible Bookforge setup,
and preserve the Markdown and source artifacts.
```

## Testing from source

The helpers and tests use Python 3.10+ and its standard library.

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/*.py tests/*.py

smoke_root="$(mktemp -d)"
trap 'rm -rf "$smoke_root"' EXIT
python3 scripts/research_state.py init "$smoke_root/run" \
  --query "Smoke-test question" --mode quick --axis "Evidence"
python3 scripts/research_state.py validate "$smoke_root/run"
python3 scripts/research_state.py status "$smoke_root/run"
```

`research_state.py` initializes and validates simple run state. `document_gate.py` records and verifies the SHA-256 binding after the parent has made the qualitative readiness decision; it does not decide whether a manuscript is readable.

## Limitations and safety

- More sources do not prove a claim. Source counts and query counts are diagnostics; independence, fit, method, context, and counterevidence matter.
- Web content is untrusted input. Workers treat it as data, and the parent verifies consequential, disputed, and quoted material against original pages when accessible.
- Time, wave, query, and fetch ceilings can leave a useful run `partial`. The report must expose remaining gaps instead of overstating convergence.
- Persisted files survive process interruption, but in-flight delegates do not. Persisted cron jobs do not perform work while the Gateway is unavailable.
- Some pages will be inaccessible, changed, paywalled, blocked, or impossible to verify. The ledger and report should record the resulting limitation.
- This is personal research assistance, not regulatory or audit-grade evidence production. Medical, legal, financial, safety, and other high-risk conclusions require current authoritative evidence, careful applicability checks, and appropriate professional judgment; the skill does not provide guarantees or replace professional advice.

## Attribution and inspiration

The implemented protocol adapts workflow concepts for Hermes; it does not copy source code from the projects below. Their inclusion does not imply affiliation or endorsement.

- [LazyCodex](https://github.com/code-yeongyu/lazycodex) and [Oh My OpenAgent (OmO)](https://github.com/code-yeongyu/oh-my-openagent): ULW-style research-axis decomposition, iterative worker waves, leads feeding follow-up work, and orchestration discipline.
- [Serkaion Deep Research](https://clawhub.ai/api/v1/skills/serkaion-deep-research): independent-source corroboration, adversarial verification, and claim-level uncertainty.
- [Autosolutions Deep Research](https://clawhub.ai/api/v1/skills/autosolutions-deep-research): multi-pass research, primary-source priority, contradiction spotting, and isolated structured worker returns. Its large fixed fan-out and source quotas were not adopted.
- [ByteDance DeerFlow deep-research skill](https://github.com/bytedance/deer-flow/tree/main/skills/public/deep-research): breadth-to-depth discovery, reference tracing, gap-driven follow-up, convergence, and replanning ideas.
- [Google Labs Stitch Loop](https://github.com/google-labs-code/stitch-skills/tree/main/plugins/stitch-utilities/skills/stitch-loop): the baton, checkpoint, and next-action concept that informed disk-backed resumability. Its perpetual page-building loop was not copied.

## License

This project is licensed under the [MIT License](LICENSE).
