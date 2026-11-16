# Research fulfilment pilot

Zero-dependency Python tools. No paid APIs, bidding, outbound messages, financial credentials or automatic delivery.

## Research
`python research.py --query 'cat:cs.AI' --count 20 --out output/new-pack`

Or use `--feed owner-supplied.xml` for offline runs. One request, maximum 50 records, 2 MB feed, 30 second timeout, redirects refused. Allow at least three seconds between runs, per arXiv API guidance. API errors stop the run; no paid fallback.

Outputs: papers.csv, report.md, quality.json and provenance.json (query URL/time/feed hash). Deduplicates versioned arXiv IDs; checks required fields, dates, exact count and evidence inclusion; neutralises spreadsheet formulas.

**Important:** summary is a labelled 20-word abstract excerpt, not generated synthesis. Full abstracts and full papers are not copied. No automatic relevance, claim correctness, peer-review or client acceptance verification. Delivery is always false. This is an evidence collection tool, not yet an autonomous researcher. Human review must supply original summaries/key findings, verify each source and meet the actual client's criteria before owner-approved delivery.

Sample is a current cs.AI metadata pilot, not the 2024–2025 dataset requested by any client. It has not been submitted to a platform.

Thank you to arXiv for use of its open access interoperability.
API guidance: https://github.com/arXiv/arxiv-docs/blob/develop/source/help/api/user-manual.md

## Private proposal tracking
`python tracker.py PRIVATE_TRACKER.json 'Customer Name' replied --note 'Reply received; scope not agreed'`

Stages: sent, replied, scope_agreed, in_progress, owner_review, delivered, paid, declined. Later stages require a note; notes are operator attestations, never payment verification. Actual approvals still happen with Jay. Keep customer data, replies and payment details out of this public repo. A seeded private tracker is provided separately, not committed.

Tests: `python -m unittest discover -s tests -v` from this directory.
