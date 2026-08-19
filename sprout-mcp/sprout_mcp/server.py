"""Sprout Social MCP server.

Exposes the Sprout Reporting API to Claude so post text and engagement data can
be pulled straight into a session, instead of exporting a report by hand and
pasting it into Notion.

Run it over stdio:  python -m sprout_mcp.server
"""

from __future__ import annotations

import csv
import io
import json
from datetime import date, timedelta
from typing import Any

from mcp.server.mcpserver import MCPServer

from .client import SproutClient, SproutError

mcp = MCPServer("sprout-social", version="0.1.0")

# The metric set that matters for written-content work: what the post said, how
# far it went, and how many people talked back. Override per call if needed.
DEFAULT_POST_METRICS = [
    "lifetime.impressions",
    "lifetime.reach",
    "lifetime.engagements_total",
    "lifetime.reactions",
    "lifetime.comments_count",
    "lifetime.shares_count",
    "lifetime.post_link_clicks",
]

DEFAULT_PROFILE_METRICS = [
    "impressions",
    "followers_count",
    "net_follower_growth",
    "engagements_total",
    "posts_sent_count",
]


def _fmt(exc: SproutError) -> str:
    """Turn a Sprout error into something actionable rather than a stack trace."""
    hints = {
        0: "Could not reach Sprout at all. Check network access to "
           "api.sproutsocial.com, including any VPN or corporate proxy. "
           "Sandboxed environments commonly block it.",
        401: "Token rejected. Regenerate it in Sprout under Settings > API Access.",
        403: "Token is valid but lacks permission. The Reporting API needs the "
             "Premium Analytics add-on on your Sprout plan.",
        404: "Path or customer id not found. Run sprout_whoami to confirm the customer id.",
        429: "Rate limited by Sprout. Wait and retry with a smaller max_records.",
    }
    hint = hints.get(exc.status, "")
    return f"Sprout API error {exc.status}\n{exc.body}\n\n{hint}".strip()


def _date_window(days_back: int) -> str:
    """Build Sprout's created_time range filter for the last N days."""
    end = date.today()
    start = end - timedelta(days=days_back)
    return f"created_time.in({start.isoformat()}T00:00:00..{end.isoformat()}T23:59:59)"


@mcp.tool()
async def sprout_whoami() -> str:
    """Confirm the API token works and return the customer id and account name.

    Run this first. Every other call is scoped by customer id, and this is the
    fastest way to tell a bad token from a bad query.
    """
    try:
        return json.dumps(await SproutClient().whoami(), indent=2)
    except SproutError as exc:
        return _fmt(exc)


@mcp.tool()
async def sprout_list_profiles() -> str:
    """List every connected social profile with its id, network and handle.

    You need the customer_profile_id from here to filter posts to one account,
    for example Syd's LinkedIn versus the agency page.
    """
    try:
        data = await SproutClient().list_profiles()
    except SproutError as exc:
        return _fmt(exc)

    profiles = data.get("data") or []
    if not profiles:
        return "No profiles returned. Check the token is scoped to the right Sprout account."

    lines = ["customer_profile_id | network | name | native_id"]
    for p in profiles:
        lines.append(
            " | ".join(
                str(p.get(k, ""))
                for k in ("customer_profile_id", "network_type", "name", "native_id")
            )
        )
    return "\n".join(lines)


@mcp.tool()
async def sprout_get_posts(
    profile_ids: list[int] | None = None,
    days_back: int = 90,
    max_records: int = 100,
    metrics: list[str] | None = None,
    sort_by_engagement: bool = True,
) -> str:
    """Pull published posts with their full text and engagement metrics.

    This is the main tool. It returns what was actually written alongside how it
    performed, which is what voice and performance analysis both need.

    Args:
        profile_ids: customer_profile_id values from sprout_list_profiles.
            Omit to pull every connected profile.
        days_back: How far back to look. 90 days is the default.
        max_records: Cap on posts returned. Sprout pages at 100 per request.
        metrics: Override the default metric set. Sprout names the offending
            metric in its error body if one is not available on your plan.
        sort_by_engagement: Return highest-engagement posts first. Set False for
            reverse-chronological.
    """
    filters = [_date_window(days_back)]
    if profile_ids:
        ids = ",".join(str(i) for i in profile_ids)
        filters.append(f"customer_profile_id.eq({ids})")

    sort = ["lifetime.engagements_total:desc"] if sort_by_engagement else None

    try:
        rows = await SproutClient().get_posts(
            filters=filters,
            metrics=metrics or DEFAULT_POST_METRICS,
            max_records=max_records,
            sort=sort,
        )
    except SproutError as exc:
        return _fmt(exc)

    if not rows:
        return (
            f"No posts found in the last {days_back} days"
            + (f" for profile(s) {profile_ids}." if profile_ids else ".")
        )

    return json.dumps(rows, indent=2, default=str)


@mcp.tool()
async def sprout_get_profile_analytics(
    profile_ids: list[int] | None = None,
    days_back: int = 90,
    metrics: list[str] | None = None,
) -> str:
    """Pull account-level analytics: followers, impressions, growth, volume.

    Use this for the account benchmarks that individual posts get measured
    against, not for post copy.
    """
    filters = [_date_window(days_back)]
    if profile_ids:
        ids = ",".join(str(i) for i in profile_ids)
        filters.append(f"customer_profile_id.eq({ids})")

    try:
        rows = await SproutClient().get_profile_analytics(
            filters=filters,
            metrics=metrics or DEFAULT_PROFILE_METRICS,
        )
    except SproutError as exc:
        return _fmt(exc)

    return json.dumps(rows, indent=2, default=str) if rows else "No analytics returned."


@mcp.tool()
async def sprout_export_posts_csv(
    output_path: str,
    profile_ids: list[int] | None = None,
    days_back: int = 180,
    max_records: int = 500,
) -> str:
    """Export posts to a CSV file: post text in one column, metrics in the rest.

    Built for handing a copywriter a single file they can sort and read, and for
    rebuilding the Notion performance archive without a manual export.
    """
    filters = [_date_window(days_back)]
    if profile_ids:
        ids = ",".join(str(i) for i in profile_ids)
        filters.append(f"customer_profile_id.eq({ids})")

    try:
        rows = await SproutClient().get_posts(
            filters=filters,
            metrics=DEFAULT_POST_METRICS,
            max_records=max_records,
            sort=["lifetime.engagements_total:desc"],
        )
    except SproutError as exc:
        return _fmt(exc)

    if not rows:
        return f"No posts found in the last {days_back} days. Nothing written."

    flat = [_flatten(r) for r in rows]
    fieldnames: list[str] = []
    for row in flat:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(flat)

    with open(output_path, "w", encoding="utf-8", newline="") as fh:
        fh.write(buf.getvalue())

    return f"Wrote {len(flat)} posts to {output_path} ({len(fieldnames)} columns)."


def _flatten(row: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten Sprout's nested metrics object into single-level CSV columns."""
    out: dict[str, Any] = {}
    for key, value in row.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            out.update(_flatten(value, prefix=f"{name}."))
        elif isinstance(value, list):
            out[name] = ", ".join(str(v) for v in value)
        else:
            out[name] = value
    return out


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
