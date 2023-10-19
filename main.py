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

os.chdir(os.path.dirname(__file__))

URL = f"http://localhost:8080/{args.username}/with_replies/rss"
URL_REGEX = r"http://.*?/.*?/status/(\d+)"
NEW_DOMAIN = f"https://vxtwitter.com/{args.username}/status/"
WEBHOOK = args.webhook


def add_fail():
    try:
        with open("fail_marker", "r+") as file:
            res = file.readline()
            if len(res) == 0:
                fail_counter = 1
            else:
                fail_counter = int(res)
            file.seek(0)
            file.truncate()
            file.write(f"{fail_counter+1}\n")
            return fail_counter
    except FileNotFoundError:
        with open("fail_marker", "x") as file:
            file.write("1")
            return 0


def remove_fail():
    try:
        os.remove("fail_marker")
    except FileNotFoundError:
        pass


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

seen = None
with open("seen_tweets.json") as file:
    j = json.load(file)
    seen = set(j)

for tweet in reversed(feed.entries):
    id = re.search(URL_REGEX, tweet["id"])[1]
    if id not in seen:
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
            seen.add(id)

os.rename("seen_tweets.json", "seen_tweets.json.old")
with open("seen_tweets.json", "w") as file:
    json.dump(list(seen), file, indent=2)
