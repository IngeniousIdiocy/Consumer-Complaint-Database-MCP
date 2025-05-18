"""
complaints.py – local-only MCP server for querying U.S. CFPB consumer-complaint data.

This file is a refactor of the original `server.py`.  The **only** transport
it supports is stdio, so tools like Claude Desktop can launch it directly
without exposing an HTTP port.

Dependencies (declare these in pyproject.toml or install with uv/pip):
    mcp[cli] >= 1.2.0
    httpx >= 0.27.0               # async HTTP client (could be requests if you prefer)
    python-dateutil >= 2.9.0      # for robust date parsing

Typical one-time setup (from the project root -– see earlier explanation):
    uv add "mcp[cli]" httpx python-dateutil
    uv run complaints.py          # smoke test – waits for stdin/stdout client
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import Annotated, List, Optional

import httpx
from dateutil import parser as date_parser
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

# --------------------------------------------------------------------------- #
# 1.  MCP server instance
# --------------------------------------------------------------------------- #

mcp = FastMCP(
    "Banking Complaints",
    description=(
        "Use this server whenever you need data from the CFPB Consumer Complaint "
        "Database.  Tip: pass the company name *exactly* as it appears in the "
        "CFPB 'company' field (e.g., 'PNC Bank N.A.')."
    ),
)


# --------------------------------------------------------------------------- #
# 2.  Internal helpers
# --------------------------------------------------------------------------- #

_CFPB_ENDPOINT = (
    "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
)


@dataclass(slots=True)
class Complaint:
    complaint_id: str
    date_received: str
    date_sent_to_company: str | None
    product: str
    sub_product: str | None
    issue: str
    sub_issue: str | None
    consumer_complaint_narrative: str
    consumer_consent_provided: str | None
    company: str
    company_public_response: str | None
    company_response_to_consumer: str | None
    timely_response: str | None
    consumer_disputed: str | None
    state: str | None
    zip_code: str | None
    submitted_via: str | None
    tags: list[str] | None

    @classmethod
    def from_json(cls, item: dict) -> "Complaint":
        attrs = {
            "complaint_id": item.get("complaint_id"),
            "date_received": item.get("date_received"),
            "date_sent_to_company": item.get("date_sent_to_company"),
            "product": item.get("product"),
            "sub_product": item.get("sub_product"),
            "issue": item.get("issue"),
            "sub_issue": item.get("sub_issue"),
            "consumer_complaint_narrative": item.get("consumer_complaint_narrative") or "",
            "consumer_consent_provided": item.get("consumer_consent_provided"),
            "company": item.get("company"),
            "company_public_response": item.get("company_public_response"),
            "company_response_to_consumer": item.get("company_response_to_consumer"),
            "timely_response": item.get("timely_response"),
            "consumer_disputed": item.get("consumer_disputed"),
            "state": item.get("state"),
            "zip_code": item.get("zip_code"),
            "submitted_via": item.get("submitted_via"),
            "tags": item.get("tags"),
        }
        return cls(**attrs)


async def _fetch_cfpb(params: dict) -> List[Complaint]:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(_CFPB_ENDPOINT, params=params)
        if resp.status_code != 200:
            raise ToolError(f"CFPB API error {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        results = data.get("hits", {}).get("hits", [])
        return [Complaint.from_json(hit["_source"]) for hit in results]


def _date_to_iso(date_like: str | _dt.date | None) -> Optional[str]:
    if date_like is None:
        return None
    if isinstance(date_like, _dt.date):
        return date_like.isoformat()
    return date_parser.parse(str(date_like)).date().isoformat()


# --------------------------------------------------------------------------- #
# 3.  Public MCP tool
# --------------------------------------------------------------------------- #

@mcp.tool(
    name="search_complaints",
    description=(
        "Search the U.S. Consumer Financial Protection Bureau public complaint "
        "database and return recent complaints as structured objects."
        "  Pass `narrative_only=true` if you need complaints that include consumer narrative text."
    ),
)
async def search_complaints(
    *,
    text: Annotated[
        str | None,
        "Full-text query (matched across narrative, product, and issue fields).  "
        "Leave blank to fetch most recent complaints.",
    ] = None,
    company: Annotated[
        str | None,
        "Exact company string as shown in the CFPB database.  Common examples: "
        "'JPMorgan Chase Bank, N.A.', 'Bank of America, N.A.', 'Wells Fargo Bank, N.A.', "
        "'Citibank, N.A.', 'U.S. Bank National Association', 'PNC Bank, N.A.', "
        "'Truist Bank', 'Goldman Sachs Bank USA', 'TD Bank, N.A.', "
        "'Capital One Bank (USA), N.A.', 'Charles Schwab Bank, SSB', "
        "'Fifth Third Bank, National Association', 'The Bank of New York Mellon', "
        "'State Street Bank and Trust Company', 'BMO Bank N.A.', 'Ally Bank', "
        "'Citizens Bank, N.A.', 'Regions Bank', 'KeyBank National Association', "
        "'Huntington National Bank'."
    ] = None,
    product: Annotated[
        str | None,
        "Exact CFPB product category (e.g., 'Mortgage', 'Credit card', 'Auto loan or lease', "
        "'Checking or savings account')."
    ] = None,
    since: Annotated[
        str | None,
        "Only return complaints received **on or after** this date "
        "(ISO 8601, e.g., '2024-01-01').  Mutually exclusive with `days`.",
    ] = None,
    days: Annotated[
        int | None,
        "Shorthand to set `since` to N days ago (e.g., 30).  "
        "Ignored if `since` is provided.",
    ] = 30,
    size: Annotated[
        int,
        "Maximum number of results to return (1 – 100).",
    ] = 20,
    narrative_only: Annotated[
        bool,
        "Set to `true` to return only complaints that include consumer narrative text."
    ] = False,
) -> List[Complaint]:
    """
    Query parameters mirror the public CFPB API.

    Returns
    -------
    List[Complaint]
        Up to `size` complaint objects sorted by date_received descending.
    """
    if not (1 <= size <= 100):
        raise ToolError("`size` must be between 1 and 100")

    if since and days:
        raise ToolError("Provide either `since` **or** `days`, not both")

    # Resolve date filter
    if since:
        since_iso = _date_to_iso(since)
    else:
        since_iso = _date_to_iso(_dt.date.today() - _dt.timedelta(days=days or 0))

    # Build search params
    es_query: dict[str, object] = {
        "size": size,
        "sort": "created_date_desc",
    }

    # Map parameters to CFPB API query fields
    if text:
        es_query["search_term"] = text
        es_query["field"] = "all"
    if company:
        es_query["company"] = company
    if product:
        es_query["product"] = product
    if since_iso:
        es_query["date_received_min"] = since_iso
    if narrative_only:
        es_query["has_narrative"] = "true"

    return await _fetch_cfpb(es_query)


# --------------------------------------------------------------------------- #
# 4.  Entrypoint (stdio transport only)
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    # Claude Desktop (and any other stdio-aware client) will exec:
    #     uv run complaints.py
    # which drops us into this launcher.
    mcp.run(transport="stdio")
