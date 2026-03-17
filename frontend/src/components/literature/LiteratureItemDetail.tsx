"use client";

import { useEffect, useState, useCallback } from "react";
import type { LiteratureItem, EvidenceCard } from "@/lib/types";
import { isExtracted } from "@/lib/types";
import { api, ApiError } from "@/lib/api";
import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";
import EvidenceCardRow from "./EvidenceCardRow";
import EvidenceCardForm from "./EvidenceCardForm";

interface Props {
  item: LiteratureItem;
  projectId: string;
  onItemUpdated: (item: LiteratureItem) => void;
  onItemDeleted: (itemId: string) => void;
  onClose: () => void;
}

export default function LiteratureItemDetail({
  item,
  projectId,
  onItemUpdated,
  onItemDeleted,
  onClose,
}: Props) {
  const [cards, setCards] = useState<EvidenceCard[]>([]);
  const [loadingCards, setLoadingCards] = useState(true);
  const [cardsError, setCardsError] = useState<string | null>(null);
  const [addingCard, setAddingCard] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [extractError, setExtractError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const loadCards = useCallback(async () => {
    setLoadingCards(true);
    setCardsError(null);
    try {
      const data = await api.evidenceCards.list(projectId, item.id);
      setCards(data);
    } catch (err) {
      setCardsError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoadingCards(false);
    }
  }, [projectId, item.id]);

  useEffect(() => {
    loadCards();
  }, [loadCards]);

  async function handleExtract() {
    setExtracting(true);
    setExtractError(null);
    try {
      const updated = await api.literature.runExtraction(projectId, item.id);
      onItemUpdated(updated);
    } catch (err) {
      setExtractError(
        err instanceof ApiError
          ? err.message
          : "Extraction failed — check backend logs."
      );
    } finally {
      setExtracting(false);
    }
  }

  async function handleDelete() {
    if (!confirm(`Delete "${item.title}"? This cannot be undone.`)) return;
    setDeleting(true);
    try {
      await api.literature.delete(projectId, item.id);
      onItemDeleted(item.id);
    } finally {
      setDeleting(false);
    }
  }

  const extracted = isExtracted(item);

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 px-5 pt-5 pb-3 border-b border-gray-700 shrink-0">
        <div className="min-w-0">
          <h2 className="text-base font-semibold text-white leading-snug">
            {item.title}
          </h2>
          <p className="mt-0.5 text-xs text-gray-400">
            {[item.authors?.join(", "), item.year, item.venue]
              .filter(Boolean)
              .join(" · ")}
          </p>
          {item.doi_or_url && (
            <a
              href={item.doi_or_url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-0.5 text-xs text-indigo-400 hover:underline truncate block"
            >
              {item.doi_or_url}
            </a>
          )}
        </div>
        <div className="flex gap-2 shrink-0">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDelete}
            loading={deleting}
            className="text-red-400 hover:text-red-300"
          >
            Delete
          </Button>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-lg leading-none"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Scrollable body */}
      <div className="flex-1 overflow-y-auto px-5 py-4 flex flex-col gap-6">
        {/* Abstract */}
        {item.abstract && (
          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1.5">
              Abstract
            </h3>
            <p className="text-sm text-gray-300 leading-relaxed">
              {item.abstract}
            </p>
          </section>
        )}

        {/* Tags */}
        {item.tags && item.tags.length > 0 && (
          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1.5">
              Tags
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {item.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-gray-700 px-2.5 py-0.5 text-xs text-gray-300"
                >
                  {tag}
                </span>
              ))}
            </div>
          </section>
        )}

        {/* Extraction */}
        <section>
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">
              AI Extraction
            </h3>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleExtract}
              loading={extracting}
            >
              {extracted ? "Re-extract" : "Run Extraction"}
            </Button>
          </div>

          {extractError && (
            <p className="mb-2 rounded bg-red-900/40 border border-red-700 px-3 py-2 text-xs text-red-300">
              {extractError}
            </p>
          )}

          {extracted ? (
            <div className="flex flex-col gap-3">
              {item.extracted_summary && (
                <ExtractionSection label="Summary" text={item.extracted_summary} />
              )}
              {item.extracted_methods && item.extracted_methods.length > 0 && (
                <ExtractionListSection
                  label="Methods"
                  items={item.extracted_methods}
                />
              )}
              {item.extracted_datasets && item.extracted_datasets.length > 0 && (
                <ExtractionListSection
                  label="Datasets"
                  items={item.extracted_datasets}
                />
              )}
              {item.extracted_metrics && item.extracted_metrics.length > 0 && (
                <ExtractionListSection
                  label="Metrics"
                  items={item.extracted_metrics}
                />
              )}
              {item.extracted_limitations && item.extracted_limitations.length > 0 && (
                <ExtractionListSection
                  label="Limitations"
                  items={item.extracted_limitations}
                />
              )}
            </div>
          ) : (
            <p className="text-xs text-gray-500">
              No extraction yet. Click &ldquo;Run Extraction&rdquo; to analyse this paper.
            </p>
          )}
        </section>

        {/* BibTeX */}
        {item.bibtex && (
          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1.5">
              BibTeX
            </h3>
            <pre className="rounded bg-gray-900 border border-gray-700 p-3 text-xs text-gray-400 overflow-x-auto whitespace-pre-wrap break-all">
              {item.bibtex}
            </pre>
          </section>
        )}

        {/* Evidence Cards */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">
              Evidence Cards ({cards.length})
            </h3>
            {!addingCard && (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setAddingCard(true)}
              >
                + Add Evidence
              </Button>
            )}
          </div>

          {addingCard && (
            <div className="mb-4 rounded-lg border border-indigo-700 bg-gray-800 p-4">
              <EvidenceCardForm
                projectId={projectId}
                literatureItemId={item.id}
                onSaved={(card) => {
                  setCards((prev) => [card, ...prev]);
                  setAddingCard(false);
                }}
                onCancel={() => setAddingCard(false)}
              />
            </div>
          )}

          {loadingCards ? (
            <div className="flex justify-center py-6">
              <Spinner />
            </div>
          ) : cardsError ? (
            <p className="text-xs text-red-400">{cardsError}</p>
          ) : cards.length === 0 ? (
            <p className="text-xs text-gray-500">
              No evidence cards yet. Extract the paper first, then tag the key
              claims.
            </p>
          ) : (
            <div className="flex flex-col gap-3">
              {cards.map((card) => (
                <EvidenceCardRow
                  key={card.id}
                  card={card}
                  projectId={projectId}
                  onUpdated={(updated) =>
                    setCards((prev) =>
                      prev.map((c) => (c.id === updated.id ? updated : c))
                    )
                  }
                  onDeleted={(id) =>
                    setCards((prev) => prev.filter((c) => c.id !== id))
                  }
                />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ExtractionSection({ label, text }: { label: string; text: string }) {
  return (
    <div>
      <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 mb-1">
        {label}
      </p>
      <p className="text-sm text-gray-300 leading-relaxed">{text}</p>
    </div>
  );
}

function ExtractionListSection({
  label,
  items,
}: {
  label: string;
  items: string[];
}) {
  return (
    <div>
      <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 mb-1">
        {label}
      </p>
      <ul className="flex flex-col gap-1">
        {items.map((item, i) => (
          <li key={i} className="flex gap-2 text-sm text-gray-300">
            <span className="text-indigo-500 shrink-0">•</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
