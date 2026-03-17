"""
Extraction service — stub implementation.

This module defines the interface and data contracts for paper extraction.
The stub returns realistic placeholder data so the rest of the system
can be built and tested end-to-end without a real PDF pipeline.

Future real implementations can swap in:
  - PyMuPDF / pdfplumber for text extraction
  - Marker (VikParuchuri/marker) for high-quality PDF-to-markdown
  - An LLM call for structured extraction (methods, datasets, metrics, limitations)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Structured extraction output from a paper."""

    summary: Optional[str]
    methods: List[str]
    datasets: List[str]
    metrics: List[str]
    limitations: List[str]


def extract_from_pdf(pdf_path: str) -> ExtractionResult:
    """
    Extract structured information from a PDF file.

    Stub: returns placeholder data.  Replace body with real extraction logic.
    The interface (signature + ExtractionResult) must remain stable.

    Args:
        pdf_path: Absolute or repo-relative path to the PDF.

    Returns:
        ExtractionResult with structured fields.
    """
    path = Path(pdf_path)
    logger.info("extract_from_pdf called for %s (stub)", path.name)

    # In a real implementation this is where we would:
    #   1. Read raw text from PDF (pdfplumber / PyMuPDF)
    #   2. Send to an LLM with a structured extraction prompt
    #   3. Parse structured JSON response
    #   4. Return validated ExtractionResult

    return ExtractionResult(
        summary=(
            f"[Stub extraction for {path.name}] "
            "This is a placeholder summary. Connect a real PDF extraction pipeline "
            "by replacing this stub with calls to PyMuPDF + an LLM extraction prompt."
        ),
        methods=["[Stub] Method 1", "[Stub] Method 2"],
        datasets=["[Stub] Dataset A"],
        metrics=["[Stub] Accuracy", "[Stub] F1-Score"],
        limitations=["[Stub] Limited dataset size", "[Stub] Evaluation on single domain only"],
    )


def extract_from_url(url: str) -> ExtractionResult:
    """
    Extract structured information from a paper URL (e.g. arXiv abstract page).

    Stub: returns placeholder data.  Replace body with real extraction logic.

    Args:
        url: URL to the paper (arXiv, ACL Anthology, DOI, etc.)

    Returns:
        ExtractionResult with structured fields.
    """
    logger.info("extract_from_url called for %s (stub)", url)

    return ExtractionResult(
        summary=(
            f"[Stub extraction for {url}] "
            "Connect a real extraction pipeline using requests + BeautifulSoup "
            "to fetch the abstract, then an LLM for structured field extraction."
        ),
        methods=["[Stub] Method from URL"],
        datasets=["[Stub] Dataset from URL"],
        metrics=["[Stub] Metric from URL"],
        limitations=["[Stub] Limitation from URL"],
    )
