import re
import json
import time
import random
from datetime import datetime

import requests
import feedparser
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm


class YahooFinanceNewsCrawler:
    def __init__(
        self,
        rss_url: str = "https://finance.yahoo.com/news/rssindex",
        sleep_min: float = 0.8,
        sleep_max: float = 2.0,
        timeout: int = 20,
    ):
        self.rss_url = rss_url
        self.sleep_min = sleep_min
        self.sleep_max = sleep_max
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update(
            {
                "user-agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Safari/537.36"
                ),
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "accept-language": "en-US,en;q=0.9",
                "referer": "https://finance.yahoo.com/news/",
            }
        )

    @staticmethod
    def _clean_text(text: str | None) -> str | None:
        if text is None:
            return None
        text = re.sub(r"\s+", " ", text).strip()
        return text if text else None

    def _sleep(self):
        time.sleep(random.uniform(self.sleep_min, self.sleep_max))

    def collect_rss_links(self, max_links: int = 30) -> list[dict]:
        feed = feedparser.parse(self.rss_url)

        rows = []

        for entry in feed.entries[:max_links]:
            rows.append(
                {
                    "rss_title": self._clean_text(entry.get("title")),
                    "rss_url": entry.get("link"),
                    "rss_published": entry.get("published"),
                    "rss_summary": self._clean_text(entry.get("summary")),
                    "rss_id": entry.get("id"),
                }
            )

        return rows

    def _get_soup(self, url: str) -> BeautifulSoup:
        res = self.session.get(
            url,
            timeout=self.timeout,
            allow_redirects=True,
        )
        res.raise_for_status()
        return BeautifulSoup(res.text, "lxml")

    def parse_article(self, rss_row: dict) -> dict:
        url = rss_row["rss_url"]
        soup = self._get_soup(url)

        headline = self._extract_headline(soup) or rss_row.get("rss_title")
        provider = self._extract_provider(soup)
        author = self._extract_author(soup)
        published_at = self._extract_published_at(soup) or rss_row.get("rss_published")
        modified_at = self._extract_modified_at(soup)
        body = self._extract_body(soup)
        canonical_url = self._extract_canonical_url(soup)

        tickers = self._extract_tickers(soup)

        title_tag = soup.find("title")
        page_title = self._clean_text(title_tag.get_text(" ", strip=True)) if title_tag else None

        return {
            "source": "yahoo_finance",
            "provider": provider,
            "headline": headline,
            "author": author,
            "published_at": published_at,
            "modified_at": modified_at,
            "summary": rss_row.get("rss_summary"),
            "body": body,
            "tickers": tickers,
            "rss_url": rss_row.get("rss_url"),
            "canonical_url": canonical_url,
            "page_title": page_title,
            "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": None,
        }

    def _extract_json_ld_items(self, soup: BeautifulSoup) -> list[dict]:
        items = []

        for script in soup.find_all("script", type="application/ld+json"):
            raw = script.string or script.get_text()
            if not raw:
                continue

            try:
                data = json.loads(raw)
            except Exception:
                continue

            if isinstance(data, dict):
                items.append(data)
                if isinstance(data.get("@graph"), list):
                    items.extend([x for x in data["@graph"] if isinstance(x, dict)])
            elif isinstance(data, list):
                items.extend([x for x in data if isinstance(x, dict)])

        return items

    def _extract_canonical_url(self, soup: BeautifulSoup) -> str | None:
        canonical = soup.find("link", rel="canonical")
        if canonical and canonical.get("href"):
            return self._clean_text(canonical.get("href"))

        og_url = soup.find("meta", property="og:url")
        if og_url and og_url.get("content"):
            return self._clean_text(og_url.get("content"))

        return None

    def _extract_headline(self, soup: BeautifulSoup) -> str | None:
        for item in self._extract_json_ld_items(soup):
            if item.get("headline"):
                return self._clean_text(item.get("headline"))

        for selector in [
            "h1",
            "h1[data_lake-testid='headline']",
            "h1[data_lake-test-locator='headline']",
        ]:
            tag = soup.select_one(selector)
            if tag:
                txt = self._clean_text(tag.get_text(" ", strip=True))
                if txt:
                    return txt

        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return self._clean_text(og_title.get("content"))

        return None

    def _extract_provider(self, soup: BeautifulSoup) -> str | None:
        for item in self._extract_json_ld_items(soup):
            publisher = item.get("publisher")
            if isinstance(publisher, dict) and publisher.get("name"):
                return self._clean_text(publisher.get("name"))

            source_org = item.get("sourceOrganization")
            if isinstance(source_org, dict) and source_org.get("name"):
                return self._clean_text(source_org.get("name"))

        og_site = soup.find("meta", property="og:site_name")
        if og_site and og_site.get("content"):
            return self._clean_text(og_site.get("content"))

        return "Yahoo Finance"

    def _extract_author(self, soup: BeautifulSoup) -> str | None:
        for item in self._extract_json_ld_items(soup):
            author = item.get("author")

            if isinstance(author, dict) and author.get("name"):
                return self._clean_text(author.get("name"))

            if isinstance(author, list):
                names = []
                for x in author:
                    if isinstance(x, dict) and x.get("name"):
                        names.append(self._clean_text(x.get("name")))

                names = [x for x in names if x]
                if names:
                    return ", ".join(names)

        for selector in [
            '[class*="byline"]',
            '[class*="author"]',
            '[data_lake-testid*="author"]',
            '[data_lake-test-locator*="author"]',
        ]:
            tag = soup.select_one(selector)
            if tag:
                txt = self._clean_text(tag.get_text(" ", strip=True))
                if txt and len(txt) <= 150:
                    txt = re.sub(r"^By\s+", "", txt, flags=re.I)
                    return txt

        return None

    def _extract_published_at(self, soup: BeautifulSoup) -> str | None:
        for item in self._extract_json_ld_items(soup):
            for key in ["datePublished", "dateCreated"]:
                value = item.get(key)
                if value:
                    return self._clean_text(value)

        for attrs in [
            {"property": "article:published_time"},
            {"name": "pubdate"},
            {"name": "publish-date"},
            {"itemprop": "datePublished"},
        ]:
            tag = soup.find("meta", attrs=attrs)
            if tag and tag.get("content"):
                return self._clean_text(tag.get("content"))

        time_tag = soup.find("time")
        if time_tag:
            if time_tag.get("datetime"):
                return self._clean_text(time_tag.get("datetime"))
            return self._clean_text(time_tag.get_text(" ", strip=True))

        return None

    def _extract_modified_at(self, soup: BeautifulSoup) -> str | None:
        for item in self._extract_json_ld_items(soup):
            value = item.get("dateModified")
            if value:
                return self._clean_text(value)

        tag = soup.find("meta", property="article:modified_time")
        if tag and tag.get("content"):
            return self._clean_text(tag.get("content"))

        return None

    def _extract_body_from_json_ld(self, soup: BeautifulSoup) -> str | None:
        for item in self._extract_json_ld_items(soup):
            article_body = item.get("articleBody")
            if article_body:
                txt = self._clean_text(article_body)
                if txt and len(txt) >= 120:
                    return txt

        return None

    def _extract_body(self, soup: BeautifulSoup) -> str | None:
        json_body = self._extract_body_from_json_ld(soup)
        if json_body:
            return json_body

        roots = []

        for selector in [
            "div.caas-body",
            "div.caas-content",
            "div[data_lake-testid='article-body']",
            "div[data_lake-test-locator='article-body']",
            "article",
            "main article",
            "main",
        ]:
            root = soup.select_one(selector)
            if root:
                roots.append(root)

        bad_patterns = [
            "Advertisement",
            "Story continues",
            "Read more",
            "Recommended Stories",
            "Most Read",
            "TRENDING",
            "Sign in",
            "Subscribe",
            "Click here",
            "Download the Yahoo Finance app",
            "Yahoo Finance",
            "Privacy Dashboard",
        ]

        paragraphs = []
        seen = set()

        for root in roots:
            for tag in root.find_all(["p", "h2"]):
                txt = self._clean_text(tag.get_text(" ", strip=True))
                if not txt:
                    continue

                if any(bad.lower() in txt.lower() for bad in bad_patterns):
                    continue

                if len(txt) < 40:
                    continue

                if txt in seen:
                    continue

                seen.add(txt)

                if tag.name == "h2":
                    paragraphs.append(f"\n## {txt}\n")
                else:
                    paragraphs.append(txt)

            if len(paragraphs) >= 3:
                break

        if not paragraphs:
            return None

        body = "\n".join(paragraphs)
        body = re.sub(r"\n{3,}", "\n\n", body).strip()

        return body if body else None

    def _extract_tickers(self, soup: BeautifulSoup) -> str | None:
        tickers = set()

        for a in soup.select("a[href*='/quote/']"):
            href = a.get("href") or ""
            m = re.search(r"/quote/([^/?#]+)", href)
            if m:
                ticker = m.group(1).strip()
                if ticker:
                    tickers.add(ticker)

        # 본문/메타 내 괄호형 티커 보조 추출: (AAPL), (TSLA), (^GSPC)
        text = soup.get_text(" ", strip=True)
        for m in re.finditer(r"\(([A-Z^][A-Z0-9.^=-]{0,12})\)", text):
            tickers.add(m.group(1))

        if not tickers:
            return None

        return ",".join(sorted(tickers))

    def crawl(self, max_links: int = 30) -> pd.DataFrame:
        rss_rows = self.collect_rss_links(max_links=max_links)

        rows = []

        for rss_row in tqdm(rss_rows, desc="collecting yahoo finance news"):
            try:
                row = self.parse_article(rss_row)
                rows.append(row)

            except Exception as e:
                rows.append(
                    {
                        "source": "yahoo_finance",
                        "provider": None,
                        "headline": rss_row.get("rss_title"),
                        "author": None,
                        "published_at": rss_row.get("rss_published"),
                        "modified_at": None,
                        "summary": rss_row.get("rss_summary"),
                        "body": None,
                        "tickers": None,
                        "rss_url": rss_row.get("rss_url"),
                        "canonical_url": None,
                        "page_title": None,
                        "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "error": str(e),
                    }
                )

            self._sleep()

        df = pd.DataFrame(rows)

        columns = [
            "source",
            "provider",
            "headline",
            "author",
            "published_at",
            "modified_at",
            "summary",
            "body",
            "tickers",
            "rss_url",
            "canonical_url",
            "page_title",
            "collected_at",
            "error",
        ]

        for col in columns:
            if col not in df.columns:
                df[col] = None

        df = df[columns]
        df = df.drop_duplicates(subset=["canonical_url", "rss_url"]).reset_index(drop=True)

        return df


if __name__ == "__main__":
    crawler = YahooFinanceNewsCrawler(
        rss_url="https://finance.yahoo.com/news/rssindex",
        sleep_min=1.0,
        sleep_max=2.5,
    )

    news_data = crawler.crawl(max_links=50)

    news_data["body_len"] = news_data["body"].fillna("").str.len()

    print(
        news_data[
            [
                "headline",
                "provider",
                "published_at",
                "body_len",
                "tickers",
                "rss_url",
                "error",
            ]
        ].head(30)
    )

    news_data.to_excel("yahoo_finance_news_20260703.xlsx", index=False)
    #news_data.to_csv("yahoo_finance_news_test.csv", index=False, encoding="utf-8-sig")