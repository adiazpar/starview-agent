#!/usr/bin/env python3
"""
Normalize checkpoint files from sub-agents to canonical format.

Usage:
    python normalize_checkpoint.py <checkpoint_path> <expected_batch_num>

Or import and use directly:
    from normalize_checkpoint import normalize_checkpoint
"""

import json
import sys


def normalize_checkpoint(data, expected_batch_num):
    """
    Normalize any sub-agent output format to canonical structure.

    Canonical format:
    {
        "batch_num": N,
        "validated": { "slug": "url" or null },
        "websites_found": { "slug": "url" },
        "rejection_notes": { "slug": "reason" }
    }

    Handles these input formats:
    - Canonical: {"batch_num": N, "validated": {...}}
    - Old format: {"batch_num": N, "results": [...]}
    - Array format: [{slug, image_url, image_status}, ...]
    """
    normalized = {
        "batch_num": expected_batch_num,
        "validated": {},
        "websites_found": {},
        "rejection_notes": {}
    }

    # Already canonical format
    if isinstance(data, dict) and "validated" in data and isinstance(data["validated"], dict):
        normalized["validated"] = data["validated"]
        normalized["websites_found"] = data.get("websites_found", {})
        normalized["rejection_notes"] = data.get("rejection_notes", {})
        return normalized

    # Old format: {"batch_num": N, "results": [...]}
    if isinstance(data, dict) and "results" in data and isinstance(data["results"], list):
        for item in data["results"]:
            slug = item.get("slug")
            if not slug:
                continue
            # Get final_url (may be named differently)
            final_url = item.get("final_url") or item.get("image_url") or item.get("url")
            if item.get("accepted") == False or item.get("image_status") == "rejected":
                final_url = None
                # Capture rejection reason if available
                if item.get("rejection_reason") or item.get("reason"):
                    normalized["rejection_notes"][slug] = item.get("rejection_reason") or item.get("reason")
            normalized["validated"][slug] = final_url
            # Check for website additions
            if item.get("type_metadata", {}).get("website"):
                normalized["websites_found"][slug] = item["type_metadata"]["website"]
        return normalized

    # Array format: [{slug, image_url, image_status, ...}, ...]
    if isinstance(data, list):
        for item in data:
            slug = item.get("slug")
            if not slug:
                continue
            # Determine if accepted
            is_accepted = (
                item.get("image_status") == "accepted" or
                item.get("accepted") == True or
                (item.get("image_url") and "rejected" not in str(item.get("image_status", "")))
            )
            final_url = item.get("image_url") if is_accepted else None
            normalized["validated"][slug] = final_url
            # Capture rejection reason if rejected
            if not is_accepted and (item.get("rejection_reason") or item.get("reason")):
                normalized["rejection_notes"][slug] = item.get("rejection_reason") or item.get("reason")
            # Check for website
            if item.get("type_metadata", {}).get("website"):
                normalized["websites_found"][slug] = item["type_metadata"]["website"]
        return normalized

    raise ValueError(f"Unrecognized checkpoint format: {list(data.keys()) if isinstance(data, dict) else type(data)}")


def normalize_file(checkpoint_path, expected_batch_num):
    """Load, normalize, and save a checkpoint file."""
    with open(checkpoint_path) as f:
        data = json.load(f)

    normalized = normalize_checkpoint(data, expected_batch_num)

    with open(checkpoint_path, 'w') as f:
        json.dump(normalized, f, indent=2)

    return normalized


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python normalize_checkpoint.py <checkpoint_path> <batch_num>")
        sys.exit(1)

    checkpoint_path = sys.argv[1]
    batch_num = int(sys.argv[2])

    result = normalize_file(checkpoint_path, batch_num)
    rejected_count = len(result.get('rejection_notes', {}))
    msg = f"Normalized: {len(result['validated'])} observatories, {len(result['websites_found'])} websites found"
    if rejected_count:
        msg += f", {rejected_count} rejection notes"
    print(msg)
