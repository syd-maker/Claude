"""Thin async wrapper over the Sprout Social Reporting API.

Sprout's Reporting API is a small surface: a metadata endpoint that tells you
which customer id your token belongs to, a profiles endpoint, and two analytics
endpoints that take a POST body of filters + metrics. Everything here is a
direct mapping onto that.

Docs: https://api.sproutsocial.com/docs/
"""

from __future__ import annotations

import os
from typing import Any, Iterable

import httpx

BASE_URL = os.environ.get("SPROUT_BASE_URL", "https://api.sproutsocial.com/v1")
DEFAULT_TIMEOUT = 60.0

# Sprout caps page size at 100 for the analytics endpoints.
MAX_PAGE_SIZE = 100


class SproutError(RuntimeError):
    """Raised when Sprout returns a non-2xx response.

    Carries the response body, because Sprout's error payloads name the exact
    offending filter or metric and that is the fastest way to fix a call.
    """

    def __init__(self, status: int, body: str, url: str) -> None:
        self.status = status
        self.body = body
        self.url = url
        super().__init__(f"Sprout API {status} on {url}\n{body}")


class SproutClient:
    def __init__(self, token: str | None = None, customer_id: str | None = None) -> None:
        self._token = token or os.environ.get("SPROUT_API_TOKEN")
        if not self._token:
            raise SproutError(
                401,
                "No API token. Set SPROUT_API_TOKEN in the environment. "
                "Find it in Sprout under Settings > API Access "
                "(requires the Premium Analytics add-on).",
                BASE_URL,
            )
        self._customer_id = customer_id or os.environ.get("SPROUT_CUSTOMER_ID")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{BASE_URL}{path}"
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as http:
                resp = await http.request(method, url, headers=self._headers(), **kwargs)
        except httpx.HTTPError as exc:
            # Never reached Sprout at all: DNS, TLS, timeout, or a proxy in the
            # way. Status 0 marks it as a transport failure, not an API refusal.
            raise SproutError(0, f"{type(exc).__name__}: {exc}", url) from exc
        if resp.status_code >= 400:
            raise SproutError(resp.status_code, resp.text, url)
        return resp.json()

    async def resolve_customer_id(self) -> str:
        """Return the customer id, fetching it from /metadata/client if unset.

        Sprout scopes every analytics path by customer id, so this runs before
        anything else. The result is cached on the instance.
        """
        if self._customer_id:
            return self._customer_id
        data = await self._request("GET", "/metadata/client")
        customers = data.get("data") or []
        if not customers:
            raise SproutError(
                404,
                "Token is valid but is not attached to any customer. "
                "Check the token was generated for the right Sprout account.",
                f"{BASE_URL}/metadata/client",
            )
        self._customer_id = str(customers[0]["customer_id"])
        return self._customer_id

    async def whoami(self) -> dict[str, Any]:
        return await self._request("GET", "/metadata/client")

    async def list_profiles(self) -> dict[str, Any]:
        cid = await self.resolve_customer_id()
        return await self._request("GET", f"/{cid}/metadata/customer")

    async def _paged_analytics(
        self,
        endpoint: str,
        filters: Iterable[str],
        metrics: Iterable[str],
        max_records: int,
        sort: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Walk Sprout's paged analytics response until max_records or exhaustion."""
        cid = await self.resolve_customer_id()
        collected: list[dict[str, Any]] = []
        page = 1

        while len(collected) < max_records:
            body: dict[str, Any] = {
                "filters": list(filters),
                "metrics": list(metrics),
                "page": page,
                "limit": min(MAX_PAGE_SIZE, max_records - len(collected)),
            }
            if sort:
                body["sort"] = sort

            payload = await self._request("POST", f"/{cid}/analytics/{endpoint}", json=body)
            rows = payload.get("data") or []
            collected.extend(rows)

            paging = payload.get("paging") or {}
            total_pages = paging.get("total_pages")
            # Stop on a short page too: Sprout omits paging metadata on some plans.
            if not rows or (total_pages is not None and page >= total_pages):
                break
            page += 1

        return collected[:max_records]

    async def get_posts(
        self,
        filters: Iterable[str],
        metrics: Iterable[str],
        max_records: int = 200,
        sort: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        return await self._paged_analytics("posts", filters, metrics, max_records, sort)

    async def get_profile_analytics(
        self,
        filters: Iterable[str],
        metrics: Iterable[str],
        max_records: int = 200,
    ) -> list[dict[str, Any]]:
        return await self._paged_analytics("profiles", filters, metrics, max_records)
