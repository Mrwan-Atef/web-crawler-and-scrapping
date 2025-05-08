# Multi-Topic Web Crawler & Scraper

## Overview
This Python-based crawler scrapes multiple topics from seed URLs, extracts vocabulary tokens, and maintains URL mappings. It supports retries, rate-limit handling (429), robots.txt crawl-delay, deduplication, and incremental resumption.

## Features
- **Multi-topic**: Group seeds by topic.
- **Per-seed limits**: Crawl up to _N_ pages per seed.
- **Politeness**: Honors `robots.txt` crawl-delay and random delays.
- **Retries & Backoff**: Retries failed requests (including 429) with exponential backoff.
- **Deduplication & Resumption**: Tracks visited URLs in `all_urls_master.txt`.
- **URL Mapping**: Stores SHA-256–based short hashes mapping to canonical URLs in `url_mapping.json`.
- **Vocabulary Extraction**: Outputs per-page token lists as `vocab_<hash>.txt`.

## Repository Structure
```
.
├── crawler.py               # Main crawler script
├── seeds/                   # Seed URLs (.txt files)
│   ├── books.txt
│   └── education.txt
├── output/                  # Default output directory
│   ├── all_urls_master.txt
│   ├── url_mapping.json
│   └── books/
│       └── vocab_<hash>.txt
└── README.md
```

## Requirements
- Python 3.8+
- `requests`
- `beautifulsoup4`

Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage
```bash
python crawler.py   --seeds-dir seeds   --max-pages 200   --output-dir output
```
- `--seeds-dir`: Directory containing `*.txt` files; each file named `<topic>.txt`.
- `--max-pages`: Maximum pages per seed URL.
- `--output-dir`: Root directory for outputs.

## How It Works
1. **Load** previous `visited` URLs from `all_urls_master.txt`.
2. **Load/Init** `url_mapping.json`.
3. **For each topic**:
   - Read seeds.
   - For each seed:
     1. Read and honor `robots.txt` crawl-delay.
     2. Normalize URLs, skip login pages.
     3. Retry requests (up to 3) with exponential backoff; handle HTTP 429.
     4. Save canonical URL to master list and mark visited.
     5. Extract tokens via BeautifulSoup and regex.
     6. Save as `vocab_<hash>.txt` under topic directory.
     7. Enqueue same-domain links.
4. **On completion**, write updated `url_mapping.json`.

## Troubleshooting
- **Duplicates in master file**: Ensure you don’t manually truncate; the script appends only new URLs.
- **403 / 429 Errors**: Adjust `User-Agent`, verify seeds, or increase backoff.
- **Missing files on rerun**: Keep output directory intact between runs to resume.
- **Performance**: Increase random delay or reduce parallel seeds.

## License
MIT © 2025
"# web-crawler-and-scrapping" 
