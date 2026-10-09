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

## Saved routine and live verification

The saved Claude routine (now named Texas Desk) points to
`codex/texas-desk-claude-2026-10-09`. The two verification runs fetched runtime commit
`90e23d3238fa872d62db1a376f3a67d3fb5e037f`. The documentation connector was removed,
Gmail retained, and Auto-fix pull requests turned off. A dedicated Texas Desk cloud environment
uses Trusted network access and `CLAUDE_CODE_EFFORT_LEVEL=medium`, with no new credentials.
The existing Wednesday 4:04 AM Eastern schedule was retained. The duplicate legacy Codex
schedule was confirmed PAUSED after migration.

Two fresh Claude runs reached needs-attention before web research. The first created one
exact-subject status draft. The second found and updated that same draft, without creating
another status draft. It requested Gmail `FULL_CONTENT` readback and reported an exact subject,
matching body, DRAFT label, and no SENT label. Account resolution succeeded from the connector's
authenticated view URL before either write. The earlier no-target draft has a different subject
and was preserved. No profile image, LinkedIn post, sent email, or merge was produced.

| Session | Outcome | UI cost estimate | API / active | Cache read / write | Context |
| --- | --- | --- | --- | --- | --- |
| Baseline | No-target after research | $0.76 | 6m 45s / 6m 45s | 5.8M / 110.5k | 199k |
| Updated contract | ImageGen preflight failure; status draft created | $0.03 | 38s / 49s | 836.1k / 93k | 93k |
| Repeat | Same status draft updated; narrow effort diagnostic | $0.03 | 39s / 52s | 950.9k / 60.9k | 89.2k |

These are different workloads. The verified saving is avoiding research after a known capability
failure, not a measured reduction for an equivalent completed profile. Full profile cost and
artwork delivery remain unmeasured.

There is an unresolved effort-display mismatch. The runtime receipt confirmed the environment
value `medium`, but both fresh native controls displayed High. Manually setting the completed
second session to Medium did not carry into the third session. Do not claim proven Medium
operation or attribute these savings to effort. The serving effort was not independently exposed.
Built-in ImageGen was absent in both fresh tool inventories, so autonomous profile delivery is
still blocked. Web tool presence was verified; live source fetching under the new environment
was not exercised because the capability check stopped the run first.
