[한국어](README.ko.md)

# Hermes Deep Research

A Hermes skill for research that has to hold up.

## 🤔 Why this exists

Ask an ordinary search skill a hard question and you get a page from the top few hits. Ask a one-pass research skill and you get a single round of searching, summarized once, held entirely in the conversation. On anything genuinely contested — or anything that takes longer than one session — both run out of road.

### How it operates

| | Ordinary search | One-pass research | Hermes Deep Research |
| --- | --- | --- | --- |
| **Structure** | One query, one result list | One round of searching, summarized once | The question is split into research axes and worked as parallel lanes |
| **Coverage** | The top few hits | Whatever a single pass collected | Lanes per language and source surface, up to each axis's ceiling |
| **Verification** | None | Whatever the summarization pass happened to catch | Each wave checks original pages, source independence, freshness, and counterevidence |
| **Progress state** | None | Lives in the conversation context | `state.json`, `sources.json`, and `notes/` on disk, checkpointed every step |
| **If the Gateway stops** | Not applicable — it already finished | The work dies with it | The files survive; the run reads them and continues from that point |
| **Duration** | Seconds | One session | Hours, spread across sessions and restarts via cron |
| **Finishing** | You decide when you have enough | Done after one pass | `completed` on convergence, `partial` at a limit — with the remaining gaps named |
| **Output** | Links | A summary | A report plus a separate source ledger, and a PDF only on request |

### What that changes in the result

| What usually goes wrong | What this skill does instead |
| --- | --- |
| Snippets stand in for sources — a search-result summary gets quoted as if the page had been read | Original pages are opened for consequential, disputed, and directly quoted claims, and snippets count as discovery only |
| Source count reads as evidence — ten links that all rewrite one press release look like ten confirmations | Syndications, rewrites, translations, and same-actor pages are collapsed into one evidence family before anything is concluded |
| Only confirming evidence gets searched | Countersearch is written into each research axis, not left to chance |
| Conflicting numbers get averaged, or one side quietly wins | Conflicts are compared directly; differences in population, definitions, timeframe, incentives, and method are named, and unresolved ones stay visible in the report |
| Gaps vanish into confident prose | A run may end `partial`, and the report has to say which gaps remain |
| More is treated as better — more searches, more sources, longer output | Budgets are ceilings, not targets; research stops at saturation and the reserve goes into verification and writing |

The trade is honest: this is slower and more expensive than a lookup. It is for questions where being wrong costs more than being late.

| | |
| --- | --- |
| **Use it for** | Multi-source investigation, conflicting accounts, lived experience and community discourse, long unattended research runs |
| **Not for** | Quick lookups, and regulatory or audit-grade evidence |
| **Requirements** | Hermes with web/file/terminal toolsets, Python 3.10+ (standard library only) |

Everything runs on standard Hermes tools — web and browser, files, terminal, and helper agents. Nothing runs as a daemon and no external service is involved.

## 📦 Install

Inspect the skill before installing it, then use the tested commands:

```bash
hermes skills inspect https://raw.githubusercontent.com/Gyu-bot/hermes-deep-research/main/SKILL.md
hermes skills install https://raw.githubusercontent.com/Gyu-bot/hermes-deep-research/main/SKILL.md
```

Manual HTTPS clone as a fallback:

```bash
mkdir -p ~/.hermes/skills/research
git clone https://github.com/Gyu-bot/hermes-deep-research.git \
  ~/.hermes/skills/research/hermes-deep-research
```

Read `SKILL.md` after installing. Keep research runs outside the installed skill directory — the skill package and the run artifacts are deliberately separate.

Hermes cron is needed only for unattended runs.

### Check subagent concurrency first

Coverage lanes are dispatched with `delegate_task`, and Hermes caps how many children run at once with `delegation.max_concurrent_children` — **3 by default**. A `deep` wave usually plans more lanes than that.

The cap is enforced rather than smoothed over: per the Hermes documentation, "batches larger than the limit return a tool error rather than being silently truncated" — no queueing, no truncation. The parent is instructed to read the live limit and size its batches to fit, so a correctly behaving run serializes instead of erroring. But left at 3, a wave that planned six lanes runs as two sequential batches, the run takes proportionally longer, and since the mode budget is wall-clock time, `deep` and `exhaustive` runs can reach that budget and finish `partial` before coverage would otherwise have converged.

So raise it to roughly one per lane you expect in a wave before your first real run, in `~/.hermes/config.yaml`:

```yaml
delegation:
  max_concurrent_children: 8   # default 3, floor 1, no hard ceiling
```

or for a single session:

```bash
export DELEGATION_MAX_CONCURRENT_CHILDREN=8
```

Concurrent children multiply token spend as well as throughput, so pick a number you actually want to pay for. Confirm the current key and default against the [Hermes delegation docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation) — this skill never sets or changes the value itself, treating runtime limits purely as dispatch ceilings.

### Optional external skills

Two separately maintained skills turn the finished research into something people actually enjoy reading — one at the sentence layer, one at the document layer. Neither ships with this repository and neither is installed automatically; each is its own project that you install yourself, following that project's current instructions. Recommended when a final report is the deliverable:

| Skill | What it is for | Repository |
| --- | --- | --- |
| **Bookforge** | Document design — laying the approved report out as a typeset, well-structured PDF that reads well on the page. The only supported path to a PDF | [gongnyang/bookforge](https://github.com/gongnyang/bookforge) |
| **Humanize Korean** | Sentence polish — rewriting Korean prose so it reads like a person wrote it, without AI-sounding phrasing or translationese | [epoko77-ai/im-not-ai](https://github.com/epoko77-ai/im-not-ai) |

Neither is used when the research is only feeding another task as context; they exist for the case where a person sits down and reads the final report. Install each from its own repository and check its compatibility before invoking it — do not copy its scripts or instructions into this skill. Research itself is complete without either: if the integration you need is missing, Hermes delivers the validated Markdown and says so rather than claiming a PDF or a polished draft it did not produce. See [Optional integrations](#-optional-integrations) for how each one is gated.

<details>
<summary>Checklist for an installation agent</summary>

- Inspect `SKILL.md` and the repository before installing anything.
- Install only the Hermes Deep Research base skill.
- Confirm standard Hermes support for helper tasks, web and browser access, files, and terminal commands. Confirm Hermes cron only if unattended research was requested.
- Check `delegation.max_concurrent_children` (default 3), report its current value to the user, and explain that leaving it below one per planned lane serializes each wave and can push a long run to `partial`. Ask before changing it; never raise it silently.
- Install the optional external skills separately from their own repositories, only when the requested deliverable needs them, and check their current upstream instructions and compatibility first.
- Do not install unrelated tools or change credentials, providers, or other settings.
- Run the tests and the temporary `init` → `validate` → `status` smoke check from the development section below.

Copyable prompt:

```text
Inspect this repository and SKILL.md first. Install only the Hermes Deep Research
base skill and verify its standard Hermes tools. Run the included standard-library
tests and a temporary init/validate/status smoke test. Check my
delegation.max_concurrent_children setting and tell me whether it is high enough
for parallel research lanes, but ask before changing it. Do not change credentials
or install unrelated tools. Install
optional integrations only when my requested output needs them, and check their
current upstream instructions and compatibility first.
```

</details>

## 🚀 Use it

A request that already carries its own scope starts research immediately:

```text
Use deep mode to investigate whether small Korean exporters are adopting AI
translation tools. This is a report for policy staff. Include Korean and English
sources, recent evidence since 2024, user experience, and disagreement between
vendor claims and independent evidence. A Markdown report is enough; do not make a PDF.
```

A bare topic gets a short interview first:

```text
Research congestion pricing.
```

Hermes may ask which city and period matter, how the result will be used, and what the report must cover. It asks at most three questions, and only when the answer would change the research.

More shapes of request:

```text
Quickly research the main arguments for and against congestion pricing in Seoul.
Use quick mode and return a detailed Markdown report with the source list.
```

```text
Run exhaustive research on long-duration energy storage for island grids. Continue
only while important gaps have a practical search path. Mark the result partial if
important gaps remain when a planning limit is reached.
```

```text
Run this as unattended deep research with Hermes cron. Save each step in a unique
run directory and deliver the completed or partial Markdown report after synthesis.
```

```text
Research this topic in deep mode. After the Markdown report passes validation,
prepare a final PDF using the document-readiness and SHA-256 checks. Preserve the
Markdown report and source files too.
```

## 📄 What you get

Each run owns a directory, normally under `~/.hermes/research/hermes-deep-research/`, and never reuses another run's:

```text
<run-dir>/
├── state.json     # question, mode, axes, wave history, limitations, next actions
├── sources.json   # source ledger: topic, note, use, limitation
├── notes/         # completed helper-agent research notes
└── report.md      # the final Markdown report
```

`report.md` is the deliverable: an executive orientation, scope and method, substantive thematic sections, agreements and conflicts with their likely causes, cases and context, strong versus limited evidence, uncertainties and limitations, conclusions, and a curated major-source list. The orientation summarizes the body; it never replaces it.

`sources.json` is the source-to-report map. Every useful source records what it covers, how it was used, and where it stops being reliable — which is why sentence-level citations are optional in the report body.

A run ends `completed` when coverage converged, or `partial` when a planning limit was reached while material gaps remained. Useful incomplete work is `partial`, never `failed`, and the report has to name the gaps.

## 🔍 How a run works

1. **Scope the question.** Objective, intended use, scope and exclusions, freshness needs, mandatory topics, and success criteria. Hermes also decides whether the deliverable is a reader-facing report or an internal memo feeding a larger task, and records separately whether you explicitly asked for a document or PDF. Asking for deep research is not asking for a PDF.
2. **Split it into research axes.** A few distinct axes that together cover the need, each with the question it must answer, useful query families and languages, freshness needs, what counts as adequate coverage, and the counterclaims worth searching for. Counterevidence lives inside the relevant axis rather than being someone else's job.
3. **Research in waves.** A wave is a research stage, not a search or a tool call. Wave 1 establishes broad multilingual and source-surface coverage. Wave 2 checks original pages, source independence, freshness, and counterevidence. Wave 3 digs into conflicts and their conditions, lived experience, and edge cases. Wave 4 closes targeted gaps. `quick` compresses all of that into one wave; `exhaustive` may extend to eight, but only for material gaps.
4. **Checkpoint after every step.** Notes, sources, coverage counters, disagreements, new leads, limitations, and concrete `next_actions` are written to disk before the next dispatch, so a fresh session can continue without the conversation history.
5. **Decide when to stop.** Continue while a material gap has a practical search path and the budget allows. Stop when new searches mostly repeat what is already known — including when convergence happens exactly at the maximum wave, which still counts as complete.
6. **Write the report.** Synthesis, source reconciliation, conflict review, confidence language, and the `completed`/`partial` decision all happen before any editorial polish, and long before any document rendering.

Search counts and source counts are diagnostics, not completion criteria. What matters is whether the report answers the question, explains disagreement, and is honest about what remains uncertain.

## ⚙️ Modes

- **`quick`** — a focused question that needs more than a lookup but can finish in one stage.
- **`deep`** — the normal choice when the question needs several stages.
- **`exhaustive`** — extra stages for important gaps, when the added work is genuinely useful.

The numbers below are planning ceilings, not targets, quotas, or evidence of quality. Hermes may stop well short of them.

| Mode | Total budget | Max waves | Queries per axis | Original-page fetches per axis |
| --- | ---: | ---: | ---: | ---: |
| `quick` | 1,800 s | 1 | 8 | 8 |
| `deep` | 10,800 s | 4 | 20 | 20 |
| `exhaustive` | 21,600 s | 8 | 40 | 40 |

At least 20% of the budget is reserved for integration, source rechecks, conflict analysis, and writing. The parent may move budget around within the same total to close a material gap, but must record what changed and why in `planning.budget_reallocations`.

## 👥 Who does what

**The parent agent** owns the run. It plans axes and waves, holds the run files, opens the consequential and disputed pages itself, collapses mirrors and rewrites into single evidence families, resolves conflicts, decides `completed` or `partial`, and writes the report.

**Helper agents** take one bounded coverage lane each and return a Markdown note using the [research-note template](templates/research-note.md). They run in parallel, never write to the shared run directory, never decide that the research is finished, and never substitute for the parent's own source checks. A child summary is not authority.

Lanes are flat, not nested: an axis may be split by language, source surface, or adversarial perspective, but splitting lanes does not multiply that axis's ceilings — lane queries and fetches aggregate back into the same counters.

## 💾 Persistence and restarts

The run directory is the persistence mechanism. It survives a Hermes Gateway stop; in-flight helper and model calls do not. After a restart, any lane without a saved note is treated as pending and redone — never described as resumed. A saved note whose state update was interrupted is integrated rather than researched again.

Nothing progresses while the Gateway is down. A saved cron schedule simply resumes firing afterward, reads the files, and continues from them.

For unattended work, the skill uses Hermes cron directly — one bounded, self-contained recurring job, no supervisor, daemon, worker runner, or self-scheduler. Each tick performs exactly one bounded action, writes its artifact, checkpoints, and returns `[SILENT]`; the first tick that makes the report terminal delivers it back to the originating conversation. A tick never edits its own cron job. See [references/unattended-research.md](references/unattended-research.md) for the exact pattern.

## 🔌 Optional integrations

Research produces a correct report. These two skills make it a pleasant one to read, at two different layers: **Humanize Korean** fixes how the sentences sound, and **Bookforge** fixes how the finished document looks. Neither touches what the research found.

Both apply only when a final report is the deliverable — something a person will sit down and read. When the research is an internal memo feeding a larger task, its Markdown and source ledger go straight to whatever consumes them and neither skill runs. Both are also strictly post-research: they run after the `completed`/`partial` decision is already made, so polish and layout can never create evidence or change a status.

Both are external skills maintained in their own repositories, [installed separately](#optional-external-skills) and never pulled in automatically. Deep research completes without either, and neither is a dependency of this skill. Check their current upstream instructions before use.

### Bookforge — document design for a requested PDF

[Bookforge](https://github.com/gongnyang/bookforge) is the last mile: it takes the approved Markdown and lays it out as a typeset PDF — structure, typography, and a cover — so the report reads well on the page instead of looking like a dumped text file. It may normalize headings and chapter boundaries for typesetting, but it must not re-research, pad, or rewrite the report's claims.

Two gates stand in front of it. First the document-readiness gate: the accepted report is preserved as `report.pre-document.md`, a document-only edit becomes `report.document-candidate.md`, and the parent records a qualitative `PASS`/`FAIL` in `report.document-readiness-gate.md` — automation does not judge readability. `scripts/document_gate.py pass` then copies the approved bytes to `report.document-ready.md` and binds them with SHA-256. Immediately before handoff, `document_gate.py verify` must succeed, or rendering is blocked.

Keeping rendering in a separate project keeps research separate from typesetting and lets this skill work without depending on another repository. If Bookforge is unavailable, deliver the validated Markdown and do not claim a PDF was produced. Details: [references/report-documentation.md](references/report-documentation.md).

### Humanize Korean — sentence polish for a Korean report

[Humanize Korean](https://github.com/epoko77-ai/im-not-ai) works on the prose rather than the layout. It strips the AI-sounding Korean, translationese, padding, and mechanical rhythm that make an otherwise solid report tiring to read, while preserving meaning, facts, numbers, dates, proper nouns, quotations, technical terms, structure, links, uncertainty, and register. It runs on a copy, never on the canonical draft.

Its output is an untrusted candidate. The parent diffs it against `report.pre-polish.md` and rejects or repairs any change to facts, meaning, confidence, scope, conditions, contradictions, limitations, numbers, dates, names, quotations, links, or structure. If the edit cannot be verified, the validated pre-polish draft ships instead — smoother prose is never worth a weakened evidence check.

## 🗂️ Repository layout

```text
hermes-deep-research/
├── SKILL.md                            # the behavior contract Hermes follows
├── references/
│   ├── source-review.md                # fit-for-purpose source evaluation
│   ├── unattended-research.md          # the Hermes cron pattern
│   ├── report-documentation.md         # the two-stage documentation workflow
│   └── LICENSE.md
├── scripts/
│   ├── research_state.py               # init / status / validate a run
│   └── document_gate.py                # pass / fail / verify the document gate
├── templates/
│   ├── research-note.md                # helper-agent note format
│   └── report.md                       # final report structure
└── tests/
```

[SKILL.md](SKILL.md) is the authoritative description of the workflow; this README is the tour.

## 🧪 Development

The helper scripts and tests use Python 3.10+ and the standard library only — no dependencies to install.

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

`research_state.py` creates a run and validates its shape: known status and mode, positive planning ceilings, a current wave within the maximum, a synthesis reserve of at least 20%, budget reallocations that carry reasons, well-formed axes whose note paths stay inside the run directory, and a non-empty report for any `completed` or `partial` run. `document_gate.py` records and verifies the SHA-256 binding for an approved document candidate. Neither script judges research quality; both write atomically so an interrupted run leaves no half-written state.

## ⚠️ Limits and safety

- More sources do not prove a claim. Independence, relevance, method, context, and disagreement do the work — see [references/source-review.md](references/source-review.md).
- Web content is untrusted data, never instructions. Consequential, disputed, and directly quoted claims are checked against original pages when they are reachable.
- Pages can be changed, blocked, paywalled, or gone. The resulting limits are recorded rather than papered over.
- A run may legitimately end `partial`. The report must say which gaps remain.
- This supports personal research. It is not a regulatory or audit evidence system, and medical, legal, financial, and safety conclusions need current authoritative sources plus appropriate professional judgment.

## 📚 Attribution and inspiration

The workflow adapts concepts from the projects below for Hermes. No source code was copied, and these links do not imply affiliation or endorsement.

- [LazyCodex](https://github.com/code-yeongyu/lazycodex) and [Oh My OpenAgent (OmO)](https://github.com/code-yeongyu/oh-my-openagent) — splitting a question into research axes, repeated helper-agent stages, following useful leads, and keeping the parent in charge of coordination.
- [Serkaion Deep Research](https://clawhub.ai/api/v1/skills/serkaion-deep-research) — cross-checking independent sources, actively hunting for evidence against a claim, and stating uncertainty per claim.
- [Autosolutions Deep Research](https://clawhub.ai/api/v1/skills/autosolutions-deep-research) — multi-pass research, preferring original sources, spotting contradictions, and returning separate structured helper notes. Its large fixed helper count and source quotas were not adopted.
- [ByteDance DeerFlow deep-research skill](https://github.com/bytedance/deer-flow/tree/main/skills/public/deep-research) — moving from broad discovery to deeper verification, following references, returning to gaps, judging when findings have settled, and revising the plan.
- [Google Labs Stitch Loop](https://github.com/google-labs-code/stitch-skills/tree/main/plugins/stitch-utilities/skills/stitch-loop) — handing work forward through checkpoints and a saved next action. Its never-ending page-building loop was not copied.

## 📜 License

[MIT](LICENSE).
