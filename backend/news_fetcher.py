"""
Crypto news fetcher for TradingApp.

Fetches articles from public RSS feeds, tags them with relevant tokens
(BTC, ETH, HYPE), and caches results for 5 minutes to reduce network load.
Falls back to static demo articles if all feeds are unavailable.
"""
import logging
import re
import time
from datetime import datetime, timezone
from typing import Optional

import feedparser

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RSS_FEEDS = [
    {"url": "https://cointelegraph.com/rss",                       "source": "CoinTelegraph"},
    {"url": "https://www.coindesk.com/arc/outboundfeeds/rss/",     "source": "CoinDesk"},
    {"url": "https://decrypt.co/feed",                             "source": "Decrypt"},
    {"url": "https://cryptonews.com/news/feed/",                   "source": "CryptoNews"},
]

# Keywords used to tag articles with relevant tokens
TOKEN_KEYWORDS: dict[str, list[str]] = {
    "BTC":  ["bitcoin", " btc ", "satoshi", "bitcoin etf", "btc etf"],
    "ETH":  ["ethereum", " eth ", "vitalik", "ethereum etf", "eth etf", "ether"],
    "HYPE": ["hyperliquid", "hype token", "hype coin", "$hype"],
}

CACHE_TTL = 300   # seconds (5 minutes)
MAX_ITEMS_PER_FEED = 20

# ---------------------------------------------------------------------------
# In-memory cache
# ---------------------------------------------------------------------------

_cache: dict = {"articles": [], "fetched_at": 0.0}

# ---------------------------------------------------------------------------
# Demo fallback articles (used when all feeds are unreachable)
# ---------------------------------------------------------------------------

DEMO_ARTICLES = [
    {
        "id": "demo-btc-1",
        "title": "Bitcoin Breaks $100,000: Institutional Demand Drives New All-Time Highs",
        "url": "https://coindesk.com",
        "source": "CoinDesk",
        "published_at": "2024-12-15T10:00:00+00:00",
        "summary": "Bitcoin surpassed the $100,000 mark for the first time as spot ETF inflows hit record levels and major institutions added BTC to their treasury reserves.",
        "tokens": ["BTC"],
    },
    {
        "id": "demo-btc-2",
        "title": "MicroStrategy Adds Another 5,000 BTC to Its Holdings",
        "url": "https://cointelegraph.com",
        "source": "CoinTelegraph",
        "published_at": "2024-12-14T08:30:00+00:00",
        "summary": "MicroStrategy announced it has purchased an additional 5,000 Bitcoin, bringing its total holdings to over 400,000 BTC worth approximately $40 billion.",
        "tokens": ["BTC"],
    },
    {
        "id": "demo-eth-1",
        "title": "Ethereum Layer-2 Ecosystem Surpasses $50 Billion in Total Value Locked",
        "url": "https://decrypt.co",
        "source": "Decrypt",
        "published_at": "2024-12-15T09:00:00+00:00",
        "summary": "The Ethereum Layer-2 ecosystem has reached a milestone, with protocols like Arbitrum, Optimism, and Base collectively locking over $50 billion in assets.",
        "tokens": ["ETH"],
    },
    {
        "id": "demo-eth-2",
        "title": "Vitalik Buterin Proposes New Ethereum Roadmap for 2025",
        "url": "https://coindesk.com",
        "source": "CoinDesk",
        "published_at": "2024-12-13T14:00:00+00:00",
        "summary": "Ethereum co-founder Vitalik Buterin published a new vision document outlining key upgrades planned for Ethereum in 2025, focusing on scalability and privacy improvements.",
        "tokens": ["ETH"],
    },
    {
        "id": "demo-hype-1",
        "title": "Hyperliquid's HYPE Token Surges 300% Following Mainnet Launch",
        "url": "https://cointelegraph.com",
        "source": "CoinTelegraph",
        "published_at": "2024-12-15T11:00:00+00:00",
        "summary": "Hyperliquid's native token HYPE has surged dramatically following the launch of its L1 blockchain, with the decentralized perpetual exchange gaining massive traction among traders.",
        "tokens": ["HYPE"],
    },
    {
        "id": "demo-hype-2",
        "title": "Hyperliquid Processes $10 Billion in Daily Volume, Rivaling Centralized Exchanges",
        "url": "https://decrypt.co",
        "source": "Decrypt",
        "published_at": "2024-12-14T16:00:00+00:00",
        "summary": "Hyperliquid has emerged as a major player in the derivatives market, processing over $10 billion in daily trading volume and positioning itself as a competitor to Binance and OKX.",
        "tokens": ["HYPE"],
    },
    {
        "id": "demo-btc-eth-1",
        "title": "Crypto Market Rally: Bitcoin and Ethereum Lead Bull Run Into Year-End",
        "url": "https://cryptonews.com",
        "source": "CryptoNews",
        "published_at": "2024-12-15T07:00:00+00:00",
        "summary": "The broader crypto market is experiencing a strong year-end rally, with Bitcoin and Ethereum leading gains as macroeconomic conditions improve and regulatory clarity increases.",
        "tokens": ["BTC", "ETH"],
    },
    {
        "id": "demo-general-1",
        "title": "DeFi Total Value Locked Hits Record $200 Billion Amid Bull Market",
        "url": "https://coindesk.com",
        "source": "CoinDesk",
        "published_at": "2024-12-12T12:00:00+00:00",
        "summary": "Decentralized finance protocols collectively locked over $200 billion in assets for the first time, a milestone that underscores the growing adoption of on-chain financial services.",
        "tokens": ["ETH", "HYPE"],
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_html(text: str) -> str:
    """Remove HTML tags from a string."""
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _tag_tokens(title: str, summary: str) -> list[str]:
    """Return list of token tags for an article based on keyword matching."""
    text = (" " + title + " " + summary + " ").lower()
    return [token for token, keywords in TOKEN_KEYWORDS.items()
            if any(kw in text for kw in keywords)]


def _parse_date(entry) -> str:
    """Extract ISO-8601 date string from a feed entry."""
    try:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            return dt.isoformat()
    except Exception:  # noqa: BLE001
        pass
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def fetch_news(token_filter: Optional[str] = None) -> list[dict]:
    """
    Return a list of crypto news articles, optionally filtered by token.

    Results are cached for ``CACHE_TTL`` seconds.  Falls back to
    ``DEMO_ARTICLES`` if all RSS feeds fail.

    Parameters
    ----------
    token_filter:
        Optional uppercase token symbol (``"BTC"``, ``"ETH"``, ``"HYPE"``).
        When supplied only articles tagged with that token are returned.
    """
    global _cache  # noqa: PLW0603

    now = time.time()

    if now - _cache["fetched_at"] < CACHE_TTL and _cache["articles"]:
        articles = _cache["articles"]
    else:
        articles = _fetch_from_feeds()
        if not articles:
            logger.info("All RSS feeds failed – using demo news articles")
            articles = DEMO_ARTICLES.copy()
        _cache = {"articles": articles, "fetched_at": now}

    if token_filter:
        tf = token_filter.upper()
        return [a for a in articles if tf in a["tokens"]]

    return articles


def _fetch_from_feeds() -> list[dict]:
    """Fetch and parse all configured RSS feeds. Returns empty list on total failure."""
    articles: list[dict] = []
    seen_urls: set[str] = set()

    for feed_cfg in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_cfg["url"])
            if feed.bozo and not feed.entries:
                logger.warning("Malformed feed from %s", feed_cfg["url"])
                continue

            for entry in feed.entries[:MAX_ITEMS_PER_FEED]:
                url = getattr(entry, "link", "") or ""
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                title   = _strip_html(getattr(entry, "title",   ""))
                summary = _strip_html(getattr(entry, "summary", ""))[:400]
                tokens  = _tag_tokens(title, summary)

                articles.append({
                    "id":           str(abs(hash(url))),
                    "title":        title,
                    "url":          url,
                    "source":       feed_cfg["source"],
                    "published_at": _parse_date(entry),
                    "summary":      summary,
                    "tokens":       tokens,
                })

            logger.info("Fetched %d articles from %s", len(feed.entries), feed_cfg["source"])
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to fetch feed %s: %s", feed_cfg["url"], exc)

    articles.sort(key=lambda a: a["published_at"], reverse=True)
    return articles
