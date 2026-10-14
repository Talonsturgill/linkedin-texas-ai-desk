# Texas Desk cloud delivery test — October 9th, 2026

This test launched the saved **Texas Desk** Claude routine, using Haiku 5.5 and its attached
Texas Desk environment. It completed live source fetching, editorial selection, bespoke coded
artwork, dated artifact pushes, an immutable image check, and an unsent Gmail draft. The result
was engineering-assisted: source leads and review corrections were supplied during the run.
It is evidence for the repaired path, not proof of a fully unattended run with the final contract.

The selected decision is Chad Seely's account of ERCOT placing large-load eligibility verification
ahead of the Batch Zero interconnection study. The primary ERCOT presentation, ERCOT role page,
Texas Tribune reporting and Utility Dive reporting support the package. The copy distinguishes
the governor's directive from Seely's operational accountability, uses August tense for August
plans, and identifies the pre-directive review sequence as the baseline. Public-policy coverage
uses neutral accountability, with no political endorsement or rating.

## Repairs exercised

- Compute the 60- and 90-day research windows before discovery, after dependency setup. A named
  operator's implementation decision can be supported jointly by a primary process document and
  independent attributed reporting; a title or unsigned PDF alone does not establish ownership.
- Read the compact artwork schema instead of rediscovering it from validator implementation.
  The initial drawing was adjusted to keep its dropped card inside the focal band. A third build
  was explicitly authorized for the engineering dossier-hash refresh; pixels stayed unchanged.
  Future ordinary runs still have two artwork attempts.
- Preserve the full-suite process until its actual exit status. The first short-timeout attempt
  was incomplete; the subsequent 48-test cloud suites passed in 138.8 and 139.4 seconds.
- Reject stale chronology, an unsupported available alternative, generic importance prose,
  and style metadata that does not describe the picture. Scores were not increased after review.
- Use a real small attachment for Claude Gmail. RAW MIME proved that remote `img` tags were
  removed and a longer manually copied base64 attachment was corrupt. The broken attachment was
  removed. A 160-square JPEG made from the approved cover was then stored successfully: 2,410
  bytes, SHA-256 `84fa505e8a088e3117916ffed29f58fa5f088fb486d6f9dd1d467522421b424d`.
  The decoded stored bytes matched exactly. The full-resolution PNG remains the download asset.
- Add `scripts/gmail_delivery.py` and seven regression tests. The verifier checks stored visible
  text and canonical link targets, exact attachment bytes, recipient, subject and DRAFT/no SENT.
  CSS removal and Google's link wrapper are expected transport changes, not permission to lose
  editorial copy. The saved routine now invokes this path and allows only one delivery repair.

## Artwork and rotation

The cover shows paper application cards entering a brass verification gate, with a rejected card
falling below the queue. Its headline is **Verification comes first**. Three depicted elements
bind to sourced dossier claims. The full-size image and 300-pixel review thumbnail were inspected.
The art gate checked nine historical covers. The final style metadata describes paper relief and
cut paper; the pixels did not change when those descriptive labels were corrected.

The rotation engine inspects the last fourteen days and at least three previous covers, refuses
repeated styles and compositions, requires three changed visual dimensions, and compares image
structure so recoloring alone cannot pass. It reduces repetition; every actual new cover still
requires visual review and a story-specific renderer.

## Delivery and limits

The proven stored attachment is a small review preview. Full-resolution image SHA-256 is
`bb7169e90d28e7de8e93dff9bf3f8026f66fb952daafd388bf3a7475d71121b4`, 1,015,086 bytes.
The earlier corrected artifact URL at `3c47bdf5265be45d6c984af4bf278d8a228caf02` independently
returned HTTP 200, image/png, and identical bytes. The final artifact URL below was independently
fetched again with the same successful response and byte match.

Local Mac validation of all 55 tests found four pre-existing golden-render differences in two
tests; it is not reported as a full local pass. That interpreter used Python 3.14.7, Pillow 12.3.0,
numpy 2.5.2 and FreeType 2.14.3, unlike the tested cloud renderer. The seven new delivery tests,
thirteen pipeline tests and configuration checks passed locally. No repository CI is configured.
The pinned dependency environment also retained those four Mac fixture differences: its Pillow
uses zlib-ng and lacks RAQM, unlike the cloud's zlib 1.3 and RAQM 0.10.5. Matching Python package
versions does not make those native renderers identical. Production validation is the Linux cloud
suite; no pixel-comparison gate was weakened to make the Mac fixtures pass.

The saved schedule remains Wednesday at 4:04 AM Eastern. Its thin instructions fetch
`codex/texas-desk-claude-2026-10-09`; main does not need to be merged for that selected execution
path. The legacy Codex schedule remains paused. The cloud environment retains its reviewed
public-host allowlist, Gmail connector and no new credentials. Auto-fix PRs remains off.

The fresh session displayed High effort despite the medium environment and project settings.
This test manually changed the current session control to Medium and verified that control.
Future automatic launches at Medium remain unproven because the routine editor exposes no
effort control. A later UI read displayed Max; consistent serving effort remains unverified.
Account-wide subscription percentages and context occupancy are not run cost.

## Completed profile delivery

The final artifact commit is `e9ed3b431dbcd85affd35c4d3fbf488c9277c249` on
`codex/texas-desk-2026-10-09-3`, with [draft PR 12](https://github.com/Talonsturgill/linkedin-texas-ai-desk/pull/12).
The [full cover](https://raw.githubusercontent.com/Talonsturgill/linkedin-texas-ai-desk/e9ed3b431dbcd85affd35c4d3fbf488c9277c249/out/post_image.png)
is commit-pinned. The final post has 424 body words and a 207-character hook. Its score remains
8.02 against 8.0; the narrow margin is editorial judgment, not an inflated post-repair score.

Gmail transport required additional engineering iterations. Omitting the attachment field really
does remove the stored attachment. Omitting body fields during an attachment-only update preserves
the existing body. After a long-context sequence failed to copy the base64 accurately, the session
was compacted from 543.6k context to 50.9k. The next attachment-only write succeeded on its first
attempt. This is one observed recovery, not a guaranteed success rate for binary copying.

The successful final RAW readback was extracted directly from this session's real JSONL tool
result. `gmail_delivery.py verify` returned `ok: true` with no errors: the complete generated
visible body, required link targets, exact subject, connected recipient, DRAFT/no SENT, and exact
2,410-byte preview all matched. No RAW content or private identifiers were copied to public files.

At release `18610ddd60b2d1bec9c4f7eb2500cb771a23ae23`, Claude ran `art_smoke.py`,
`check_config.py`, and all 58 tests in an isolated ignored release checkout. All passed; the full
suite took 142.3 seconds. It used Python 3.11.17, Pillow 12.3.0, numpy 2.4.6 and PyYAML 6.0.1.

The reusable transcript extractor was then integrated into release
`b8991ce66feaa143fa24c56a94eee312e8f22d18`. Five focused extractor tests pass locally,
including rejection of stale evidence after a later failed read and owner-only output permissions.
The delivery reference now gives the exact extraction commands and the proven attachment-only
repair path. A final combined cloud check and fresh Gmail readback follow in the verification receipt.

The release uses Haiku, one editor, bounded discovery, compact source packets, deterministic
validation, small attachment payloads and no image-generation API. A content-only repair can reuse
the same run's passing unit suite when no runtime inputs changed. The source ledger records 19
of 24 searches and 12 of 24 fetch attempts. Engineering retries and test runs were additional;
do not use this assisted debugging session as an ordinary-run price forecast.

No email was sent, LinkedIn post published, main branch pushed, or PR merged. Public reports omit
mailbox addresses, private draft identifiers, RAW MIME and connector payloads.

## Final combined verification

Release `b8991ce66feaa143fa24c56a94eee312e8f22d18` passed all **63 cloud tests** in
138.690 seconds, exit 0. Artwork smoke and configuration checks also passed. One fresh Gmail RAW
read was extracted with that exact release's stricter helper, and the stored-MIME verifier again
returned `ok: true`, no errors, DRAFT only and no SENT. No further Gmail writes followed.

The public-safe [machine receipt](final_cloud_verification_2026-10-09.json) was pushed on the
artifact branch in commit `8122908c47f441a5b5d7579f62951fa03cfd6efb`. It records the tested release,
commands, true exit status, test count, image hashes and draft-only result. The final release
adds this report and quieter routine test output on top of the tested runtime; it changes no
renderer, validator or delivery code after that pass.

Actual session telemetry contained 165 unique assistant message IDs across 476 usage records,
all labelled `claude-haiku-5-5`. Taking the maximum per token field per message ID produced
332 input tokens, 269,154 output tokens, 609,539 cache-write tokens and 41,883,318 cache-read tokens.
These figures cover the long engineering session, including failed transfers and revisions.
They are not billed dollars, a recurring-run estimate, or a measured before/after saving.

The earlier no-target and needs-attention drafts from separate test paths were preserved. The
completed profile is the exact-subject October 9th Texas Desk Draft; its latest stored content
and attached preview passed the fresh check above. All PRs remain drafts and no merge occurred.
