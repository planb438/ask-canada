#!/usr/bin/env python3
"""Ask Canada Civic Hub collector.
Pulls the latest Government of Canada news (official canada.ca feed), keeps the topics
newcomers and residents care about, and merges them into data/updates.json.
Every item keeps the date we first saw it, so the file is also the change history.
Runs daily from .github/workflows/civic-hub.yml. Standard library only."""
import json, os, urllib.request, datetime as dt

FEED = "https://api.io.canada.ca/io-server/gc/news/en/v2?sort=publishedDate&orderBy=desc&pick=500&format=json"
TOPICS = {
    "immigration-refugees-citizenship": "Immigration & citizenship",
    "employment-social-development": "Jobs & benefits",
    "revenue-agency": "Taxes & money",
    "department-finance": "Taxes & money",
    "financial-consumer-agency": "Taxes & money",
    "health-canada": "Health",
    "public-health": "Health",
    "border-services-agency": "Travel & borders",
    "transport-canada": "Travel & borders",
    "housing-infrastructure-communities": "Housing",
    "public-safety-canada": "Safety",
}
DEPTS = {
    "immigration-refugees-citizenship": "IRCC", "employment-social-development": "ESDC / Service Canada",
    "revenue-agency": "CRA", "department-finance": "Finance Canada", "financial-consumer-agency": "FCAC",
    "health-canada": "Health Canada", "public-health": "Public Health Agency", "border-services-agency": "CBSA",
    "transport-canada": "Transport Canada", "housing-infrastructure-communities": "Housing, Infrastructure and Communities",
    "public-safety-canada": "Public Safety Canada",
}
KEEP_DAYS, MAX_ITEMS = 120, 400
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "updates.json")

def main():
    req = urllib.request.Request(FEED, headers={"User-Agent": "ask-canada.ca civic hub"})
    entries = json.load(urllib.request.urlopen(req, timeout=60))["feed"]["entry"]
    try:
        old = json.load(open(OUT))
    except Exception:
        old = {"items": []}
    items = {i["link"]: i for i in old.get("items", [])}
    today = dt.date.today().isoformat()
    added = 0
    for e in entries:
        link = e.get("link", "")
        if "canada.ca/en/" not in link:
            continue
        dept = link.split("/en/")[1].split("/")[0]
        if dept not in TOPICS or link in items:
            continue
        items[link] = {"title": e.get("title", "").strip(), "link": link, "teaser": (e.get("teaser") or "").strip(),
                       "published": e.get("publishedDate", "")[:10], "topic": TOPICS[dept], "source": DEPTS[dept],
                       "first_seen": today}
        added += 1
    cutoff = (dt.date.today() - dt.timedelta(days=KEEP_DAYS)).isoformat()
    kept = sorted((i for i in items.values() if i["published"] >= cutoff), key=lambda i: i["published"], reverse=True)[:MAX_ITEMS]
    data = {"updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
            "source": "Government of Canada news (canada.ca)", "topics": sorted(set(TOPICS.values())), "items": kept}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(f"added {added}, total {len(kept)}")

if __name__ == "__main__":
    main()
