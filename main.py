import argparse
import json
import os
import re

import feedparser
import requests

parser = argparse.ArgumentParser()
parser.add_argument("--report", action="store_true")
parser.add_argument("--no-send", action="store_true")
parser.add_argument("--no-store", action="store_true")
parser.add_argument("username")
parser.add_argument("webhook")

args = parser.parse_args()

URL = f"http://localhost:8080/{args.username}/with_replies/rss"
URL_REGEX = r"http://.*?/.*?/status/(\d+)"
NEW_DOMAIN = f"https://vxtwitter.com/{args.username}/status/"
WEBHOOK = args.webhook

def url_to_id(url):
    return re.search(URL_REGEX, url)[1]

feed = feedparser.parse(URL)

if feed.status != 200 or len(feed.entries) == 0:
    if args.report and not os.access("fail_marker", os.F_OK):
            requests.post(WEBHOOK, json={
                "content": "bep it broke help",
            })
            open("fail_marker", "x").close()
    print("Failed to fetch", feed.status)
elif args.report:
    try:
        os.remove("fail_marker")
    except FileNotFoundError:
        pass

seen = None
with open("seen_tweets.json") as file:
    j = json.load(file)
    seen = set(j)

for tweet in reversed(feed.entries):
    id = re.search(URL_REGEX, tweet["id"])[1]
    if id not in seen:
        link = NEW_DOMAIN + id
        if not args.no_send:
            requests.post(WEBHOOK, json={
                "content": link,
            })
        else:
            print(link)
        if not args.no_store:
            seen.add(id)

os.rename("seen_tweets.json", "seen_tweets.json.old")
with open("seen_tweets.json", "w") as file:
    json.dump(list(seen), file, indent=2)
