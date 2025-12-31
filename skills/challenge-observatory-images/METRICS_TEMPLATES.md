# Challenge Observatory Images - Metrics Templates

Display templates for the challenge skill's final summary.

---

## Main Template

Use this template after Step 4 (Consolidate Checkpoints):

```
╔═══════════════════════════════════════════════════════════╗
║           OBSERVATORY CHALLENGE COMPLETE                  ║
╠═══════════════════════════════════════════════════════════╣
║ INPUT                                                     ║
║   Rejected observatories loaded:               {rejected} ║
║   Batches processed:                            {batches} ║
║                                                           ║
║ RESEARCH RESULTS                                          ║
║   Challenged & Accepted:                       {accepted} ║
║   Confirmed Rejected:                      {still_reject} ║
║   Challenge success rate:                  {success_rate} ║
║                                                           ║
║ EVIDENCE COLLECTED                                        ║
║   Total confirming images found:              {evidence}  ║
║   Average images per accepted:                   {avg}    ║
║                                                           ║
║ OUTPUT                                                    ║
║   File: seed_data/challenged_observatories.json           ║
╚═══════════════════════════════════════════════════════════╝
```

---

## Variable Definitions

| Variable | Source | Description |
|----------|--------|-------------|
| `{rejected}` | `len(rejected_data['observatories'])` | Total rejected observatories loaded |
| `{batches}` | `len(batch_files)` | Number of sub-agent batches processed |
| `{accepted}` | `len(challenged_accepted)` | Observatories that passed the 3-image challenge |
| `{still_reject}` | `len(confirmed_rejected)` | Observatories that remain rejected |
| `{success_rate}` | `accepted / (accepted + still_reject) * 100` | Percentage successfully challenged |
| `{evidence}` | Sum of all `challenge_evidence` entries | Total confirming images collected |
| `{avg}` | `evidence / accepted` | Average evidence per accepted observatory |

---

## Calculating Variables

```python
# After consolidation
rejected = len(data['observatories'])  # from rejected_observatories.json
batches = len(batch_files)
accepted = len(challenged_accepted)
still_reject = len(confirmed_rejected)

total = accepted + still_reject
success_rate = f"{accepted / total * 100:.1f}%" if total > 0 else "N/A"

evidence = sum(len(obs.get('challenge_evidence', [])) for obs in challenged_accepted)
avg = f"{evidence / accepted:.1f}" if accepted > 0 else "N/A"
```

---

## Accepted Observatory List

After the main summary, optionally list the successfully challenged observatories:

```
SUCCESSFULLY CHALLENGED:
  1. {name} ({country})
     Evidence: {n} confirming images
  2. {name} ({country})
     Evidence: {n} confirming images
  ...
```

---

## Next Steps Box

Always display after the metrics:

```
╔═══════════════════════════════════════════════════════════╗
║ NEXT STEPS                                                ║
╠═══════════════════════════════════════════════════════════╣
║ 1. Review: seed_data/challenged_observatories.json        ║
║ 2. Verify the challenge_evidence images are correct       ║
║ 3. Merge accepted into validated_observatories.json:      ║
║                                                           ║
║    djvenv/bin/python -c "                                 ║
║    import json                                            ║
║    from observatory_seeder import \\                       ║
║        merge_validated_observatories                      ║
║                                                           ║
║    with open('seed_data/challenged_observatories.json')   ║
║        as f: data = json.load(f)                          ║
║                                                           ║
║    to_merge = [{k:v for k,v in o.items()                  ║
║        if k != 'challenge_evidence'}                      ║
║        for o in data['challenged_accepted']]              ║
║                                                           ║
║    path, total, added = merge_validated_observatories(    ║
║        to_merge)                                          ║
║    print(f'Added {added}, total now {total}')             ║
║    "                                                      ║
╚═══════════════════════════════════════════════════════════╝
```

---

## Empty Results Template

If no observatories were challenged (file empty or all skipped):

```
╔═══════════════════════════════════════════════════════════╗
║           OBSERVATORY CHALLENGE - NO RESULTS              ║
╠═══════════════════════════════════════════════════════════╣
║ No rejected observatories were found to challenge.        ║
║                                                           ║
║ This could mean:                                          ║
║   • rejected_observatories.json is empty                  ║
║   • All observatories were accepted in seed-observatories ║
║   • --offset skipped all available entries                ║
╚═══════════════════════════════════════════════════════════╝
```

---

## Partial Success Template

When some batches failed:

```
╔═══════════════════════════════════════════════════════════╗
║      OBSERVATORY CHALLENGE - PARTIAL COMPLETION           ║
╠═══════════════════════════════════════════════════════════╣
║ WARNING: {missing} of {total} batches did not complete    ║
║                                                           ║
║ COMPLETED RESULTS                                         ║
║   ...                                                     ║
║                                                           ║
║ TO RETRY MISSING BATCHES:                                 ║
║   Re-run /challenge-observatory-images and choose Resume  ║
╚═══════════════════════════════════════════════════════════╝
```
