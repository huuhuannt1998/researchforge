"""
Search service — Semantic Scholar paper search.

Provides a simple async interface to the Semantic Scholar Graph API
for finding and retrieving academic papers.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings

log = logging.getLogger(__name__)

# Shared client
_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=settings.SEMANTIC_SCHOLAR_API_URL,
            timeout=httpx.Timeout(60.0, connect=15.0),
        )
    return _client


async def close() -> None:
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None


# -------------------------------------------------------------------------
# Paper search
# -------------------------------------------------------------------------

PAPER_FIELDS = "paperId,title,authors,year,venue,abstract,url,citationCount,openAccessPdf,externalIds"


async def search_papers(
    query: str,
    *,
    limit: int | None = None,
    year: str | None = None,
) -> List[Dict[str, Any]]:
    """Search Semantic Scholar for papers matching *query*.

    Parameters
    ----------
    query : str
        Free-text search query.
    limit : int | None
        Number of results to return (defaults to ``settings.PAPER_SEARCH_LIMIT``).
    year : str | None
        Optional year filter, e.g. ``"2020-"`` or ``"2018-2023"``.

    Returns
    -------
    list[dict] — Each dict has keys:
        paper_id, title, authors (list[str]), year, venue, abstract, url,
        citation_count, pdf_url, doi
    """
    client = _get_client()
    params: Dict[str, Any] = {
        "query": query,
        "limit": limit or settings.PAPER_SEARCH_LIMIT,
        "fields": PAPER_FIELDS,
    }
    if year:
        params["year"] = year

    log.info("Semantic Scholar search: %r (limit=%s)", query, params["limit"])
    resp = await client.get("/paper/search", params=params)
    resp.raise_for_status()
    data = resp.json()

    results: List[Dict[str, Any]] = []
    for paper in data.get("data", []):
        authors = [a.get("name", "") for a in (paper.get("authors") or [])]
        pdf_url = None
        if paper.get("openAccessPdf"):
            pdf_url = paper["openAccessPdf"].get("url")
        doi = None
        if paper.get("externalIds"):
            doi = paper["externalIds"].get("DOI")
        results.append({
            "paper_id": paper.get("paperId"),
            "title": paper.get("title", ""),
            "authors": authors,
            "year": paper.get("year"),
            "venue": paper.get("venue", ""),
            "abstract": paper.get("abstract", ""),
            "url": paper.get("url", ""),
            "citation_count": paper.get("citationCount", 0),
            "pdf_url": pdf_url,
            "doi": doi,
        })
    log.info("Found %d papers", len(results))
    return results


async def get_paper(paper_id: str) -> Dict[str, Any] | None:
    """Fetch a single paper by its Semantic Scholar ID."""
    client = _get_client()
    resp = await client.get(f"/paper/{paper_id}", params={"fields": PAPER_FIELDS})
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    paper = resp.json()
    authors = [a.get("name", "") for a in (paper.get("authors") or [])]
    pdf_url = None
    if paper.get("openAccessPdf"):
        pdf_url = paper["openAccessPdf"].get("url")
    doi = None
    if paper.get("externalIds"):
        doi = paper["externalIds"].get("DOI")
    return {
        "paper_id": paper.get("paperId"),
        "title": paper.get("title", ""),
        "authors": authors,
        "year": paper.get("year"),
        "venue": paper.get("venue", ""),
        "abstract": paper.get("abstract", ""),
        "url": paper.get("url", ""),
        "citation_count": paper.get("citationCount", 0),
        "pdf_url": pdf_url,
        "doi": doi,
    }
