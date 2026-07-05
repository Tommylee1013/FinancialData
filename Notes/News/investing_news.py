import re
import json
import time
import random
from datetime import datetime
from urllib.parse import urljoin, urlparse

import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
from playwright.sync_api import sync_playwright


class InvestingNewsCrawler:
    def __init__(
        self,
        base_url: str = "https://www.investing.com",
        news_url: str = "https://www.investing.com/news",
        headless: bool = False,
        sleep_min: float = 1.5,
        sleep_max: float = 3.0,
        timeout: int = 60000,
    ):
        self.base_url = base_url
        self.news_url = news_url
        self.headless = headless
        self.sleep_min = sleep_min
        self.sleep_max = sleep_max
        self.timeout = timeout

    @staticmethod
    def _clean_text(text: str | None) -> str | None:
        if text is None:
            return None
        text = re.sub(r"\s+", " ", text).strip()
        return text if text else None

    @staticmethod
    def _is_article_url(url: str) -> bool:
        path = urlparse(url).path

        if not path.startswith("/news/"):
            return False

        exclude_paths = {
            "/news",
            "/news/",
            "/news/latest-news",
            "/news/most-popular-news",
            "/news/stock-market-news",
            "/news/forex-news",
            "/news/commodities-news",
            "/news/economy",
            "/news/cryptocurrency-news",
        }

        if path in exclude_paths:
            return False

        return bool(re.search(r"-\d{5,}$", path))

    def _sleep(self):
        time.sleep(random.uniform(self.sleep_min, self.sleep_max))

    def _new_context(self, browser):
        return browser.new_context(
            viewport={"width": 1440, "height": 1000},
            locale="en-US",
            timezone_id="America/New_York",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            extra_http_headers={
                "accept-language": "en-US,en;q=0.9",
                "referer": "https://www.google.com/",
            },
        )

    def collect_article_links(self, page, max_links: int = 30) -> list[str]:
        page.goto(
            self.news_url,
            wait_until="domcontentloaded",
            timeout=self.timeout,
        )
        page.wait_for_timeout(3000)

        for text in ["Accept All", "I Accept", "Agree", "Accept"]:
            try:
                page.get_by_text(text, exact=False).click(timeout=1500)
                page.wait_for_timeout(1000)
                break
            except Exception:
                pass

        for _ in range(5):
            page.mouse.wheel(0, 1200)
            page.wait_for_timeout(1000)

        html = page.content()
        soup = BeautifulSoup(html, "lxml")

        links = []
        seen = set()

        for a in soup.select("a[href]"):
            href = a.get("href")
            if not href:
                continue

            full_url = urljoin(self.base_url, href)
            path = urlparse(full_url).path

            if not self._is_article_url(full_url):
                continue

            if path in seen:
                continue

            seen.add(path)
            links.append(full_url)

            if len(links) >= max_links:
                break

        return links

    def parse_article(self, page, url: str) -> dict:
        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=self.timeout,
        )

        page.wait_for_timeout(3000)

        current_url = page.url
        html = page.content()
        soup = BeautifulSoup(html, "lxml")

        headline = self._extract_headline(soup)
        author = self._extract_author(soup)
        published_at = self._extract_published_at(soup)
        modified_at = self._extract_modified_at(soup)
        category = self._extract_category(soup)
        body = self._extract_body(soup)

        canonical_url = self._extract_canonical_url(soup)

        title_tag = soup.find("title")
        page_title = self._clean_text(title_tag.get_text(" ", strip=True)) if title_tag else None

        return {
            "source": "investing.com",
            "category": category,
            "headline": headline,
            "author": author,
            "published_at": published_at,
            "modified_at": modified_at,
            "body": body,
            "url": url,
            "canonical_url": canonical_url,
            "current_url": current_url,
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

    def _extract_headline(self, soup: BeautifulSoup) -> str | None:
        h1 = soup.find("h1", id="articleTitle")
        if h1:
            return self._clean_text(h1.get_text(" ", strip=True))

        for item in self._extract_json_ld_items(soup):
            if item.get("@type") == "NewsArticle" and item.get("headline"):
                return self._clean_text(item.get("headline"))

        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = self._clean_text(og_title.get("content"))
            if title:
                title = re.sub(r"\s+By\s+.+$", "", title).strip()
            return title

        title_tag = soup.find("title")
        if title_tag:
            title = self._clean_text(title_tag.get_text(" ", strip=True))
            if title:
                title = re.sub(r"\s+By\s+.+$", "", title).strip()
            return title

        return None

    def _extract_author(self, soup: BeautifulSoup) -> str | None:
        for item in self._extract_json_ld_items(soup):
            if item.get("@type") == "NewsArticle":
                author = item.get("author")

                if isinstance(author, dict):
                    name = author.get("name")
                    if name:
                        return self._clean_text(name)

                if isinstance(author, list):
                    names = []
                    for x in author:
                        if isinstance(x, dict) and x.get("name"):
                            names.append(self._clean_text(x.get("name")))
                    names = [x for x in names if x]
                    if names:
                        return ", ".join(names)

        text = soup.get_text("\n", strip=True)
        m = re.search(r"\bBy\s+([A-Za-z가-힣 .,'-]{2,80})", text)
        if m:
            return self._clean_text(m.group(1))

        return None

    def _extract_published_at(self, soup: BeautifulSoup) -> str | None:
        for item in self._extract_json_ld_items(soup):
            if item.get("@type") == "NewsArticle":
                for key in ["datePublished", "dateCreated"]:
                    value = item.get(key)
                    if value:
                        return self._clean_text(value)

        return None

    def _extract_modified_at(self, soup: BeautifulSoup) -> str | None:
        for item in self._extract_json_ld_items(soup):
            if item.get("@type") == "NewsArticle":
                value = item.get("dateModified")
                if value:
                    return self._clean_text(value)

        return None

    def _extract_category(self, soup: BeautifulSoup) -> str | None:
        for item in self._extract_json_ld_items(soup):
            if item.get("@type") == "NewsArticle":
                value = item.get("articleSection")
                if value:
                    return self._clean_text(value)

        return None

    def _extract_canonical_url(self, soup: BeautifulSoup) -> str | None:
        canonical = soup.find("link", rel="canonical")
        if canonical and canonical.get("href"):
            return self._clean_text(canonical.get("href"))

        og_url = soup.find("meta", property="og:url")
        if og_url and og_url.get("content"):
            return self._clean_text(og_url.get("content"))

        return None

    def _extract_body(self, soup: BeautifulSoup) -> str | None:
        article_root = soup.find("div", id="article")

        if article_root is None:
            return None

        # CTA, 광고, 관련기사, 버튼성 링크 제거
        for tag in article_root.select(
            """
            a[data_lake-article-pro-hook],
            script,
            style,
            iframe,
            button,
            form,
            aside,
            figure
            """
        ):
            tag.decompose()

        paragraphs = []

        for tag in article_root.find_all(["p", "h2"]):
            txt = self._clean_text(tag.get_text(" ", strip=True))
            if not txt:
                continue

            if txt.startswith("Unlock premium"):
                continue

            if txt.startswith("Reporting by"):
                # 기자 표기는 body에서 빼고 싶으면 continue,
                # 남기고 싶으면 이 줄 삭제
                continue

            if len(txt) < 30:
                continue

            if tag.name == "h2":
                paragraphs.append(f"\n## {txt}\n")
            else:
                paragraphs.append(txt)

        if not paragraphs:
            return None

        body = "\n".join(paragraphs)
        body = re.sub(r"\n{3,}", "\n\n", body).strip()

        return body if body else None

    def crawl(self, max_links: int = 30) -> pd.DataFrame:
        rows = []

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            )

            context = self._new_context(browser)
            page = context.new_page()

            article_links = self.collect_article_links(
                page=page,
                max_links=max_links,
            )

            print(f"collected article links: {len(article_links)}")

            for url in tqdm(article_links, desc="collecting investing.com articles"):
                try:
                    row = self.parse_article(page, url)
                    rows.append(row)

                except Exception as e:
                    rows.append(
                        {
                            "source": "investing.com",
                            "category": None,
                            "headline": None,
                            "author": None,
                            "published_at": None,
                            "modified_at": None,
                            "body": None,
                            "url": url,
                            "canonical_url": None,
                            "current_url": None,
                            "page_title": None,
                            "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "error": str(e),
                        }
                    )

                self._sleep()

            context.close()
            browser.close()

        df = pd.DataFrame(rows)

        columns = [
            "source",
            "category",
            "headline",
            "author",
            "published_at",
            "modified_at",
            "body",
            "url",
            "canonical_url",
            "current_url",
            "page_title",
            "collected_at",
            "error",
        ]

        for col in columns:
            if col not in df.columns:
                df[col] = None

        df = df[columns]
        df = df.drop_duplicates(subset=["canonical_url", "url"]).reset_index(drop=True)

        return df


if __name__ == "__main__":
    crawler = InvestingNewsCrawler(
        headless=False,
        sleep_min=2.0,
        sleep_max=4.0,
    )

    news_data = crawler.crawl(max_links=100)

    news_data["body_len"] = news_data["body"].fillna("").str.len()

    print(
        news_data[
            [
                "headline",
                "category",
                "author",
                "published_at",
                "body_len",
                "url",
                "error",
            ]
        ]
    )

    news_data.to_excel("investing_com_20260705.xlsx", index=False)
    # news_data.to_csv("investing_test.csv", index=False, encoding="utf-8-sig")