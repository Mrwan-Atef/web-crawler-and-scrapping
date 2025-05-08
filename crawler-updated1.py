import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Configuration: define your topics and their seed URLs
topics = {
    "electronics": ["https://example.com/electronics/"],
    "books": ["https://example.com/books/"],
    # add more topics as needed
}

# Crawl settings
max_pages_per_topic = 100   # adjust as needed

# Utility: make filesystem-safe names from URLs
def slugify(url):
    return re.sub(r"[^a-zA-Z0-9]", "_", urlparse(url).path.strip("/")) or "root"

# Main crawler function per topic
def crawl_topic(topic, seeds):
    output_dir = os.path.join("output", topic)
    os.makedirs(output_dir, exist_ok=True)

    # Files
    all_urls_path = os.path.join(output_dir, "all_urls.txt")
    # Ensure a fresh start
    open(all_urls_path, "w").close()

    # State
    urls_to_visit = list(seeds)
    seen = set()
    session = requests.Session()
    count = 0

    while urls_to_visit and count < max_pages_per_topic:
        url = urls_to_visit.pop(0)
        if url in seen:
            continue
        seen.add(url)

        try:
            resp = session.get(url, timeout=5)
            resp.raise_for_status()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            continue

        # Record URL in the master list
        with open(all_urls_path, "a", encoding="utf-8") as f:
            f.write(url + "\n")

        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract vocabulary
        text = soup.get_text(separator=" ")
        tokens = re.findall(r"\b\w+\b", text.lower())
        vocab = sorted(set(tokens))

        # Write vocab file
        safe_name = slugify(url)
        vocab_path = os.path.join(output_dir, f"vocab_{safe_name}.txt")
        with open(vocab_path, "w", encoding="utf-8") as vf:
            vf.write("\n".join(vocab))

        # Enqueue new URLs within the same domain
        for link in soup.find_all("a", href=True):
            href = link["href"]
            abs_url = urljoin(url, href)
            if abs_url.startswith(seeds[0]) and abs_url not in seen:
                urls_to_visit.append(abs_url)

        count += 1
        print(f"[{topic}] Crawled ({count}) {url}")

# Run crawler for each topic
def main():
    for topic, seeds in topics.items():
        print(f"Starting crawl for topic: {topic}")
        crawl_topic(topic, seeds)

if __name__ == "__main__":
    main()
