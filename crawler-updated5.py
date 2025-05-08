#!/usr/bin/env python3
import os
import re
import requests
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# --- Utility function to create safe filenames ---
def slugify(url: str) -> str:
    path = urlparse(url).path.strip("/")
    slug = re.sub(r"[^a-zA-Z0-9]", "_", path)
    return slug or "root"

# --- Main crawl function per topic ---
def crawl_topic(topic: str, seeds: list, max_pages: int, master_file: str, output_dir: str):
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

        # Parse and extract vocabulary
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator=" ")
        tokens = re.findall(r"\b\w+\b", text.lower())
        vocab = sorted(set(tokens))

        # Write vocab file in topic folder
        safe_name = slugify(url)
        vocab_path = os.path.join(topic_dir, f"vocab_{safe_name}.txt")
        with open(vocab_path, "w", encoding="utf-8") as vf:
            vf.write("\n".join(vocab))

        # Discover same-domain links and enqueue
        base = seeds[0]
        for link in soup.find_all("a", href=True):
            abs_url = urljoin(url, link["href"])
            if abs_url.startswith(base) and abs_url not in seen:
                urls_to_visit.append(abs_url)

        count += 1
        print(f"[{topic}] Crawled {count}/{max_pages}: {url}")

# --- Script entrypoint ---
def main():
    parser = argparse.ArgumentParser(
        description="Local multi-topic crawler: dynamic seeds per topic from a directory"
    )
    parser.add_argument(
        "--seeds-dir", required=True,
        help="Path to a directory containing per-topic seed files (*.txt)"
    )
    parser.add_argument(
        "--max-pages", type=int, default=100,
        help="Max pages to crawl per topic"
    )
    parser.add_argument(
        "--output-dir", default="output",
        help="Root directory to store master URLs and topic folders"
    )
    args = parser.parse_args()

    # Prepare root output and master file
    os.makedirs(args.output_dir, exist_ok=True)
    master_file = os.path.join(args.output_dir, "all_urls_master.txt")
    open(master_file, "w").close()

    # Load topics and seeds dynamically from directory
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
        print(f"No seed files found in {args.seeds_dir}. Exiting.")
        return

    # Run crawler for each dynamic topic
    for topic, seeds in topics.items():
        print(f"Starting crawl for topic '{topic}' with seeds: {seeds}")
        crawl_topic(topic, seeds, args.max_pages, master_file, args.output_dir)

    print(f"Crawling complete. Master URL list: {master_file}")

if __name__ == "__main__":
    main()
