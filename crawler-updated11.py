#!/usr/bin/env python3
import os
import re
import argparse
import requests
import hashlib
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from requests.utils import requote_uri

# --- HTTP headers to mimic a real browser ---
hdrs = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# --- Utility: shorten and hash URL for safe filenames ---
def encode_name(url: str) -> str:
    h = hashlib.sha256(url.encode('utf-8')).hexdigest()
    return h[:16]

# --- Crawl a single seed under a topic ---
def crawl_seed(topic: str, seed: str, max_pages: int, master_file: str,
               output_dir: str, mapping: dict, visited: set):
    topic_dir = os.path.join(output_dir, topic)
    os.makedirs(topic_dir, exist_ok=True)

    session = requests.Session()
    queue = [seed]
    seen = set()
    count = 0
    base = seed.rstrip('/')

    while queue and count < max_pages:
        raw_url = queue.pop(0).strip()
        if raw_url in visited or raw_url in seen:
            continue
        seen.add(raw_url)

        safe_url = requote_uri(raw_url)
        parsed = urlparse(safe_url)
        canonical = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip('/')
        if not canonical or any(x in canonical.lower() for x in ['signin', 'login']):
            continue

        try:
            resp = session.get(canonical, headers=hdrs, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"Error fetching {canonical}: {e}")
            continue

        visited.add(canonical)
        with open(master_file, "a", encoding="utf-8") as mf:
            mf.write(canonical + "\n")

        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator=" ")
        raw_tokens = re.findall(r"\b\w+\b", text, flags=re.UNICODE)
        tokens = [t for t in raw_tokens if t.isalpha()]

        safe_name = encode_name(canonical)
        mapping[safe_name] = canonical
        vocab_path = os.path.join(topic_dir, f"vocab_{safe_name}.txt")
        os.makedirs(os.path.dirname(vocab_path), exist_ok=True)
        with open(vocab_path, "w", encoding="utf-8") as vf:
            vf.write(' '.join(tokens))

        for link in soup.find_all("a", href=True):
            abs_url = urljoin(canonical, link["href"])
            if abs_url.startswith(base) and abs_url not in visited and abs_url not in seen:
                queue.append(abs_url)

        count += 1
        print(f"[{topic}] seed {seed} crawled {count}/{max_pages}: {canonical}")

# --- Main script ---
def main():
    parser = argparse.ArgumentParser(
        description="Multi-topic, multi-seed crawler with resume capability"
    )
    parser.add_argument("--seeds-dir", required=True,
                        help="Directory containing per-topic seed files (*.txt)")
    parser.add_argument("--max-pages", type=int, default=100,
                        help="Max pages to crawl per seed URL")
    parser.add_argument("--output-dir", default="output",
                        help="Root directory to store outputs")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    master_file = os.path.join(args.output_dir, "all_urls_master.txt")

    # Load existing visited URLs
    visited = set()
    if os.path.exists(master_file):
        with open(master_file, 'r', encoding='utf-8') as mf:
            for line in mf:
                visited.add(line.strip())
    else:
        open(master_file, 'w').close()

    # Load existing mapping JSON and merge
    mapping_path = os.path.join(args.output_dir, "url_mapping.json")
    if os.path.exists(mapping_path):
        with open(mapping_path, 'r', encoding='utf-8') as mp:
            mapping = json.load(mp)
    else:
        mapping = {}

    # Load seeds by topic
    topics = {}
    for fname in os.listdir(args.seeds_dir):
        if fname.endswith('.txt'):
            topic = os.path.splitext(fname)[0]
            path = os.path.join(args.seeds_dir, fname)
            with open(path, 'r', encoding='utf-8') as f:
                seeds = [line.strip() for line in f if line.strip()]
            if seeds:
                topics[topic] = seeds

    for topic, seeds in topics.items():
        print(f"Starting topic '{topic}'")
        for seed in seeds:
            print(f"  Crawling seed: {seed}")
            crawl_seed(topic, seed, args.max_pages, master_file,
                       args.output_dir, mapping, visited)

    # Save mapping (merged with previous runs)
    with open(mapping_path, 'w', encoding='utf-8') as mp:
        json.dump(mapping, mp, indent=2)

    print("Crawling complete.")

if __name__ == "__main__":
    main()
