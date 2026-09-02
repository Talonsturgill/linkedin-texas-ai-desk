# Texas Desk dossier contract

Write `out/desk_dossier.json` as UTF-8 JSON. A successful profile uses this shape:

```json
{
  "schema_version": 1,
  "run_date": "YYYY-MM-DD",
  "window_days": 60,
  "no_target_this_cycle": false,
  "selected_subject": {
    "full_name": "Full Name",
    "role": "Current public role",
    "organization": "Organization",
    "role_category": "founder|operator|public|research",
    "texas_tie": "Specific place, office, project, or affected Texas jurisdiction",
    "place_label": "TRAVIS COUNTY",
    "coordinates": "30°16′N · 97°45′W",
    "role_source": {"url": "https://...", "title": "...", "publisher": "..."},
    "verbatim_quotes": [
      {"text": "Exact source text", "url": "https://...", "context": "..."}
    ]
  },
  "selected_decision": {
    "what_happened": "Exact, source-grounded description",
    "decision_anchor": "Short exact phrase that must appear in the post",
    "date": "YYYY-MM-DD",
    "owner_evidence": "Why this person made or owns the decision",
    "alternative_available": "The real alternative they could have chosen",
    "ai_nexus": "How this governs, funds, builds, procures, deploys, or constrains AI or its infrastructure",
    "texas_consequence": "Named affected Texans, entity, sector, and timeframe",
    "next_check": "Specific future filing, vote, milestone, result, or date to watch",
    "public_policy_or_electoral": false,
    "primary_source": {
      "url": "https://...",
      "title": "...",
      "publisher": "...",
      "published_at": "YYYY-MM-DD",
      "source_type": "primary",
      "claims_supported": ["..."]
    },
    "corroborating_sources": [
      {
        "url": "https://...",
        "title": "...",
        "publisher": "...",
        "published_at": "YYYY-MM-DD",
        "source_type": "independent_reporting",
        "independent_of_subject": true,
        "claims_supported": ["..."]
      }
    ]
  },
  "analysis": {
    "editorial_mode": "execution_assessment|neutral_accountability",
    "assessment": "sharp|mixed|weak|not_applicable",
    "evidence_for": ["..."],
    "evidence_against": ["..."],
    "structural_read": "...",
    "forward_implication": "...",
    "conflict_screen": "clear"
  },
  "required_post_phrases": ["Full Name", "decision anchor"],
  "verified_facts": [
    {"claim": "...", "source_urls": ["https://..."]}
  ],
  "gate_results": {
    "named_subject": true,
    "recent_decision": true,
    "decision_owner": true,
    "texas_ai_consequence": true,
    "primary_source": true,
    "independent_corroboration": true,
    "position_or_accountability_read": true,
    "not_recent_repeat": true,
    "conflict_clear": true,
    "political_neutrality": true
  },
  "dropped_candidates": []
}
```

For a no-target run, set `no_target_this_cycle` to `true`, omit `selected_subject` and
`selected_decision`, and include both `_validation_note` and a nonempty `dropped_candidates` array.
Each dropped candidate uses this shape:

```json
{
  "subject": "Full name or best available candidate label",
  "decision": "Proposed decision",
  "drop_reason": "Concrete failed gate",
  "sources": [
    {"url": "https://...", "title": "...", "publisher": "..."}
  ]
}
```

Additional fields are allowed. Do not remove or rename required fields. URLs must be fetched in
the current run. A search-result snippet is not a fetched source.
