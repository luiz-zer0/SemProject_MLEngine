# Friday demo and evaluation handoff

SYNTHETIC ONLY. Base main: 346cb30. This run used Python 3.12.6 on Windows.
Designed same-item labels are engineering assertions, not independently verified
real matches. These results do not establish campus accuracy.

## Fresh setup (PowerShell, repository root)

Prerequisites: Git, Python 3.12, internet access for packages. Start in a parent
folder where a new checkout can be created, then run:

    git clone https://github.com/nimrod-kobia/SemProject_MLEngine.git
    cd SemProject_MLEngine
    git pull --ff-only origin main
    python -m venv .venv
    .venv/Scripts/python.exe -m pip install -r requirements.txt
    .venv/Scripts/python.exe -m unittest discover -s tests -q
    .venv/Scripts/python.exe scripts/evaluate_day2_synthetic.py
    .venv/Scripts/python.exe -m scripts.rebuild_nlp_index
    .venv/Scripts/python.exe -m scripts.demo_day3
    .venv/Scripts/python.exe scripts/capture_day3_evidence.py

Using the venv Python directly avoids activation-policy issues. On macOS/Linux,
use .venv/bin/python. Run from the repository root; use -m for scripts that import
matching_system. Review the PR branch until this handoff is merged. The commands
below were run in the existing environment, not a newly isolated clean install;
the fresh-venv recipe above is documented but a clean-machine install was not
verified. Dependencies currently have lower bounds, not a locked environment.

## Actual commands and results

- git fetch upstream; git switch -c codex/louis-friday-handoff upstream/main:
  base 346cb30, latest upstream main when fetched.
- python -m unittest discover -s tests -q: 37 tests, OK (1.390 seconds).
- python scripts/capture_day3_evidence.py: passed frozen Day 2 comparison,
  HTTP 200 health/bottle/telescope, invalid request 422, expected authored
  candidates, empty telescope result and ownership_approved false. This command
  also reruns scripts/evaluate_day2_synthetic.py internally.
- python -m scripts.rebuild_nlp_index: 4 found reports indexed, 31 vocabulary
  terms; index is memory-only, not a persisted or deployed artifact.
- python -m scripts.demo_day3: completed report-to-ranking-to-agent-evidence-to-
  suggested-staff-action pipeline. HTTP capture separately exercises the API.
- git diff --exit-code -- results/day2_synthetic_evaluation.json data/raw
  matching_system: no changes. git diff --check: passed before commit.

Machine-readable actual responses, query rankings and source hashes are in
results/friday_demo_evidence.json. Existing Day 3 evidence is preserved.
The capture uses HTTP TestClient in-process; network, Android, authentication,
persisted review decisions and item release are not demonstrated.
A Starlette TestClient/httpx deprecation warning was observed; tests passed.

## Compact synthetic evaluation

| Cohort | Queries | Recall@5 | MRR@5 | Uncertain pairs | Authored no-match |
| --- | ---: | ---: | ---: | --- | --- |
| Development | 11 | 1.000000 | 0.651515 | 8 corpus-wide, excluded from binary metrics | Separate case below |
| Held-out test | 3 | 1.000000 | 0.611111 | Same 8, not an additional count | Separate case below |
| All labelled lost queries | 14 | 1.000000 | 0.642857 | 8 total | Not in ranking denominator |
| Authored telescope syn-q03 | 1 | N/A | N/A | N/A | 1/1 empty candidate list |

46 synthetic reports (14 lost, 32 found); 32 designed pairs (14 match,
8 plausible/uncertain, 10 non_match). No verified real-world pairs. Uncertain
pairs are never negatives. No binary accuracy is reported. Recall/MRR use known
designed positives only, with MRR truncated at five. Fixed grouped split and
source hashes are unchanged; the found-only inventory includes test counterparts
because this is retrieval, not an ownership classifier. Empty lexical output
is not proof that a physical counterpart does not exist.

## Present the report-to-staff-review demo

Read the bottle request and response in results/friday_demo_evidence.json.
The authored blue scratched metal bottle returns:

| Rank | Candidate | Cosine similarity | Advisory action | Ownership approved |
| --- | --- | ---: | --- | --- |
| 1 | demo-found-metal | 0.835001 | review_conflicts | false |
| 2 | demo-found-unknown | 0.699263 | request_details | false |
| 3 | demo-found-plastic | 0.563049 | review_conflicts | false |

The metal suggestion agrees on category and compatible date, but its location
differs. It is authored as the same item, not independently verified. Unknown
has missing category/date evidence. Plastic overlaps in wording but conflicts
on material/category. Staff must inspect evidence; scores are not ownership
probabilities. The telescope HTTP query has zero candidates. No release action
or saved staff decision follows any response.

For an optional local network walkthrough, run in terminal A:

    .venv/Scripts/python.exe -m uvicorn matching_system.api:app --host 127.0.0.1 --port 8000

In terminal B, send the synthetic request (never private real report text):

    Invoke-RestMethod http://127.0.0.1:8000/health
    $body = @{item_name='Metal water bottle';description='Blue bottle with a scratched lid';category_id='metal_water_bottle';location_id='msb';event_date='2026-11-10';limit=3} | ConvertTo-Json
    Invoke-RestMethod http://127.0.0.1:8000/preview/matches -Method Post -ContentType 'application/json' -Body $body | ConvertTo-Json -Depth 20

Stop terminal A with Ctrl+C. These network commands are a walkthrough recipe;
this run verified the same API routes in-process. The local preview uses fixed
synthetic inventory and is not a real-report intake endpoint.

## Before importing permitted real data

- Confirm collection permission, intended use, retention and authorized access.
  Have a person review privacy before import. Remove private ID numbers, contact
  details, names and sensitive incidental text from model fields; keep necessary
  consent/source/evidence references in protected storage. Pattern rejection in
  the API is incomplete and does not make arbitrary reports safe to submit.
- Copy data/templates/day1/real_reports.csv and verified_pairs.csv to protected
  intake storage, or use intake.json arrays with matching field names. Preserve
  synthetic fixtures separately; never overwrite raw campus files or commit
  private records/evidence to the repository.
- Validate nonempty, unique report_id and pair_id; report_type lost/found;
  descriptions; explicit category/location IDs; valid timezone-aware event dates.
  Do not equate reported_at with event_date. Reject dangling pair references,
  repeated pairs and pairs that do not link one lost and one found report.
- Record source/consent and independent reviewer, reviewed_at, verification_method
  and evidence_reference. Review actual physical identity separately from text
  similarity. Unresolved/plausible labels remain uncertain; do not manufacture
  negative labels from missing evidence or failed retrieval.
- Build reviewed physical-item groups, including duplicates and wording variants.
  Keep each group in one query split; adjudicate uncertain cross-group links.
  Freeze a versioned evaluation manifest, source hashes and relevance labels
  before tuning. Keep verified real metrics separate from designed synthetic ones.
- Parse JSON with json.load or CSV with csv.DictReader using utf-8-sig; validate
  before converting to report CSV. Use load_text_reports_csv with an explicit
  mapping for report_id, report_type, description, item_name, category_id,
  location_id and event_date. Pair labels remain separate from model input.
- Fit TfidfRanker on reviewed found reports only; rank lost reports. Rebuild using
  replace_inventory when inventory changes. python -m scripts.rebuild_nlp_index
  PATH_TO_APPROVED_REPORT_CSV checks the in-memory corpus; it does not deploy it
  or switch the API's fixed demo inventory. Any production inventory wiring,
  access controls, persistence and release workflow need separate implementation.
- Check counts, references, source hashes, split leakage and uncertain exclusion;
  report ranking metrics and no-match behavior with denominators. Request staff
  review on conflicts/missing evidence; never authorize ownership from ranking.

## Remaining dependencies

Android integration is unverified: no Android build or client connection was run.
No screenshots are supplied because this handoff records CLI/JSON API evidence.
Production auth, protected real-data intake, persistent review/audit trail,
independent pair verification, representative real reports, calibrated abstention
and item-release authorization remain pending. See also
friday_knowledge_agents_api_handoff.md for the agent/API owner's handoff.
