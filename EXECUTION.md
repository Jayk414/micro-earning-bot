# Execution layer — first stage

worker.py prepares application drafts and internal work orders for individually vetted jobs. It requires explicit AI permission, acceptance criteria, independently reviewed payment arrangements and zero upfront cost. These fields are human attestations, not automated verification.

Commands: python worker.py prepare vetted-job.json work/job-id; python worker.py package work/job-id. The latter requires deliverable files and review.json containing the exact criteria list, all_passed=true and actual evidence. Hashes identify the exact draft and deliverable contents for owner approval. Secret-extension checks are basic screening, not a complete secret detector.

This module is offline and cannot apply, execute downloaded job code, spend or submit. It does not claim the work was accepted or paid. ChatGPT can carry out selected research/coding during an active work session; unattended inference is not configured. No paid model endpoint is enabled.

Next stage: a platform-specific application adapter with approval tied to exact job, price, terms and application hash; isolated task execution; and a separate approval tied to delivery manifest. Account-specific authorization is required before enabling external writes. Discovery remains read-only.
