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
    """Hash the canonical URL to a fixed-length hex string."""
    h = hashlib.sha256(url.encode('utf-8')).hexdigest()
    return h[:16]  # first 16 chars

# --- Crawl a single topic ---
def crawl_topic(topic: str, seeds: list, max_pages: int, master_file: str, output_dir: str, mapping: dict):
    topic_dir = os.path.join(output_dir, topic)
    os.makedirs(topic_dir, exist_ok=True)

    session = requests.Session()
    urls_to_visit = list(seeds)
    seen = set()
    count = 0

    while urls_to_visit and count < max_pages:
        raw_url = urls_to_visit.pop(0).strip()
        if raw_url in seen:
            continue
        seen.add(raw_url)

        # percent-encode, parse, and canonicalize (drop query/fragment)
        safe_url = requote_uri(raw_url)
        parsed = urlparse(safe_url)
        canonical = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        canonical = canonical.rstrip('/')
        # skip empty or login pages
        if not canonical or any(x in canonical.lower() for x in ['signin', 'login']):
            continue

        try:
            resp = session.get(canonical, headers=hdrs, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"Error fetching {canonical}: {e}")
            continue

        # record in master list
        with open(master_file, "a", encoding="utf-8") as mf:
            mf.write(canonical + "\n")

        # extract only alphabetic words (English + Arabic)
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator=" ")
        raw_tokens = re.findall(r"\b\w+\b", text, flags=re.UNICODE)
        tokens = [t for t in raw_tokens if t.isalpha()]

        # encode canonical URL for filename
        safe_name = encode_name(canonical)
        mapping[safe_name] = canonical
        vocab_filename = f"vocab_{safe_name}.txt"
        vocab_path = os.path.join(topic_dir, vocab_filename)

        os.makedirs(os.path.dirname(vocab_path), exist_ok=True)
        with open(vocab_path, "w", encoding="utf-8") as vf:
            vf.write(' '.join(tokens))

        # discover same-domain links
        base = seeds[0]
        for link in soup.find_all("a", href=True):
            abs_url = urljoin(canonical, link["href"])
            if abs_url.startswith(seeds[0]) and abs_url not in seen:
                urls_to_visit.append(abs_url)

        count += 1
        print(f"[{topic}] Crawled {count}/{max_pages}: {canonical}")

# --- Main script ---
def main():
    parser = argparse.ArgumentParser(
        description="Local multi-topic crawler with hashed filenames and canonical URLs"
    )
    parser.add_argument(
        "--seeds-dir", required=True,
        help="Directory containing per-topic seed files (*.txt)"
    )
    parser.add_argument(
        "--max-pages", type=int, default=100,
        help="Max pages to crawl per topic"
    )
    parser.add_argument(
        "--output-dir", default="output",
        help="Root directory to store master URLs, mapping, and topic data"
    )
    args = parser.parse_args()

    # prepare output
    os.makedirs(args.output_dir, exist_ok=True)
    master_file = os.path.join(args.output_dir, "all_urls_master.txt")
    open(master_file, "w").close()

    # load topics
    topics = {}
    for fname in os.listdir(args.seeds_dir):
        if fname.endswith('.txt'):
            topic = os.path.splitext(fname)[0]
            path = os.path.join(args.seeds_dir, fname)
            with open(path, 'r', encoding='utf-8') as f:
                seeds = [line.strip() for line in f if line.strip()]
            if seeds:
                topics[topic] = seeds
    if not topics:
        print(f"No seed files in {args.seeds_dir}")
        return

    mapping = {}
    for topic, seeds in topics.items():
        print(f"Starting topic '{topic}' with seeds: {seeds}")
        crawl_topic(topic, seeds, args.max_pages, master_file, args.output_dir, mapping)

    # save mapping
    mapping_path = os.path.join(args.output_dir, "url_mapping.json")
    with open(mapping_path, 'w', encoding='utf-8') as mp:
        json.dump(mapping, mp, indent=2)

    print(f"Crawling complete. Master URLs: {master_file}")
    print(f"URL mapping file: {mapping_path}")

if __name__ == "__main__":
    main()
