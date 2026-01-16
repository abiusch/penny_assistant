#!/usr/bin/env python3
"""
Enhanced Web Search System
Provides reliable web search with multiple providers and fallback strategies.
"""

import asyncio
import aiohttp
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Represents a search result from any provider"""
    title: str
    url: str
    snippet: str
    provider: str
    confidence: float = 0.7
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class EnhancedWebSearch:
    """Enhanced web search with multiple providers and reliability features"""

    def __init__(self):
        self.session = None
        self.providers = ["duckduckgo", "brave", "serp"]
        self.max_results_per_provider = 5
        self.timeout = 15

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search with multiple providers and fallback"""
        if not self.session:
            raise RuntimeError("EnhancedWebSearch must be used as async context manager")

        all_results = []

        # Try each provider in order
        for provider in self.providers:
            try:
                print(f"🔍 Trying {provider} search for: '{query}'")
                results = await self._search_provider(provider, query)

                if results:
                    print(f"✅ {provider} returned {len(results)} results")
                    all_results.extend(results)
                    # If we have enough good results, don't try more providers
                    if len(all_results) >= max_results:
                        break
                else:
                    print(f"⚠️ {provider} returned no results")

            except Exception as e:
                print(f"❌ {provider} search failed: {e}")
                continue

        # Deduplicate and sort by confidence
        unique_results = self._deduplicate_results(all_results)
        return sorted(unique_results, key=lambda r: r.confidence, reverse=True)[:max_results]

    async def _search_provider(self, provider: str, query: str) -> List[SearchResult]:
        """Search using specific provider"""
        if provider == "duckduckgo":
            return await self._search_duckduckgo(query)
        elif provider == "brave":
            return await self._search_brave(query)
        elif provider == "serp":
            return await self._search_serp(query)
        else:
            return []

    async def _search_duckduckgo(self, query: str) -> List[SearchResult]:
        """Search using DuckDuckGo Instant Answer API"""
        results = []

        try:
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    # Process abstract
                    if data.get("Abstract") and data.get("AbstractURL"):
                        results.append(SearchResult(
                            title=data.get("Heading", "DuckDuckGo Abstract"),
                            url=data["AbstractURL"],
                            snippet=data["Abstract"],
                            provider="duckduckgo",
                            confidence=0.9  # High confidence for instant answers
                        ))

                    # Process related topics
                    for topic in data.get("RelatedTopics", [])[:3]:
                        if isinstance(topic, dict) and topic.get("FirstURL") and topic.get("Text"):
                            results.append(SearchResult(
                                title=topic.get("Text", "").split(" - ")[0],
                                url=topic["FirstURL"],
                                snippet=topic["Text"],
                                provider="duckduckgo",
                                confidence=0.8
                            ))

                elif response.status == 202:
                    # DuckDuckGo is processing - wait a moment and try a simpler query
                    await asyncio.sleep(1)
                    simple_query = query.split()[:3]  # Use first 3 words
                    if len(simple_query) < len(query.split()):
                        return await self._search_duckduckgo(" ".join(simple_query))

        except Exception as e:
            print(f"DuckDuckGo search error: {e}")

        return results

    async def _search_brave(self, query: str) -> List[SearchResult]:
        """Search using Brave Search API (if available)"""
        # Brave Search would require API key - placeholder for now
        # In production, implement: https://api.search.brave.com/res/v1/web/search
        print("Brave Search not configured (requires API key)")
        return []

    async def _search_serp(self, query: str) -> List[SearchResult]:
        """Search using SERP API (if available)"""
        # SERP API would require API key - placeholder for now
        print("SERP API not configured (requires API key)")
        return []

    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on URL similarity"""
        seen_urls = set()
        unique_results = []

        for result in results:
            # Normalize URL for comparison
            normalized_url = result.url.lower().rstrip('/')

            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_results.append(result)

        return unique_results

    async def quick_search(self, query: str) -> Optional[SearchResult]:
        """Quick search for just one good result"""
        results = await self.search(query, max_results=1)
        return results[0] if results else None


async def test_enhanced_search():
    """Test the enhanced search system"""
    print("🧪 Testing Enhanced Web Search System")
    print("=" * 50)

    test_queries = [
        "Boston Dynamics Stretch robot",
        "Python programming tutorial",
        "OpenAI ChatGPT latest updates",
        "machine learning basics"
    ]

    async with EnhancedWebSearch() as search:
        for query in test_queries:
            print(f"\n--- Testing: '{query}' ---")
            results = await search.search(query, max_results=3)

            if results:
                print(f"✅ Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result.title}")
                    print(f"     {result.url}")
                    print(f"     Snippet: {result.snippet[:100]}...")
                    print(f"     Provider: {result.provider}, Confidence: {result.confidence}")
            else:
                print("❌ No results found")


if __name__ == "__main__":
    asyncio.run(test_enhanced_search())