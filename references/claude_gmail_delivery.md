# Claude Gmail delivery

The October 9th cloud test proved a real JPEG attachment can survive this connector. It also
proved remote HTML `img` tags were stripped at write time and long model-copied base64 could be
truncated. Use this tested small-preview format from the first write; do not repeat those failed
experiments on each run. No new service, key, OAuth flow, or send endpoint is needed.

1. After the full PNG has passed its visual gate and SHA-pinned public URL check, run:

   ```bash
   python3 scripts/gmail_delivery.py preview --image out/post_image.png \
     --out .local/texas-desk-cover-preview.jpg
   ```

   This creates a 160-square JPEG at quality 25 (20 if needed), at most 4 KiB, and reports its
   source hash, bytes, and preview hash. The actual tested cover used 2,410 bytes. The full
   resolution cover remains the immutable PNG; never substitute this thumbnail for it.

2. Build the ordinary email payload with `--attachment-preview`. This explicitly describes the
   small attachment and full PNG link, and omits CSS the connector would strip. Preserve all
   generated visible text, source links, score, editor note, branch and commit. If supplying a
   plain-text alternative, include the full post and links there too.

3. Deduplicate by the exact date/subject as the master routine requires. Use the connected
   account already verified in preflight. The observed connector create/update inputs include
   `to`, `subject`, `body`, `htmlBody`, and `attachments`. Each attachment takes `content`
   (base64), `filename`, `mimeType`, and `inline`. Use exactly one attachment:
   `texas-desk-cover-preview.jpg`, `image/jpeg`, `inline: false`.

   Prefer a supported exact file-to-tool transfer if the runtime exposes one. The tested current
   connector has no file-path or writable RAW-MIME argument. For its bounded fallback, print the
   preview base64 once, copy the complete string unchanged into `content`, and immediately
   validate readback. Never abbreviate, regenerate, or claim an untransferred string was copied.
   Every update must include the attachment; omitted/empty attachment arrays remove it.

4. Request RAW MIME and metadata for that same draft. Save the actual responses under `.local/`;
   prefer the tool's saved-result file when available. Do not reconstruct expected output or
   fabricate labels. The RAW file may be JSON containing one `raw` field or the base64url field
   itself. The metadata JSON must contain one actual `labels`, `labelIds`, or `label_ids` list.

   ```bash
   python3 scripts/gmail_delivery.py verify \
     --payload .local/gmail_payload.json --raw .local/gmail_raw.json \
     --metadata .local/gmail_readback.json --preview .local/texas-desk-cover-preview.jpg \
     --report .local/gmail_delivery_validation.json
   ```

   Require exit 0. The verifier checks decoded attachment bytes, filename, MIME type, dimensions,
   recipient, subject, DRAFT/no SENT, all visible text and canonical link destinations. It permits
   stripped styles and Google's URL redirect wrapper, observed in the real connector. Raw HTML
   equality would incorrectly reject those transport changes. Missing copy is still rejected.

5. One repair is allowed after the initial write. Reuse the approved image and compact payload;
   do not repeat research, art generation, or the unit suite for an attachment transport retry.
   If repair fails, remove a broken attachment, accurately label the existing draft's delivery
   failure, retain the valid full PNG link, and report needs-attention. Never send. Never expose
   account addresses, draft identifiers, RAW mail, or private payloads in public artifacts.

This attachment path passed once in the cloud test. The byte check is required on every future
run because a language model copying base64 is not a guaranteed binary transport.
