"""Export all text for translation as a simple format."""
import json

TRANSLATION_FILE = r"C:\Users\gorigamia\Desktop\game\translation.json"

with open(TRANSLATION_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Export unique entries only (ch52_g, skip ch52_g50 duplicates)
for key in sorted(data["files"].keys()):
    if "ch52_g50" in key:
        continue
    fdata = data["files"][key]
    if fdata["type"] == "AFS_TEXT":
        continue  # Skip CTL_TEXT for now
    
    tgt = fdata.get("target_file", "?")
    print(f"FILE:{key}|TARGET:{tgt}")
    for entry in fdata["entries"]:
        eid = entry["id"]
        lines = entry["original"]
        print(f"  [{eid}] " + " | ".join(lines))
    print()
