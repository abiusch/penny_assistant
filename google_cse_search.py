#!/usr/bin/env python3
"""
Google Custom Search Engine Integration
Provides reliable web search using Google's Custom Search API to replace DuckDuckGo.
"""

import os
import json
import time
import asyncio
import aiohttp
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class SearchResult:
    """Represents a search result from Google CSE"""
    title: str
    url: str
    snippet: str
    display_link: str
    engine: str = "google_cse"
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class GoogleCSESearchError(Exception):
    """Custom exception for Google CSE search errors"""
    pass


class GoogleCSESearch:
    """Google Custom Search Engine integration with rate limiting and usage tracking"""

    def __init__(self):
        self.api_key = os.getenv('GOOGLE_CSE_API_KEY')
        self.engine_id = os.getenv('GOOGLE_CSE_ENGINE_ID')
        self.daily_limit = int(os.getenv('GOOGLE_CSE_DAILY_LIMIT', '90'))

        if not self.api_key:
            raise GoogleCSESearchError("GOOGLE_CSE_API_KEY environment variable not set")
        if not self.engine_id:
            raise GoogleCSESearchError("GOOGLE_CSE_ENGINE_ID environment variable not set")

        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.usage_file = "google_cse_usage.json"
        self.session = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def _load_usage_data(self) -> Dict[str, Any]:
        """Load daily usage tracking data"""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass

        return {
            "daily_counts": {},
            "total_searches": 0,
            "last_reset": str(date.today())
        }

    def _save_usage_data(self, data: Dict[str, Any]) -> None:
        """Save daily usage tracking data"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save usage data: {e}")

    def _check_rate_limit(self) -> tuple[bool, int, str]:
        """Check if we're within rate limits. Returns (allowed, remaining, status)"""
        usage_data = self._load_usage_data()
        today = str(date.today())

        # Reset daily count if it's a new day
        if usage_data.get("last_reset") != today:
            usage_data["daily_counts"] = {}
            usage_data["last_reset"] = today
            self._save_usage_data(usage_data)

        daily_count = usage_data["daily_counts"].get(today, 0)
        remaining = self.daily_limit - daily_count

        if daily_count >= self.daily_limit:
            return False, 0, f"Daily limit reached ({daily_count}/{self.daily_limit})"
        elif daily_count >= self.daily_limit * 0.8:
            return True, remaining, f"Warning: {remaining} searches remaining today"
        else:
            return True, remaining, "OK"

    def _increment_usage(self) -> None:
        """Increment the daily usage counter"""
        usage_data = self._load_usage_data()
        today = str(date.today())

        usage_data["daily_counts"][today] = usage_data["daily_counts"].get(today, 0) + 1
        usage_data["total_searches"] = usage_data.get("total_searches", 0) + 1

        self._save_usage_data(usage_data)

    async def search(self, query: str, num_results: int = 10, safe: str = "medium") -> List[SearchResult]:
        """
        Perform Google Custom Search

        Args:
            query: Search query string
            num_results: Number of results to return (1-10)
            safe: Safe search level ("off", "medium", "high")

        Returns:
            List of SearchResult objects
        """
        if not self.session:
            raise GoogleCSESearchError("GoogleCSESearch must be used as async context manager")

        # Check rate limits
        allowed, remaining, status = self._check_rate_limit()
        if not allowed:
            raise GoogleCSESearchError(f"Rate limit exceeded: {status}")

        if "Warning" in status:
            print(f"⚠️ Google CSE: {status}")

        # Prepare API request
        params = {
            "key": self.api_key,
            "cx": self.engine_id,
            "q": query,
            "num": min(max(num_results, 1), 10),  # Clamp between 1-10
            "safe": safe
        }

        try:
            print(f"🔍 Google CSE search: '{query}' (limit: {num_results})")

            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = self._parse_search_results(data)

                    # Only increment usage on successful search
                    self._increment_usage()

                    print(f"✅ Found {len(results)} results")
                    return results

                elif response.status == 429:
                    raise GoogleCSESearchError("API rate limit exceeded (too many requests)")

                elif response.status == 403:
                    error_text = await response.text()
                    if "quota" in error_text.lower():
                        raise GoogleCSESearchError("Daily quota exceeded")
                    else:
                        raise GoogleCSESearchError(f"API access forbidden: {error_text}")

                else:
                    error_text = await response.text()
                    raise GoogleCSESearchError(f"API error {response.status}: {error_text}")

        except asyncio.TimeoutError:
            raise GoogleCSESearchError("Search request timed out")
        except aiohttp.ClientError as e:
            raise GoogleCSESearchError(f"Network error: {e}")

    def _parse_search_results(self, data: Dict[str, Any]) -> List[SearchResult]:
        """Parse Google CSE API response into SearchResult objects"""
        results = []

        items = data.get("items", [])
        for item in items:
            try:
                result = SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    display_link=item.get("displayLink", "")
                )
                results.append(result)
            except Exception as e:
                print(f"Warning: Failed to parse search result: {e}")
                continue

        return results

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        usage_data = self._load_usage_data()
        today = str(date.today())

        daily_count = usage_data["daily_counts"].get(today, 0)
        remaining = self.daily_limit - daily_count

        return {
            "today_searches": daily_count,
            "daily_limit": self.daily_limit,
            "remaining_today": remaining,
            "total_searches": usage_data.get("total_searches", 0),
            "percentage_used": (daily_count / self.daily_limit) * 100,
            "status": "OK" if daily_count < self.daily_limit * 0.8 else "Warning" if daily_count < self.daily_limit else "Limit Reached"
        }


# Backward compatibility wrapper functions
async def google_cse_search(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Backward compatible search function that returns results in the same format
    as the original DuckDuckGo implementation for seamless integration.
    """
    try:
        async with GoogleCSESearch() as search:
            results = await search.search(query, max_results)

            # Convert to the expected format for backward compatibility
            return [
                {
                    "title": result.title,
                    "url": result.url,
                    "snippet": result.snippet,
                    "type": "organic"
                }
                for result in results
            ]

    except GoogleCSESearchError as e:
        print(f"❌ Google CSE search failed: {e}")
        return []
    except Exception as e:
        print(f"❌ Unexpected search error: {e}")
        return []


async def test_google_cse():
    """Test the Google Custom Search implementation"""
    print("🧪 Testing Google Custom Search Integration")
    print("=" * 50)

    try:
        async with GoogleCSESearch() as search:
            # Test usage stats
            stats = search.get_usage_stats()
            print(f"📊 Usage Stats: {stats['today_searches']}/{stats['daily_limit']} searches today")

            # Test searches
            test_queries = [
                "Boston Dynamics Stretch robot latest updates",
                "machine learning artificial intelligence",
                "Python programming tutorial"
            ]

            for query in test_queries:
                print(f"\n🔍 Testing: '{query}'")
                results = await search.search(query, num_results=3)

                if results:
                    for i, result in enumerate(results, 1):
                        print(f"  {i}. {result.title}")
                        print(f"     {result.url}")
                        print(f"     {result.snippet[:100]}...")
                else:
                    print("  No results found")

                # Small delay between searches
                await asyncio.sleep(1)

            # Final usage stats
            final_stats = search.get_usage_stats()
            print(f"\n📈 Final Usage: {final_stats['today_searches']}/{final_stats['daily_limit']} searches today")

    except GoogleCSESearchError as e:
        print(f"❌ Google CSE Error: {e}")
        print("\n💡 Setup Instructions:")
        print("1. Get API key: https://console.cloud.google.com/apis/credentials")
        print("2. Create custom search engine: https://cse.google.com/cse/all")
        print("3. Add to .env file:")
        print("   GOOGLE_CSE_API_KEY=your_api_key_here")
        print("   GOOGLE_CSE_ENGINE_ID=your_engine_id_here")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(test_google_cse())