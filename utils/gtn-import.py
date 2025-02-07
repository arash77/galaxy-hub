import logging
import os
from datetime import datetime

import feedparser
import yaml

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

FEED_URL = "https://training.galaxyproject.org/training-material/feed.xml"
feed = feedparser.parse(FEED_URL)

count = 0
for entry in feed.entries:
    try:
        date_ymd = datetime.fromisoformat(entry.get("published")).strftime("%Y-%m-%d")
    except Exception as e:
        logging.error(
            f"Could not parse date for entry '{entry.get('title', 'Untitled')}': {e}"
        )
        continue
    tags = ["training", "gtn-news"]
    if "tags" in entry:
        tags += [tag.get("term", "") for tag in entry["tags"] if "term" in tag]
    authors = ", ".join(tag.get("name", "") for tag in entry.get("authors", []))

    meta = {
        "subsites": ["all"],
        "main_subsite": "global",
        "date": date_ymd,
        "tags": tags,
        "title": entry.get("title", "Untitled"),
        "authors": authors,
        "external_url": entry.get("link", ""),
        "tease": entry.get("summary", "").split(". ")[0],
    }
    slug = entry.get("link", "").split("/")[-1].replace(".html", "")
    folder = f"{date_ymd}-{slug}"

    if "already-on-hub" in meta["tags"]:
        continue

    folder_path = os.path.join("content", "news", folder)
    if not os.path.exists(folder_path):
        logging.info(f"New post: {folder}")
        count += 1
        os.makedirs(folder_path, exist_ok=True)
        index_path = os.path.join(folder_path, "index.md")
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("---\n")
            yaml.dump(meta, f, default_flow_style=False, sort_keys=False)
            f.write("\n---\n")
            f.write(entry.get("summary", ""))
logging.info(f"count={count}")
