#!/usr/bin/env python3
import os
import re
import argparse
import requests
import base64
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# --- Utility functions for encoding/decoding URL to safe filenames ---
def encode_name(url: str) -> str:
    """URL-safe Base64 encode without padding for filename."""
    b64 = base64.urlsafe_b64encode(url.encode('utf-8')).decode('ascii')
    return b64.rstrip('=')  # remove padding

def decode_name(name: str) -> str:
    """Decode filename-safe Base64 string back to URL."""
    padding = '=' * (-len(name) % 4)
    return base64.urlsafe_b64decode((name + padding).encode('ascii')).decode('utf-8')

# --- Crawl a single topic ---
def crawl_topic(topic: str, seeds: list, max_pages: int, master_file: str, output_dir: str, mapping: dict):
    topic_dir = os.path.join(output_dir, topic)
    os.makedirs(topic_dir, exist_ok=True)

    session = requests.Session()
    urls_to_visit = list(seeds)
    seen = set()
    count = 0

    while urls_to_visit and count < max_pages:
        url = urls_to_visit.pop(0)
        if url in seen:
            continue
        seen.add(url)

        try:
            resp = session.get(url, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            continue

        # Append to global master URL file
        with open(master_file, "a", encoding="utf-8") as mf:
            mf.write(url + "\n")

        # Parse and extract vocabulary (only alphabetic words, preserve duplicates)
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator=" ")
        # Keep only letter sequences, drop pure numbers
        # match runs of either ASCII letters or Arabic letters
        tokens = re.findall(r"[\u0600-\u06FF]+|[A-Za-z]+", text)
        #another option to keep both Arabic and English letters
        # raw = re.findall(r"\b\w+\b", text, flags=re.UNICODE)
        # tokens = [t for t in raw if t.isalpha()]

        # Encode URL for filename and record mapping
        safe_name = encode_name(url)
        mapping[safe_name] = url
        vocab_filename = f"vocab_{safe_name}.txt"
        vocab_path = os.path.join(topic_dir, vocab_filename)

        # Write all tokens on a single line separated by spaces
        # Ensure the folder exists before writing
        os.makedirs(os.path.dirname(vocab_path), exist_ok=True)

        # Write all tokens on a single line separated by spaces
        with open(vocab_path, "w", encoding="utf-8") as vf:
            vf.write(' '.join(tokens))


        # Discover same-domain links and enqueue
        base = seeds[0]
        for link in soup.find_all("a", href=True):
            abs_url = urljoin(url, link["href"])
            if abs_url.startswith(base) and abs_url not in seen:
                urls_to_visit.append(abs_url)

        count += 1
        print(f"[{topic}] Crawled {count}/{max_pages}: {url}")

# --- Main script ---
def main():
    parser = argparse.ArgumentParser(
        description="Local multi-topic crawler with URL->filename mapping"
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

    # Prepare output and master URL list
    os.makedirs(args.output_dir, exist_ok=True)
    master_file = os.path.join(args.output_dir, "all_urls_master.txt")
    open(master_file, "w").close()

    # Load topics dynamically
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

    # Global mapping from safe_name to URL
    mapping = {}

    # Crawl each topic
    for topic, seeds in topics.items():
        print(f"Starting topic '{topic}' with seeds: {seeds}")
        crawl_topic(topic, seeds, args.max_pages, master_file, args.output_dir, mapping)

    # Write mapping file once
    mapping_path = os.path.join(args.output_dir, "url_mapping.json")
    with open(mapping_path, 'w', encoding='utf-8') as mp:
        json.dump(mapping, mp, indent=2)

    print(f"Crawling complete. Master URLs: {master_file}")
    print(f"URL mapping file: {mapping_path}")

if __name__ == "__main__":
    main()
