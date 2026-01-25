# Final Metrics Display Templates

Display these at the end of the seeding process (Step 6).

---

## Prepare-Only Mode

Use this template when `--prepare-only` flag was set (no database seeding):

```
╔══════════════════════════════════════════════════════════════╗
║           OBSERVATORY VALIDATION COMPLETE                    ║
║                  (--prepare-only mode)                       ║
╠══════════════════════════════════════════════════════════════╣
║  DISCOVERY                                                   ║
║    Total from Wikidata:        {discovered}                  ║
║    Already in JSON:            {duplicates}                  ║
║    New to process:             {new_count}                   ║
║                                                              ║
║  IMAGE VALIDATION                                            ║
║    Sub-agent batches:          {batch_count}                 ║
║    Primary images accepted:    {primary_accepted}            ║
║    Fallback URLs used:         {fallback_used}               ║
║    No valid image found:       {no_valid_image}              ║
║                                                              ║
║  WEBSITE VALIDATION                                          ║
║    Valid from Wikidata:        {wikidata_valid}              ║
║    Soft 404s rejected:         {soft_404_rejected}           ║
║    Found via search:           {search_found}                ║
║                                                              ║
║  RESULTS                                                     ║
║    Observatories validated:    {total_validated}             ║
║    Acceptance rate:            {acceptance_rate}%            ║
║    Added to JSON:              {added_to_json}               ║
║    Total in JSON:              {total_in_json}               ║
║                                                              ║
║  NEXT STEP                                                   ║
║    Commit validated_observatories.json, then on production:  ║
║    python manage.py seed_locations --type=observatory        ║
╚══════════════════════════════════════════════════════════════╝
```

---

## Full Seeding Mode

Use this template when full seeding was performed (database updated):

```
╔══════════════════════════════════════════════════════════════╗
║              OBSERVATORY SEEDING COMPLETE                    ║
╠══════════════════════════════════════════════════════════════╣
║  DISCOVERY                                                   ║
║    Total from Wikidata:        {discovered}                  ║
║    Already in JSON:            {duplicates}                  ║
║    New to process:             {new_count}                   ║
║                                                              ║
║  IMAGE VALIDATION                                            ║
║    Sub-agent batches:          {batch_count}                 ║
║    Primary images accepted:    {primary_accepted}            ║
║    Fallback URLs used:         {fallback_used}               ║
║    No valid image found:       {no_valid_image}              ║
║                                                              ║
║  WEBSITE VALIDATION                                          ║
║    Valid from Wikidata:        {wikidata_valid}              ║
║    Soft 404s rejected:         {soft_404_rejected}           ║
║    Found via search:           {search_found}                ║
║                                                              ║
║  FINAL RESULTS                                               ║
║    Observatories validated:    {total_validated}             ║
║    Acceptance rate:            {acceptance_rate}%            ║
║    Locations seeded to DB:     {seeded_count}                ║
╚══════════════════════════════════════════════════════════════╝
```

---

## Variable Definitions

| Variable | Source |
|----------|--------|
| `{discovered}` | Count from discovery command output |
| `{duplicates}` | Count of observatories already in validated_observatories.json |
| `{new_count}` | discovered - duplicates |
| `{batch_count}` | Number of batch_*.json files created |
| `{primary_accepted}` | Observatories where original image_url was accepted |
| `{fallback_used}` | Observatories where fallback image was used |
| `{no_valid_image}` | Observatories with null in validated (rejected, no fallback) |
| `{wikidata_valid}` | Websites from Wikidata that passed Tier 1 validation |
| `{soft_404_rejected}` | Websites rejected due to soft 404 detection |
| `{search_found}` | Sum of websites_found across all checkpoints |
| `{total_validated}` | primary_accepted + fallback_used |
| `{acceptance_rate}` | (total_validated / new_count) * 100 |
| `{added_to_json}` | New entries added to validated_observatories.json |
| `{total_in_json}` | Total entries in validated_observatories.json after merge |
| `{seeded_count}` | Locations created in database (from seed command output) |
