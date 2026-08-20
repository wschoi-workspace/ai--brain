import json

SRC = "/Users/choi_ai/do-better-workspace/10-projects/15-bongeunsa/재구조화/deck-chunks.json"
DST = "/Users/choi_ai/do-better-workspace/10-projects/15-bongeunsa/재구조화/deck-chunks-filtered.json"

with open(SRC, "r", encoding="utf-8") as f:
    data = json.load(f)

matched_keys = [k for k in data.keys() if k.startswith("0.2/") or k.startswith("1.")]
matched_keys_sorted = sorted(matched_keys)

filtered = {k: data[k] for k in matched_keys_sorted}

with open(DST, "w", encoding="utf-8") as f:
    json.dump(filtered, f, ensure_ascii=False, indent=2)

print(f"Total matched keys: {len(matched_keys_sorted)}")
print("Matched keys:")
for k in matched_keys_sorted:
    print(k)
