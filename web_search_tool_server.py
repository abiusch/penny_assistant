"""
Web Search Tool Server
Provides secure web search and browsing capabilities with comprehensive rate limiting
"""

import asyncio
import json
import re
import time
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import aiohttp
import aiosqlite
from bs4 import BeautifulSoup

from tool_server_foundation import (
    BaseToolServer, ToolServerType, SecurityLevel, SecurityContext,
    ToolOperation, ToolOperationResult, ToolServerSecurityError,
    ToolServerRateLimitError
)


class WebSearchToolServer(BaseToolServer):
    """Web search tool server with rate limiting and security"""

    def __init__(self, *args, **kwargs):
        super().__init__(ToolServerType.WEB_SEARCH, *args, **kwargs)

        # Search configuration
        self.search_engines = {
            "duckduckgo": {
                "url": "https://api.duckduckgo.com/",
                "params": {"format": "json", "no_html": "1", "skip_disambig": "1"}
            },
            "serp": {
                "url": "https://serpapi.com/search",
                "requires_api_key": True
            }
        }

        # Rate limiting configuration
        self.rate_limits = {
            "search": {"requests": 50, "window": 3600},  # 50 searches per hour
            "browse": {"requests": 100, "window": 3600},  # 100 page views per hour
            "download": {"requests": 10, "window": 3600, "bytes": 50 * 1024 * 1024}  # 10 downloads, 50MB per hour
        }

        # Security configuration
        self.allowed_domains = set()  # Empty = all allowed, populated = whitelist
        self.blocked_domains = {
            "localhost", "127.0.0.1", "0.0.0.0", "::1",
            "169.254.0.0/16", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"
        }
        self.max_page_size = 10 * 1024 * 1024  # 10MB
        self.max_search_results = 100
        self.request_timeout = 30

        # Content filtering
        self.blocked_content_types = {
            "application/octet-stream", "application/x-msdownload",
            "application/x-executable", "application/vnd.microsoft.portable-executable"
        }

    async def _load_configuration(self):
        """Load web search specific configuration"""
        # Load API keys and configuration from environment or database
        await self._load_api_keys()
        await self._setup_content_filters()

    async def _load_api_keys(self):
        """Load API keys for search engines"""
        # Load from database or environment variables
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    service TEXT PRIMARY KEY,
                    api_key TEXT,
                    created_at TEXT,
                    last_used TEXT
                )
            """)
            await db.commit()

    async def _setup_content_filters(self):
        """Setup content filtering rules"""
        # Additional security setup for web content
        pass

    async def _execute_specific_operation(self,
                                        operation_name: str,
                                        parameters: Dict[str, Any],
                                        security_context: SecurityContext) -> Dict[str, Any]:
        """Execute web search specific operations"""

        operation_map = {
            "search": self._search,
            "browse_page": self._browse_page,
            "extract_links": self._extract_links,
            "download_file": self._download_file,
            "get_page_metadata": self._get_page_metadata,
            "check_url_safety": self._check_url_safety,
            "search_images": self._search_images,
            "get_search_suggestions": self._get_search_suggestions
        }

        if operation_name not in operation_map:
            raise ValueError(f"Unknown web search operation: {operation_name}")

        # Check rate limits
        await self._check_operation_rate_limit(operation_name, security_context.user_id)

        return await operation_map[operation_name](parameters, security_context)

    async def _determine_security_level(self, operation_name: str, parameters: Dict[str, Any]) -> SecurityLevel:
        """Determine security level for web operations"""

        # High-risk operations
        if operation_name in ["download_file"]:
            return SecurityLevel.HIGH

        # Medium-risk operations
        if operation_name in ["browse_page", "extract_links"]:
            return SecurityLevel.MEDIUM

        # Low-risk operations
        if operation_name in ["search", "get_search_suggestions", "check_url_safety", "get_page_metadata"]:
            return SecurityLevel.LOW

        return SecurityLevel.MEDIUM

    async def _requires_rollback(self, operation_name: str) -> bool:
        """Web operations typically don't require rollback"""
        return False

    async def _create_rollback_data(self, operation: ToolOperation, result_data: Dict[str, Any]) -> str:
        """Web operations don't create rollback data"""
        return ""

    async def _execute_rollback(self, rollback_type: str, rollback_data: Dict[str, Any]) -> bool:
        """Web operations don't support rollback"""
        return True

    async def _check_operation_rate_limit(self, operation_name: str, user_id: Optional[str]):
        """Check rate limits for specific operation types"""
        if not user_id:
            return

        operation_type = self._get_operation_type(operation_name)
        if operation_type not in self.rate_limits:
            return

        limit_config = self.rate_limits[operation_type]
        current_time = datetime.now()
        window_start = current_time - timedelta(seconds=limit_config["window"])

        async with aiosqlite.connect(self.db_path) as db:
            # Count requests in current window
            async with db.execute("""
                SELECT COUNT(*) FROM tool_operations
                WHERE user_id = ? AND tool_type = ? AND operation_name = ?
                AND timestamp > ?
            """, (user_id, self.server_type.value, operation_name, window_start.isoformat())) as cursor:
                count = (await cursor.fetchone())[0]

                if count >= limit_config["requests"]:
                    raise ToolServerRateLimitError(
                        f"Rate limit exceeded for {operation_type}: {count}/{limit_config['requests']} requests"
                    )

    def _get_operation_type(self, operation_name: str) -> str:
        """Map operation names to rate limit categories"""
        mapping = {
            "search": "search",
            "search_images": "search",
            "get_search_suggestions": "search",
            "browse_page": "browse",
            "extract_links": "browse",
            "get_page_metadata": "browse",
            "check_url_safety": "browse",
            "download_file": "download"
        }
        return mapping.get(operation_name, "browse")

    def _validate_url(self, url: str) -> str:
        """Validate and sanitize URL"""
        if not url:
            raise ToolServerSecurityError("URL cannot be empty")

        # Parse URL
        try:
            parsed = urllib.parse.urlparse(url)
        except Exception:
            raise ToolServerSecurityError("Invalid URL format")

        # Check scheme
        if parsed.scheme not in ["http", "https"]:
            raise ToolServerSecurityError("Only HTTP/HTTPS URLs allowed")

        # Check domain blocking
        domain = parsed.netloc.lower()
        for blocked in self.blocked_domains:
            if domain == blocked or domain.endswith(f".{blocked}"):
                raise ToolServerSecurityError(f"Domain blocked: {domain}")

        # Check domain whitelist if configured
        if self.allowed_domains:
            allowed = False
            for allowed_domain in self.allowed_domains:
                if domain == allowed_domain or domain.endswith(f".{allowed_domain}"):
                    allowed = True
                    break
            if not allowed:
                raise ToolServerSecurityError(f"Domain not in whitelist: {domain}")

        return url

    async def _search(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Perform web search"""
        query = parameters.get("query", "").strip()
        engine = parameters.get("engine", "duckduckgo")
        max_results = min(parameters.get("max_results", 10), self.max_search_results)

        if not query:
            raise ValueError("Search query cannot be empty")

        if len(query) > 500:
            raise ToolServerSecurityError("Search query too long")

        # Sanitize query
        query = re.sub(r'[<>"\']', '', query)

        if engine not in self.search_engines:
            raise ValueError(f"Unknown search engine: {engine}")

        search_config = self.search_engines[engine]

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.request_timeout)) as session:
                if engine == "duckduckgo":
                    results = await self._search_duckduckgo(session, query, max_results)
                else:
                    results = await self._search_serp(session, query, max_results, search_config)

                return {
                    "query": query,
                    "engine": engine,
                    "results": results,
                    "total_results": len(results),
                    "timestamp": datetime.now().isoformat()
                }

        except asyncio.TimeoutError:
            raise ToolServerSecurityError("Search request timed out")
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            raise

    async def _search_duckduckgo(self, session: aiohttp.ClientSession, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo API"""
        url = self.search_engines["duckduckgo"]["url"]
        params = {
            **self.search_engines["duckduckgo"]["params"],
            "q": query
        }

        async with session.get(url, params=params) as response:
            if response.status != 200:
                raise ToolServerSecurityError(f"Search API error: {response.status}")

            data = await response.json()
            results = []

            # Process abstract
            if data.get("Abstract"):
                results.append({
                    "title": data.get("Heading", "Abstract"),
                    "url": data.get("AbstractURL", ""),
                    "snippet": data.get("Abstract", ""),
                    "type": "abstract"
                })

            # Process related topics
            for topic in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(topic, dict) and "Text" in topic:
                    results.append({
                        "title": topic.get("Text", "").split(" - ")[0],
                        "url": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", ""),
                        "type": "related"
                    })

            return results[:max_results]

    async def _search_serp(self, session: aiohttp.ClientSession, query: str, max_results: int, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search using SERP API (requires API key)"""
        # Load API key
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT api_key FROM api_keys WHERE service = 'serp'") as cursor:
                row = await cursor.fetchone()
                if not row:
                    raise ToolServerSecurityError("SERP API key not configured")
                api_key = row[0]

        params = {
            "q": query,
            "api_key": api_key,
            "num": max_results,
            "engine": "google"
        }

        async with session.get(config["url"], params=params) as response:
            if response.status != 200:
                raise ToolServerSecurityError(f"SERP API error: {response.status}")

            data = await response.json()
            results = []

            for result in data.get("organic_results", []):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "type": "organic"
                })

            return results

    async def _browse_page(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Browse and extract content from web page"""
        url = self._validate_url(parameters.get("url", ""))
        extract_text = parameters.get("extract_text", True)
        extract_links = parameters.get("extract_links", False)
        follow_redirects = parameters.get("follow_redirects", True)

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.request_timeout)) as session:
                async with session.get(url, allow_redirects=follow_redirects) as response:
                    # Check content type
                    content_type = response.headers.get("content-type", "").lower()
                    if any(blocked in content_type for blocked in self.blocked_content_types):
                        raise ToolServerSecurityError(f"Blocked content type: {content_type}")

                    # Check content length
                    content_length = int(response.headers.get("content-length", 0))
                    if content_length > self.max_page_size:
                        raise ToolServerSecurityError(f"Page too large: {content_length} bytes")

                    if response.status != 200:
                        return {
                            "url": url,
                            "status": response.status,
                            "error": f"HTTP {response.status}",
                            "accessible": False
                        }

                    content = await response.text()

                    # Check actual content size
                    if len(content.encode('utf-8')) > self.max_page_size:
                        raise ToolServerSecurityError("Page content too large")

                    result = {
                        "url": str(response.url),
                        "original_url": url,
                        "status": response.status,
                        "content_type": content_type,
                        "content_length": len(content),
                        "accessible": True,
                        "headers": dict(response.headers)
                    }

                    if extract_text:
                        soup = BeautifulSoup(content, 'html.parser')

                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()

                        # Extract text
                        text = soup.get_text()
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        text = ' '.join(chunk for chunk in chunks if chunk)

                        result["text"] = text
                        result["title"] = soup.title.string if soup.title else ""

                    if extract_links:
                        soup = BeautifulSoup(content, 'html.parser')
                        links = []
                        for link in soup.find_all('a', href=True):
                            absolute_url = urllib.parse.urljoin(str(response.url), link['href'])
                            links.append({
                                "url": absolute_url,
                                "text": link.get_text().strip(),
                                "title": link.get("title", "")
                            })
                        result["links"] = links

                    return result

        except asyncio.TimeoutError:
            raise ToolServerSecurityError("Page request timed out")
        except Exception as e:
            self.logger.error(f"Browse page failed: {e}")
            raise

    async def _extract_links(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Extract all links from a web page"""
        # Reuse browse_page with link extraction enabled
        params = {**parameters, "extract_text": False, "extract_links": True}
        result = await self._browse_page(params, security_context)

        return {
            "url": result["url"],
            "links": result.get("links", []),
            "total_links": len(result.get("links", [])),
            "status": result["status"]
        }

    async def _download_file(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Download file from URL"""
        url = self._validate_url(parameters.get("url", ""))
        max_size = min(parameters.get("max_size", 10 * 1024 * 1024), 100 * 1024 * 1024)  # Cap at 100MB

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.request_timeout)) as session:
                async with session.get(url) as response:
                    # Check content type
                    content_type = response.headers.get("content-type", "").lower()
                    if any(blocked in content_type for blocked in self.blocked_content_types):
                        raise ToolServerSecurityError(f"Blocked content type: {content_type}")

                    # Check content length
                    content_length = int(response.headers.get("content-length", 0))
                    if content_length > max_size:
                        raise ToolServerSecurityError(f"File too large: {content_length} bytes")

                    if response.status != 200:
                        return {
                            "url": url,
                            "status": response.status,
                            "error": f"HTTP {response.status}",
                            "downloaded": False
                        }

                    # Download content
                    content = await response.read()

                    # Check actual size
                    if len(content) > max_size:
                        raise ToolServerSecurityError("Downloaded content too large")

                    return {
                        "url": str(response.url),
                        "original_url": url,
                        "status": response.status,
                        "content_type": content_type,
                        "size": len(content),
                        "content": content.hex(),  # Return as hex for binary safety
                        "downloaded": True,
                        "headers": dict(response.headers)
                    }

        except asyncio.TimeoutError:
            raise ToolServerSecurityError("Download request timed out")
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            raise

    async def _get_page_metadata(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Get metadata about a web page"""
        url = self._validate_url(parameters.get("url", ""))

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.request_timeout)) as session:
                async with session.head(url, allow_redirects=True) as response:
                    result = {
                        "url": str(response.url),
                        "original_url": url,
                        "status": response.status,
                        "headers": dict(response.headers),
                        "accessible": response.status == 200
                    }

                    if response.status == 200:
                        # Extract useful metadata from headers
                        result.update({
                            "content_type": response.headers.get("content-type", ""),
                            "content_length": int(response.headers.get("content-length", 0)),
                            "last_modified": response.headers.get("last-modified", ""),
                            "server": response.headers.get("server", ""),
                            "cache_control": response.headers.get("cache-control", "")
                        })

                    return result

        except asyncio.TimeoutError:
            raise ToolServerSecurityError("Metadata request timed out")
        except Exception as e:
            self.logger.error(f"Get metadata failed: {e}")
            raise

    async def _check_url_safety(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Check URL safety and accessibility"""
        url = parameters.get("url", "")

        try:
            # Validate URL format
            self._validate_url(url)
            url_valid = True
            validation_error = None
        except Exception as e:
            url_valid = False
            validation_error = str(e)

        result = {
            "url": url,
            "valid": url_valid,
            "validation_error": validation_error,
            "timestamp": datetime.now().isoformat()
        }

        if url_valid:
            try:
                # Test accessibility
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.head(url, allow_redirects=True) as response:
                        result.update({
                            "accessible": response.status == 200,
                            "final_url": str(response.url),
                            "status_code": response.status,
                            "redirected": str(response.url) != url
                        })
            except Exception as e:
                result.update({
                    "accessible": False,
                    "error": str(e)
                })

        return result

    async def _search_images(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Search for images (simplified implementation)"""
        query = parameters.get("query", "").strip()
        max_results = min(parameters.get("max_results", 10), 50)

        if not query:
            raise ValueError("Image search query cannot be empty")

        # For this implementation, return placeholder data
        # In production, integrate with actual image search APIs
        return {
            "query": query,
            "results": [],
            "message": "Image search not implemented in demo version",
            "total_results": 0,
            "timestamp": datetime.now().isoformat()
        }

    async def _get_search_suggestions(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Get search suggestions for a query"""
        query = parameters.get("query", "").strip()
        max_suggestions = min(parameters.get("max_suggestions", 10), 20)

        if not query:
            raise ValueError("Query cannot be empty")

        # For this implementation, return placeholder data
        # In production, integrate with search suggestion APIs
        return {
            "query": query,
            "suggestions": [f"{query} suggestion {i}" for i in range(1, min(max_suggestions + 1, 6))],
            "total_suggestions": min(max_suggestions, 5),
            "timestamp": datetime.now().isoformat()
        }