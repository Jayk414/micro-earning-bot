# Micro-Earning Bot

Zero-cost, read-only MoltJobs opportunity discovery and curated research drafting. No dependencies, model API charges, credentials, bids, submissions, wallet actions or payments.

## Scheduled operation

Runs every six hours (00:23, 06:23, 12:23 and 18:23 UTC), on relevant main-branch changes and manual dispatch. The workflow runs only in the public Jayk414/micro-earning-bot repository on standard ubuntu-latest runners, with a five-minute timeout and read-only contents permission. No paid runner, artifact upload or cache is used. GitHub states standard runners are free in public repositories: https://docs.github.com/en/actions/concepts/billing-and-usage . Schedules may be delayed or disabled after repository inactivity. This is periodic execution, not an always-running server.

Open the Actions tab, choose the latest run and read its Summary for the generated report, opportunity assessments and quality flags. Full raw vendor pages are temporary runner files and are not published.

## Local use

Requires Python 3.10+:

```sh
python -m unittest discover -s tests -v
python bot.py
```

Outputs appear in output/. Discovery errors fail the run rather than silently claiming there are no jobs. Source fetch failures are recorded and reports remain internal drafts.

## Limits and authority

This prototype matches job keywords, flags funding/scope gaps, refreshes three curated primary sources and assembles a draft. It does not autonomously research arbitrary topics, execute software jobs or verify escrow on-chain. API funding flags and transaction hashes are screening signals only. No opportunity is labelled verified payment. Acceptance, assignment and settlement need separate verification.

The 180 USDC asset-management job was OPEN but unfunded at inspection on 10 November 2026, due 4 December, with no recorded acceptance criteria. The included sample is not a comprehensive client deliverable. No bid, submission, evaluation or payment has been made; earnings verified: zero.

Future bidding, paid services, spending and delivery require the owner's explicit approval of the specific action and deliverable. This version has no write API or money-moving credentials.

## Validation

12 unit tests passed locally; first local live run checked 18 open records, found seven potential skill matches, held all for unresolved checks, and fetched three of three research pages. See Actions for independent cloud execution results. Job text and retrieved pages are untrusted data, never executable instructions.
