# Sprout Social MCP

Pulls post copy and engagement metrics from Sprout's Reporting API straight into
a Claude session, so nobody has to export a report by hand and paste it into
Notion again.

Built for the SSS Lighthouse content workflow: voice analysis, performance
archives, and copywriter briefing packs all need the same thing, which is what a
post said next to how it did.

## Before you start

Two hard requirements, both on the Sprout side:

1. **The Reporting API needs the Premium Analytics add-on.** It is not on the
   base plan. If your token comes back `403`, this is why. Confirm the account
   tier before debugging anything else.
2. **Network access to `api.sproutsocial.com`.** Run this on a machine that can
   reach it. Sandboxed and remote environments frequently cannot, and the
   server will tell you so rather than hanging.

## Setup

```bash
cd sprout-mcp
python3 -m venv .venv
.venv/bin/pip install -e .
cp .env.example .env      # then paste your token in
```

Get the token from Sprout: **Settings → API Access → generate token**. Copy it
immediately, it is shown once.

`SPROUT_CUSTOMER_ID` is optional. Left blank, the server resolves it from
`/metadata/client` on the first call.

## Wire it into Claude

Add to your MCP config (`claude_desktop_config.json`, or `.mcp.json` for Claude
Code), using absolute paths:

```json
{
  "mcpServers": {
    "sprout-social": {
      "command": "/absolute/path/to/sprout-mcp/.venv/bin/python",
      "args": ["-m", "sprout_mcp.server"],
      "env": {
        "SPROUT_API_TOKEN": "your-token-here"
      }
    }
  }
}
```

Restart Claude. You should see five `sprout_*` tools.

## Tools

| Tool | What it does |
|---|---|
| `sprout_whoami` | Confirms the token works, returns the customer id. Run this first. |
| `sprout_list_profiles` | Lists connected profiles with their ids. You need these to filter. |
| `sprout_get_posts` | The main one. Post text plus engagement metrics, sorted by engagement. |
| `sprout_get_profile_analytics` | Account-level: followers, impressions, growth, volume. |
| `sprout_export_posts_csv` | Writes posts to a CSV for handing to a copywriter. |

### Typical run

```
sprout_whoami                          → confirm the token
sprout_list_profiles                   → grab the LinkedIn customer_profile_id
sprout_get_posts(profile_ids=[12345],
                 days_back=90)         → the last 90 days, best first
```

## On metric names

The default metric set is the one that matters for written-content work:

```
lifetime.impressions      lifetime.reach          lifetime.engagements_total
lifetime.reactions        lifetime.comments_count lifetime.shares_count
lifetime.post_link_clicks
```

**Verify these against your own account on the first run.** Sprout's available
metrics vary by network and by plan, and a metric your plan does not carry is
rejected for the whole request. When that happens Sprout names the offending
metric in the error body, which the server passes through verbatim. Drop it from
the `metrics` argument and re-run.

Same caution applies to the filter syntax if Sprout revises the API. The two
filters used here are `created_time.in(START..END)` and
`customer_profile_id.eq(id,id)`.

## Errors

Every tool returns a readable message instead of raising, so a failure does not
blow up the session:

| Status | Meaning |
|---|---|
| `0` | Never reached Sprout. Network, VPN, or proxy. |
| `401` | Token rejected. Regenerate it. |
| `403` | Token valid, plan lacks Reporting API access. |
| `404` | Bad customer id. Run `sprout_whoami`. |
| `429` | Rate limited. Retry with a smaller `max_records`. |

## Known limits

- Read-only. No publishing or scheduling, by design.
- Sprout pages at 100 records per request; `max_records` walks the pages for you.
- Analytics cover profiles connected to Sprout at the time the post went out.
  Posts published before a profile was connected will not appear.
