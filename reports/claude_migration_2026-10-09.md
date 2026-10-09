# Claude migration test, October 9th, 2026

The first manual run used Haiku 5.5 at High effort and completed an editorial no-target
package at `ed1cd2b0962f12345bbf8be516e8aee4270b1c1d` on
`codex/texas-desk-2026-10-09` ([draft PR 10](https://github.com/Talonsturgill/linkedin-texas-ai-desk/pull/10)).
The fetched dossier also passes the updated package validator locally.

Observed failures and waste:

- The copied Mac path did not exist; Claude found the attached Linux checkout.
- The required external skill validator was absent. Eight repository tests and config checks passed.
- Built-in ImageGen was unavailable. No image was produced because the result was no-target.
- Claude initially addressed its unsent draft to the session user, then corrected the recipient
  to the connected Gmail account using connector metadata. The correction was visible in its
  transcript. A metadata readback does not independently prove complete HTML body equality.
- The session continued into PR subscriptions and notification reads after its terminal report.

Claude's session usage panel reported 17 web searches, 6m 45s active/API time, and a $0.76
session cost estimate. It displayed 77 input tokens, 317 output tokens, 5.8M cache-read tokens,
110.5k cache-write tokens, and a 98% cache hit rate. These are the displayed figures; they
are not an invoice or an independently reconciled billing record. Context occupancy was 199k,
including 151.5k messages, and is a different measurement from token consumption.

The revised contract uses a portable entry point, Medium effort configuration, one editor,
bounded four-lane discovery, compact evidence packets, no post-run watcher, account resolution
before any Gmail write, and a capability check before research. Missing ImageGen stops as
needs-attention. It does not silently downgrade the user's generated artwork requirement.
Scores are recomputed from every configured criterion; personal copy rules are checked in
posts, image headlines, and email prose.

Local validation: 13 tests pass, configuration passes, and the missing-ImageGen preflight
returns exit 2 with needs-attention. This is a safety-path test, not proof of an autonomous
profile with generated artwork. Model and effort must be verified in a fresh Claude run;
repository settings alone are insufficient. Research limits are instruction-level budgets,
not provider-enforced token or dollar limits.

Documentation used for runtime behavior:
[model and effort configuration](https://code.claude.com/docs/en/model-config),
[session usage estimates](https://code.claude.com/docs/en/costs), and
[routine completion semantics](https://code.claude.com/docs/en/routines).
