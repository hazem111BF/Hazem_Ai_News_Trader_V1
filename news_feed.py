import feedparser
from urllib.parse import quote

query = quote(
    '(gold OR XAUUSD OR Federal Reserve OR interest rates OR inflation OR USD)'
)

RSS_URL = (
    "https://news.google.com/rss/search?"
    f"q={query}&hl=en-US&gl=US&ceid=US:en"
)

print("=" * 60)
print("HAZEM AI NEWS TRADER - REAL NEWS TEST")
print("=" * 60)

feed = feedparser.parse(RSS_URL)

print("Feed URL:")
print(RSS_URL)

print()
print("NEWS RECEIVED:", len(feed.entries))
print("-" * 60)

if not feed.entries:
    print("ERROR: No news received")
    print("Check internet connection.")
    quit()

for i, item in enumerate(feed.entries[:10], 1):

    title = item.get("title", "No title")
    link = item.get("link", "No link")
    published = item.get("published", "No date")

    print(f"\n{i}. {title}")
    print(f"   Date: {published}")
    print(f"   Link: {link}")

print()
print("=" * 60)
print("REAL NEWS TEST SUCCESS")
print("=" * 60)