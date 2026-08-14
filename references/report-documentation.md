# Final report documentation

Use this workflow only when the user explicitly asks for a report document, final document, or PDF. Deep research by itself ends with the normal research report and separate `sources.json` ledger.

Research synthesis and the optional language-polish pass happen before documentation. Documentation itself has exactly two stages.

## Stage 1 — document-readiness gate

1. Validate the terminal `completed` or `partial` research run.
2. Preserve the accepted research report as `report.pre-document.md` before any document editing. Never overwrite it.
3. Prepare `report.document-candidate.md` using document-only edits. Improve ordering, headings, transitions, definitions, and reader context without adding claims, evidence, examples, citations, or confidence not already present in `report.pre-document.md`.
4. Create `report.document-readiness-gate.md` with the candidate path, research status, check date, one row per requirement below, notes for any defect, and an explicit `Final verdict: PASS` or `Final verdict: FAIL`. Every row must pass for the final verdict to be `PASS`. This Markdown file is the human qualitative audit record; automation does not decide readability.

Required checks:

- The manuscript is readable for the intended audience and stands alone without access to the research workspace.
- The objective, scope, and as-of date are understandable from the document itself.
- The narrative is coherent from beginning to end.
- The executive summary, body, and conclusions agree.
- Necessary terms are defined for the intended reader.
- Facts, interpretations, and limitations are distinguishable.
- No placeholders, raw notes, internal paths, process debris, unexplained metadata, or dangling references to local artifacts remain.
- The curated major sources are sufficient for the PDF to stand alone; keep the complete `sources.json` ledger as a separate delivery artifact, not manuscript input.
- A `partial` status and all material remaining gaps are visible in the manuscript.
- Document editing introduced no new claim, evidence, or substantive change.

After the parent makes that qualitative decision, record it with the installed skill helper. Supply `--checked-at` when the gate record already has the exact check time; otherwise the helper records the current UTC time safely.

```bash
python3 "/absolute/skill/dir/scripts/document_gate.py" pass "$RUN_DIR" \
  --checked-at "2026-08-11T12:00:00+00:00" --research-status completed
```

`pass` requires `report.pre-document.md`, `report.document-candidate.md`, and the human gate record with final `PASS` and no final `FAIL`. It atomically copies the candidate bytes to `report.document-ready.md` and writes `report.document-readiness-gate.json` with the PASS verdict, bound paths, and SHA-256. The JSON file is the machine binding; it does not replace or reinterpret the Markdown audit.

On qualitative `FAIL`, leave the defects in the Markdown record and replace the machine binding:

```bash
python3 "/absolute/skill/dir/scripts/document_gate.py" fail "$RUN_DIR" \
  --reason "Remaining document-readiness defects" \
  --checked-at "2026-08-11T12:00:00+00:00" --research-status partial
```

`fail` does not create or update `report.document-ready.md`; an older ready file may remain only for preservation and is not authorized for rendering. Re-edit from `report.pre-document.md` and run a new qualitative gate before recording another verdict.

Immediately before Bookforge handoff, verify the current binding:

```bash
python3 "/absolute/skill/dir/scripts/document_gate.py" verify "$RUN_DIR"
```

Do not scaffold a Bookforge project or render until this exact command succeeds. A current FAIL binding, a stale or changed candidate/ready file, a path escape, or a Markdown gate without final PASS and no final FAIL blocks Bookforge.

## Stage 2 — render with the separate Bookforge skill

Only after the user has explicitly requested a final document or PDF, inspect [Bookforge's current upstream instructions](https://github.com/gongnyang/bookforge) and verify that a compatible installation is available before invoking its manuscript mode. Do not install or invoke it for ordinary deep research, and do not copy Bookforge instructions, scripts, styles, or implementation into this skill. If the optional integration is unavailable, preserve and deliver the validated Markdown artifacts without claiming a PDF was produced.

- Hand off only the passed `report.document-ready.md`. Do not pass `sources.json`, notes, the pre-document draft, or the gate record as manuscript material.
- Create the disposable Bookforge project inside `RUN_DIR/tmp/workspace/bookforge/`, keep downloads and transient rendering files under `RUN_DIR/tmp/`, and copy the final PDF to durable `RUN_DIR/report.pdf`.
- Use manuscript mode. Bookforge may normalize headings, chapter boundaries, and supported markup for structure and typesetting, but it must not re-research, invent, pad, substantively rewrite, or change the report's claims.
- Use a user-specified style when present. Otherwise choose `business` for ordinary research, strategy, or market reports and `insight` for technical, trend, or data briefings. Ask about style only when the content genuinely makes this default ambiguous.
- Choose length from the manuscript body without truncating or padding: `compact` below 12,000 Korean characters, `short` from 12,000 to below 25,000, `standard` from 25,000 through 80,000, and `long` above 80,000.
- Use an authorless report cover: title, optional subtitle, and the document's as-of date; if no as-of date applies, use the prepared date. Pass a blank author value.
- Run Bookforge's normal build, QC, and visual-review workflow. Do not use `--refit` to downgrade a `compact` page-range failure; any Bookforge QC failure still blocks the final PDF.

The primary deliverables are root-level `report.pdf` and `report.document-ready.md`. Also preserve `report.pre-document.md`, `report.document-readiness-gate.md`, `report.document-readiness-gate.json`, and `sources.json` at the run root. The Bookforge project is disposable work, not a durable research artifact.
