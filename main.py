import argparse
import os
import re
import sqlite3
import random
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser()
parser.add_argument("--no-send", action="store_true")
parser.add_argument("--no-store", action="store_true")
parser.add_argument("webhook")

args = parser.parse_args()

SERVER_ID = int(urlparse(args.webhook).path.split("/")[3])

os.chdir(os.path.dirname(__file__))

db = sqlite3.connect("./seen_imgflips.db", isolation_level=None)
db.executescript(
    """
CREATE TABLE IF NOT EXISTS imgflips (
    url TEXT NOT NULL,
    server INTEGER NOT NULL,
    PRIMARY KEY (url, server)
) WITHOUT ROWID;
"""
)

URL = "https://imgflip.com/m/fun?sort=latest"
WEBHOOK = args.webhook


with requests.get(URL) as req:
    req.raise_for_status()
    soup = BeautifulSoup(req.text, "html.parser")

elements = soup.css.select(".base-unit-title > a")
candidates = []
for x in elements:
    x = x["href"]
    candidates.append(urljoin(URL, x))

for _ in range(len(candidates)):
    link = random.choice(candidates)
    exists = db.execute(
        "SELECT TRUE FROM imgflips WHERE url = ? AND server = ?", (link, SERVER_ID)
    ).fetchone()
    if not exists:
        break

if not args.no_send:
    requests.post(WEBHOOK, json={"content": link}, timeout=20)
else:
    print(link)

if not args.no_store:
    db.execute("INSERT INTO imgflips (url, server) VALUES (?, ?)", (link, SERVER_ID))
