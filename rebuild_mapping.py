import os, json, hashlib

master = "crawl_output/all_urls_master.txt"
out   = "crawl_output/url_mapping_final.json"

mapping = {}
with open(master, "r", encoding="utf-8") as mf:
    for line in mf:
        url = line.strip()
        key = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        mapping[key] = url

os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as jf:
    json.dump(mapping, jf, indent=2)

print(f"Rebuilt mapping for {len(mapping)} URLs into {out}")
