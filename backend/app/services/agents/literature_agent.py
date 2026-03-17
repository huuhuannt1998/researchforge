"""
Literature Agent
================
1. Build search queries from the project's research question / short idea.
2. Search Semantic Scholar for relevant papers.
3. For each paper, use the LLM to extract key findings.
4. Store results as LiteratureItem + EvidenceCard records.
5. Ask the LLM for a synthesis / literature-review summary.
"""
from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.literature import EvidenceCard, LiteratureItem
from app.models.pipeline import PipelineRun
from app.models.project import Project, ResearchQuestion
from app.services import llm_service, pipeline_service, search_service

log = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Prompt templates
# -------------------------------------------------------------------------

QUERY_GEN_SYSTEM = (
    "You are a research assistant. Given a research topic and question, "
    "generate 3 diverse academic search queries that would find the most "
    "relevant papers. Return a JSON object: {\"queries\": [\"q1\", \"q2\", \"q3\"]}"
)

PAPER_ANALYSIS_SYSTEM = (
    "You are a meticulous research analyst. Given a paper's title, abstract, "
    "and metadata, extract the following as a JSON object:\n"
    "{\n"
    '  "summary": "2-3 sentence summary of key contribution",\n'
    '  "methods": ["method1", "method2"],\n'
    '  "datasets": ["dataset1"],\n'
    '  "metrics": ["metric1"],\n'
    '  "limitations": ["limitation1"],\n'
    '  "key_claims": [\n'
    '    {"claim": "...", "evidence_type": "empirical|theoretical|benchmark|survey|other", "confidence": 0.8}\n'
    "  ]\n"
    "}"
)

SYNTHESIS_SYSTEM = (
    "You are a senior researcher writing a literature review. Given summaries "
    "of multiple papers, write a comprehensive synthesis that identifies:\n"
    "1. Main themes and trends\n"
    "2. Key methodological approaches\n"
    "3. Gaps in existing research\n"
    "4. Opportunities for novel contributions\n\n"
    "Write 3-5 paragraphs in academic style."
)


# -------------------------------------------------------------------------
# Main runner
# -------------------------------------------------------------------------

async def run(db: Session, project_id: UUID, run_record: PipelineRun) -> None:
    """Execute the full literature-search pipeline for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    pipeline_service.start_run(db, run_record)
    pipeline_service.append_log(db, run_record, "📚 Literature agent started")

    # Determine search topic
    topic = project.short_idea or project.title
    rq = (
        db.query(ResearchQuestion)
        .filter(ResearchQuestion.project_id == project_id)
        .first()
    )
    question_text = rq.main_question if rq else ""

    # Step 1 — Generate search queries
    pipeline_service.append_log(db, run_record, "🔍 Generating search queries…")
    queries_data = await llm_service.chat_json([
        {"role": "system", "content": QUERY_GEN_SYSTEM},
        {"role": "user", "content": f"Topic: {topic}\nResearch question: {question_text}"},
    ])
    queries = queries_data.get("queries", [topic])[:3]
    pipeline_service.append_log(db, run_record, f"   Queries: {queries}")

    # Step 2 — Search for papers
    pipeline_service.append_log(db, run_record, "🌐 Searching Semantic Scholar…")
    all_papers: list[dict] = []
    seen_ids: set[str] = set()
    for q in queries:
        try:
            papers = await search_service.search_papers(q, limit=8)
            for p in papers:
                pid = p.get("paper_id", p["title"])
                if pid not in seen_ids:
                    seen_ids.add(pid)
                    all_papers.append(p)
        except Exception as exc:
            pipeline_service.append_log(db, run_record, f"   ⚠ Search error for '{q}': {exc}")

    pipeline_service.append_log(db, run_record, f"   Found {len(all_papers)} unique papers")

    if not all_papers:
        pipeline_service.complete_run(
            db, run_record,
            result_summary="No papers found. Try a different research question.",
            result_data={"papers_found": 0},
        )
        return

    # Step 3 — Analyze each paper and store records
    pipeline_service.append_log(db, run_record, "🧠 Analyzing papers with LLM…")
    summaries_for_synthesis: list[str] = []

    for i, paper in enumerate(all_papers[:15]):  # cap at 15
        pipeline_service.append_log(
            db, run_record,
            f"   [{i+1}/{min(len(all_papers), 15)}] {paper['title'][:80]}…"
        )

        # Create LiteratureItem
        doi_or_url = paper.get("doi") or paper.get("url") or ""
        lit_item = LiteratureItem(
            project_id=project_id,
            title=paper["title"],
            authors=paper.get("authors", []),
            year=paper.get("year"),
            venue=paper.get("venue", ""),
            doi_or_url=doi_or_url,
            abstract=paper.get("abstract", ""),
            tags=["auto-discovered"],
            relevance_score=None,
        )
        db.add(lit_item)
        db.flush()  # get ID

        # LLM extraction
        try:
            user_content = (
                f"Title: {paper['title']}\n"
                f"Authors: {', '.join(paper.get('authors', []))}\n"
                f"Year: {paper.get('year', 'N/A')}\n"
                f"Venue: {paper.get('venue', 'N/A')}\n"
                f"Abstract: {paper.get('abstract', 'N/A')}"
            )
            analysis = await llm_service.chat_json([
                {"role": "system", "content": PAPER_ANALYSIS_SYSTEM},
                {"role": "user", "content": user_content},
            ])

            # Update literature item with extracted data
            lit_item.extracted_summary = analysis.get("summary", "")
            lit_item.extracted_methods = analysis.get("methods", [])
            lit_item.extracted_datasets = analysis.get("datasets", [])
            lit_item.extracted_metrics = analysis.get("metrics", [])
            lit_item.extracted_limitations = analysis.get("limitations", [])

            # Create evidence cards from claims
            for claim_data in analysis.get("key_claims", []):
                card = EvidenceCard(
                    project_id=project_id,
                    literature_item_id=lit_item.id,
                    claim=claim_data.get("claim", ""),
                    evidence_type=claim_data.get("evidence_type", "other"),
                    confidence=claim_data.get("confidence"),
                )
                db.add(card)

            summaries_for_synthesis.append(
                f"[{paper['title']}] {analysis.get('summary', paper.get('abstract', '')[:200])}"
            )
        except Exception as exc:
            pipeline_service.append_log(
                db, run_record,
                f"   ⚠ Analysis failed for '{paper['title'][:50]}': {exc}"
            )
            summaries_for_synthesis.append(
                f"[{paper['title']}] {paper.get('abstract', '')[:200]}"
            )

    db.commit()

    # Step 4 — Generate synthesis
    pipeline_service.append_log(db, run_record, "📝 Generating literature synthesis…")
    papers_text = "\n\n".join(summaries_for_synthesis)
    synthesis = await llm_service.chat([
        {"role": "system", "content": SYNTHESIS_SYSTEM},
        {"role": "user", "content": (
            f"Research topic: {topic}\n"
            f"Research question: {question_text}\n\n"
            f"Paper summaries:\n{papers_text}"
        )},
    ], temperature=0.5, max_tokens=4096)

    pipeline_service.complete_run(
        db, run_record,
        result_summary=synthesis,
        result_data={
            "papers_found": len(all_papers),
            "papers_analyzed": min(len(all_papers), 15),
            "queries_used": queries,
        },
    )
    pipeline_service.append_log(db, run_record, "✅ Literature review complete")
