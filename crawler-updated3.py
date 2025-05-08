#!/usr/bin/env python3
import os
import re
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


def parse_args():
    parser = argparse.ArgumentParser(
        description="Local Web Crawler: generates a master URL list and per-page vocab files"
    )
    parser.add_argument(
        "--seeds-file", required=True,
        help="Path to a file listing seed URLs, one per line"
    )
    parser.add_argument(
        "--max-pages", type=int, default=100,
        help="Maximum number of pages to crawl"
    )
    parser.add_argument(
        "--output-dir", default="output",
        help="Directory to store output files"
    )
    return parser.parse_args()


def slugify(url: str) -> str:
    """Convert URL path to a safe filename slug."""
    path = urlparse(url).path.strip("/")
    slug = re.sub(r"[^a-zA-Z0-9]", "_", path)
    return slug or "root"


def crawl(seeds, max_pages, output_dir):
    # Prepare output
    os.makedirs(output_dir, exist_ok=True)
    topic = os.path.splitext(os.path.basename(args.seeds_file))[0]
    master_path = os.path.join(output_dir, f"{topic}_all_urls_master.txt")
    open(master_path, "w").close()

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

        # Append to master URL list
        with open(master_path, "a", encoding="utf-8") as mf:
            mf.write(url + "\n")

        # Parse and extract vocabulary
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator=" ")
        tokens = re.findall(r"\b\w+\b", text.lower())
        vocab = sorted(set(tokens))

        # Write vocab to file
        safe_name = slugify(url)
        vocab_filename = f"vocab_{safe_name}.txt"
        vocab_path = os.path.join(output_dir, vocab_filename)
        with open(vocab_path, "w", encoding="utf-8") as vf:
            vf.write("\n".join(vocab))

        # Discover new URLs from same domain
        base = seeds[0]
        for link in soup.find_all("a", href=True):
            abs_url = urljoin(url, link["href"])
            if abs_url.startswith(base) and abs_url not in seen:
                urls_to_visit.append(abs_url)

        count += 1
        print(f"Crawled ({count}/{max_pages}): {url}")

    print(f"Done! Crawled {count} pages. Master list at: {master_path}")


def main():
    global args
    args = parse_args()
    # Load seeds
    with open(args.seeds_file, "r", encoding="utf-8") as sf:
        seeds = [line.strip() for line in sf if line.strip()]

    crawl(seeds=seeds, max_pages=args.max_pages, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
