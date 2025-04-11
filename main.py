import argparse
import os
import re
import sqlite3

import feedparser
import requests

parser = argparse.ArgumentParser()
parser.add_argument("--report", action="store_true")
parser.add_argument("--no-replies", action="store_true")
parser.add_argument("--no-retweets", action="store_true")
parser.add_argument("--no-send", action="store_true")
parser.add_argument("--no-store", action="store_true")
parser.add_argument("username")
parser.add_argument("webhook")

args = parser.parse_args()

os.chdir(os.path.dirname(__file__))

db = sqlite3.connect("./seen_tweets.db", isolation_level=None)
db.executescript(
    """
CREATE TABLE IF NOT EXISTS tweets (
    id INTEGER NOT NULL,
    poster TEXT NOT NULL,
    PRIMARY KEY (id, poster)
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id=1),
    fail_count INTEGER NOT NULL DEFAULT 0
);
INSERT OR IGNORE INTO settings (id, fail_count) VALUES (1,0);
"""
)

URL = f"http://localhost:8083/{args.username}{'/rss' if args.no_replies else '/with_replies/rss'}"
URL_REGEX = r"http://.*?/.*?/status/(\d+)"
NEW_DOMAIN = f"https://vxtwitter.com/{args.username}/status/"
WEBHOOK = args.webhook


def add_fail():
    fail_marker = db.execute("SELECT fail_count FROM settings").fetchone()[0]
    db.execute("UPDATE settings SET fail_count = fail_count+1")
    if fail_marker == 0:
        return 0
    else:
        return fail_marker


def remove_fail():
    db.execute("UPDATE settings SET fail_count = 0")


feed = feedparser.parse(URL)

if feed.status != 200 or len(feed.entries) == 0:
    if args.report and add_fail() == 1:
        requests.post(
            WEBHOOK,
            json={
                "content": "bep it broke help",
            },
            timeout=20,
        )
    print("Failed to fetch", feed.status)
    exit(1)
else:
    remove_fail()

for tweet in reversed(feed.entries):
    id = re.search(URL_REGEX, tweet["id"])[1]
    if args.no_retweets and tweet["author"].lstrip("@") != args.username:
        continue
    exists = db.execute(
        "SELECT TRUE FROM tweets WHERE id = ? AND poster = ?", (id, args.username)
    ).fetchone()
    if not exists:
        link = NEW_DOMAIN + id
        if not args.no_send:
            requests.post(
                WEBHOOK,
                json={
                    "content": link,
                },
                timeout=20,
            )
        else:
            print(link)
        if not args.no_store:
            db.execute(
                "INSERT INTO tweets (id, poster) VALUES (?, ?)", (id, args.username)
            )
