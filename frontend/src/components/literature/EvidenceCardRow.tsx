"use client";

import { useState } from "react";
import type { EvidenceCard } from "@/lib/types";
import { EVIDENCE_TYPE_LABELS, EVIDENCE_TYPE_COLORS } from "@/lib/types";
import { api } from "@/lib/api";
import EvidenceCardForm from "./EvidenceCardForm";

interface Props {
  card: EvidenceCard;
  projectId: string;
  onUpdated: (card: EvidenceCard) => void;
  onDeleted: (cardId: string) => void;
}

export default function EvidenceCardRow({
  card,
  projectId,
  onUpdated,
  onDeleted,
}: Props) {
  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const confidencePct = Math.round((card.confidence ?? 0) * 100);
  const confidenceColor =
    confidencePct >= 80
      ? "text-green-400"
      : confidencePct >= 50
        ? "text-yellow-400"
        : "text-red-400";

  async function handleDelete() {
    if (!confirm("Delete this evidence card?")) return;
    setDeleting(true);
    try {
      await api.evidenceCards.delete(projectId, card.id);
      onDeleted(card.id);
    } finally {
      setDeleting(false);
    }
  }

  if (editing) {
    return (
      <div className="rounded-lg border border-indigo-700 bg-gray-800 p-4">
        <EvidenceCardForm
          projectId={projectId}
          existing={card}
          onSaved={(updated) => {
            onUpdated(updated);
            setEditing(false);
          }}
          onCancel={() => setEditing(false)}
        />
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-700 bg-gray-800/60 p-4 hover:border-gray-600 transition-colors">
      {/* Header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          {card.evidence_type && (
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium border ${EVIDENCE_TYPE_COLORS[card.evidence_type]}`}
            >
              {EVIDENCE_TYPE_LABELS[card.evidence_type]}
            </span>
          )}
          <span className={`text-xs font-semibold ${confidenceColor}`}>
            {confidencePct}% confidence
          </span>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={() => setEditing(true)}
            className="rounded p-1 text-gray-400 hover:text-white hover:bg-gray-700 transition-colors text-xs"
          >
            Edit
          </button>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="rounded p-1 text-gray-400 hover:text-red-400 hover:bg-red-900/30 transition-colors text-xs disabled:opacity-50"
          >
            {deleting ? "…" : "Delete"}
          </button>
        </div>
      </div>

      {/* Claim */}
      <p className="mt-2 text-sm font-medium text-white leading-snug">
        {card.claim}
      </p>

      {/* Quote */}
      {card.quote_or_paraphrase && (
        <blockquote className="mt-2 border-l-2 border-indigo-500 pl-3 text-xs text-gray-400 italic leading-relaxed">
          {card.quote_or_paraphrase}
        </blockquote>
      )}

      {/* Method + Metrics inline */}
      {(card.method || card.metrics) && (
        <div className="mt-2 flex flex-wrap gap-3 text-xs text-gray-400">
          {card.method && (
            <span>
              <span className="text-gray-500">Method:</span> {card.method}
            </span>
          )}
          {card.metrics &&
            Object.entries(card.metrics).map(([k, v]) => (
              <span key={k}>
                <span className="text-gray-500">{k}:</span> {String(v)}
              </span>
            ))}
        </div>
      )}

      {/* Limitations */}
      {card.limitations && (
        <p className="mt-1.5 text-xs text-yellow-500/80">
          ⚠ {card.limitations}
        </p>
      )}

      {/* Notes */}
      {card.notes && (
        <p className="mt-1.5 text-xs text-gray-500 italic">{card.notes}</p>
      )}
    </div>
  );
}
