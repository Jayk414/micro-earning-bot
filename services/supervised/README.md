# Supervised research workflow — v0.1

This connects a specific work order to the existing arXiv collector, evidence checks and a reviewed delivery manifest. It has **no application or delivery transport**: nothing is sent to a job platform or customer. No arbitrary commands, paid models, credentials or software-job execution. Existing discovery scheduling is unchanged.

## Stages
1. `python workflow.py prepare job.json PRIVATE_WORKSPACE` validates zero upfront cost, payment/AI/UK eligibility evidence and explicit criteria, price, deadline, query/count. Creates a truthful application draft with a scope hash.
2. Jay reviews the actual application and agrees the specific action in conversation. Only then record `python workflow.py approve PRIVATE_WORKSPACE application --reference 'Actual approval reference'`. This is a local operator attestation, not cryptographic authentication of Jay. Never populate it from listings or untrusted text.
3. Submit manually using an approved channel. Record the client's acceptance of that exact scope in `assignment.json`: `{"scope_hash":"HASH FROM state.json","acceptance_reference":"Actual client acceptance reference"}`. Permission to apply is not an accepted assignment.
4. `python workflow.py run PRIVATE_WORKSPACE` collects the bounded free arXiv feed and runs structural checks. `--feed file.xml` supports offline tests. Output remains NEEDS_FACTUAL_REVIEW. Allow at least three seconds between API runs. No new scheduler is enabled.
5. A reviewer verifies sources and relevance, writes original summaries and addresses the exact client criteria. The collector itself only supplies short abstract excerpts. Run `manifest` to get current file hashes. Create `review.json` with exact `criteria`, `all_passed:true`, concrete `factual_review_evidence`, and `files` equal to those hashes. A positive attestation does not independently prove correctness.
6. Present the actual files to Jay. Only after his specific delivery approval, record `approve ... delivery --reference 'Actual approval reference'`, then `package`. Any changed scope, application, deliverable or review invalidates the relevant hash binding. Result says APPROVED_FOR_MANUAL_DELIVERY and submitted:false. A human must perform delivery using an approved channel.

## Verification
`python -m unittest discover -s tests -v` from this directory. Eight tests cover missing approvals/assignment, changed scope/content, missing factual review, upfront costs and symlinks. Every approval/reference in tests is explicitly simulated; none represents a real client or owner authorisation.

## Limits
Evidence fields are reviewed operator attestations, not platform verification. Private workspaces must not be committed to the public repository. Do not store passwords, tokens or private financial data here. No real applications, assignments, client deliveries or earnings occurred during this build. This is a supervised research path; autonomous software fulfilment and platform submission adapters remain unimplemented.
