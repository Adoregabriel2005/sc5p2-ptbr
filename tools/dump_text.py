"""Dump all text entries for translation analysis."""
import json

TRANSLATION_FILE = r"C:\Users\gorigamia\Desktop\game\translation.json"

with open(TRANSLATION_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Only show ch52_g (not ch52_g50 since they're identical)
print("=== Files to translate (ch52_g only) ===\n")
total = 0
total_lines = 0
for key, fdata in data["files"].items():
    if "ch52_g50" in key:
        continue
    n = len(fdata["entries"])
    lines = sum(len(e["original"]) for e in fdata["entries"])
    src = fdata.get("source_file", "?")
    tgt = fdata.get("target_file", "?")
    total += n
    total_lines += lines
    print(f"  {key:35s} {src:20s} -> {tgt:20s}  {n:4d} entries  {lines:4d} lines")

print(f"\nTotal unique entries: {total}")
print(f"Total unique lines: {total_lines}")

# Dump all text for each file
print("\n" + "="*80)
print("=== FULL TEXT DUMP ===")
print("="*80)

for key, fdata in sorted(data["files"].items()):
    if "ch52_g50" in key:
        continue
    print(f"\n--- {key} ({fdata.get('target_file','?')}) ---")
    for entry in fdata["entries"]:
        eid = entry["id"]
        for i, line in enumerate(entry["original"]):
            t = entry["translated"][i] if i < len(entry["translated"]) and entry["translated"][i].strip() else ""
            status = "OK" if t else "  "
            print(f"  [{eid:3d}.{i}] {status} | {line}")
