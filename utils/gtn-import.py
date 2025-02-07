import logging
import os
import sys
from datetime import datetime

import feedparser
import yaml
from dateutil.parser import isoparse
from github import Github

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

feed = feedparser.parse(os.getenv("GTN_NEWS_FEED_URL"))

g = Github(os.getenv("GITHUB_TOKEN") or sys.exit("GITHUB_TOKEN not set"))
repo = g.get_repo(os.getenv("REPO_NAME") or sys.exit("REPO_NAME not set"))
existing_prs = repo.get_pulls(state="open", base="master")

count = 0
for entry in feed.entries:
    title = entry.get("title", "Untitled")
    date_ymd = isoparse(
        entry.get("published") or entry.get("pubDate") or entry.get("updated")
    ).strftime("%Y-%m-%d")

    tags = {"training", "gtn-news"} | {
        tag["term"] for tag in entry.get("tags", []) if "term" in tag
    }
    if "already-on-hub" in tags:
        continue

    authors = ", ".join(tag.get("name", "") for tag in entry.get("authors", []))
    link = entry.get("link", "")
    summary = entry.get("summary", "")

    for existing_pr in existing_prs:
        if link in existing_pr.title:
            logging.info(f"PR already exists for {title}: {existing_pr.html_url}")
            continue

    slug = os.path.splitext(os.path.basename(link))[0]
    folder = f"{date_ymd}-{slug}"

    folder_path = os.path.join("content", "news", folder)
    if os.path.exists(folder_path):
        logging.info(f"Folder Already imported: {folder}")
        continue

    logging.info(f"New post: {folder}")
    count += 1
    meta = {
        "subsites": ["all"],
        "main_subsite": "global",
        "date": date_ymd,
        "tags": tags,
        "title": title,
        "authors": authors,
        "external_url": link,
        "tease": summary.split(". ")[0],
    }
    md_config = yaml.dump(meta, default_flow_style=False, sort_keys=False)

    branch_name = f"import-gtn-posts-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    repo.create_git_ref(
        ref=f"refs/heads/{branch_name}", sha=repo.get_branch("master").commit.sha
    )
    repo.create_file(
        path=os.path.join(folder_path, "index.md"),
        message=f"Add {title}",
        content=f"---\n{md_config}---\n{summary}",
        branch=branch_name,
    )
    pr_body = (
        f"This PR imports new GTN posts.\n"
        f"Date of post: {date_ymd}\n"
        f"[{title}]({link})"
    )
    pr = repo.create_pull(
        title=f"Import GTN Post {link}",
        body=pr_body,
        head=branch_name,
        base="master",
    )
    logging.info(f"Pull request created: {pr.html_url}")

logging.info(f"Imported {count} new posts")
