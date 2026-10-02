"""Collecte quotidienne gratuite : Google News RSS + flux RSS libres -> site/articles.json
Usage : pip install feedparser && python collector.py"""
import json, hashlib, time, urllib.parse, datetime as dt
import feedparser

METIERS = {
 "Marketing": "marketing",
 "Insights": "consumer insights",
 "Études de marché": "études de marché",
 "Innovation": "innovation",
 "Direction générale": "stratégie entreprise comité de direction",
}
SECTEURS = {
 "Retail & e-commerce": "retail e-commerce distribution",
 "Banque & assurance": "banque assurance",
 "Santé & pharma": "santé pharma",
 "Luxe & beauté": "luxe beauté cosmétique",
 "Automobile": "automobile",
 "Médias & télécoms": "médias télécoms",
 "Énergie": "énergie",
 "Industrie": "industrie",
}
# Flux libres supplémentaires (blogs, newsletters, Mastodon...) : à compléter
EXTRA_FEEDS = [
 ("Mastodon #IA", "https://mastodon.social/tags/IA.rss"),
]
MAX_AGE_DAYS, MAX_ITEMS = 30, 400

def gnews(q):
    u = "https://news.google.com/rss/search?q=" + urllib.parse.quote(q + " when:2d") + "&hl=fr&gl=FR&ceid=FR:fr"
    return feedparser.parse(u).entries

def add(store, e, source, m=None, s=None):
    link = e.get("link", "")
    key = hashlib.md5(e.get("title", "").lower().encode()).hexdigest()
    ts = time.mktime(e.published_parsed) if e.get("published_parsed") else time.time()
    if time.time() - ts > MAX_AGE_DAYS * 86400: return
    a = store.setdefault(key, {"t": e.get("title", "").strip(), "u": link, "o": source,
                               "ts": ts, "m": set(), "s": set()})
    if m: a["m"].add(m)
    if s: a["s"].add(s)

store = {}
for mn, mq in METIERS.items():
    for e in gnews(f'"intelligence artificielle" {mq}'):
        add(store, e, e.get("source", {}).get("title", "Google News"), m=mn)
for sn, sq in SECTEURS.items():
    for e in gnews(f'"intelligence artificielle" {sq}'):
        add(store, e, e.get("source", {}).get("title", "Google News"), s=sn)
for name, url in EXTRA_FEEDS:
    for e in feedparser.parse(url).entries:
        add(store, e, name)

# fusion avec l'historique pour garder 30 jours
try:
    old = json.load(open("site/articles.json", encoding="utf-8"))["articles"]
except Exception:
    old = []
items = [{**a, "m": sorted(a["m"]), "s": sorted(a["s"])} for a in store.values()]
seen = {a["u"] for a in items}
items += [a for a in old if a["u"] not in seen and time.time() - a["ts"] < MAX_AGE_DAYS * 86400]
items.sort(key=lambda a: -a["ts"])
json.dump({"updated": dt.datetime.now().isoformat(timespec="minutes"),
           "metiers": list(METIERS), "secteurs": list(SECTEURS),
           "articles": items[:MAX_ITEMS]}, open("site/articles.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(len(items), "articles")
