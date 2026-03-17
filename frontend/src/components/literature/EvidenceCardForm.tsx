"use client";

import { useState } from "react";
import type { EvidenceCard, EvidenceCardCreateInput, EvidenceCardUpdateInput, EvidenceType } from "@/lib/types";
import { EVIDENCE_TYPE_LABELS } from "@/lib/types";
import { api } from "@/lib/api";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Textarea from "@/components/ui/Textarea";

interface Props {
  projectId: string;
  literatureItemId?: string;
  /** When provided, the form operates in edit mode */
  existing?: EvidenceCard;
  onSaved: (card: EvidenceCard) => void;
  onCancel: () => void;
}

const EVIDENCE_TYPES: EvidenceType[] = [
  "empirical",
  "theoretical",
  "survey",
  "case_study",
  "benchmark",
  "other",
];

export default function EvidenceCardForm({
  projectId,
  literatureItemId,
  existing,
  onSaved,
  onCancel,
}: Props) {
  const [claim, setClaim] = useState(existing?.claim ?? "");
  const [evidenceType, setEvidenceType] = useState<EvidenceType>(
    existing?.evidence_type ?? "empirical"
  );
  const [quote, setQuote] = useState(existing?.quote_or_paraphrase ?? "");
  const [method, setMethod] = useState(existing?.method ?? "");
  const [metrics, setMetrics] = useState(
    existing?.metrics ? JSON.stringify(existing.metrics, null, 2) : ""
  );
  const [limitations, setLimitations] = useState(existing?.limitations ?? "");
  const [notes, setNotes] = useState(existing?.notes ?? "");
  const [confidence, setConfidence] = useState<number>(
    existing?.confidence ?? 0.8
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metricsError, setMetricsError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!claim.trim()) return;

    let parsedMetrics: Record<string, string> | undefined;
    if (metrics.trim()) {
      try {
        parsedMetrics = JSON.parse(metrics);
      } catch {
        setMetricsError("Must be valid JSON, e.g. {\"accuracy\": \"92%\"}");
        return;
      }
    }
    setMetricsError(null);

    setSaving(true);
    setError(null);
    try {
      let saved: EvidenceCard;
      if (existing) {
        const payload: EvidenceCardUpdateInput = {
          claim: claim.trim() || undefined,
          evidence_type: evidenceType,
          quote_or_paraphrase: quote.trim() || undefined,
          method: method.trim() || undefined,
          metrics: parsedMetrics,
          limitations: limitations.trim() || undefined,
          notes: notes.trim() || undefined,
          confidence,
        };
        saved = await api.evidenceCards.update(projectId, existing.id, payload);
      } else {
        const payload: EvidenceCardCreateInput = {
          claim: claim.trim(),
          evidence_type: evidenceType,
          quote_or_paraphrase: quote.trim() || undefined,
          method: method.trim() || undefined,
          metrics: parsedMetrics,
          limitations: limitations.trim() || undefined,
          notes: notes.trim() || undefined,
          confidence,
          literature_item_id: literatureItemId,
        };
        saved = await api.evidenceCards.create(projectId, payload);
      }
      onSaved(saved);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <Textarea
        label="Claim *"
        value={claim}
        onChange={(e) => setClaim(e.target.value)}
        placeholder="The key claim this evidence supports…"
        rows={2}
        required
      />

      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-gray-300">
          Evidence Type
        </label>
        <select
          value={evidenceType}
          onChange={(e) => setEvidenceType(e.target.value as EvidenceType)}
          className="rounded-lg border border-gray-600 bg-gray-700 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
        >
          {EVIDENCE_TYPES.map((t) => (
            <option key={t} value={t}>
              {EVIDENCE_TYPE_LABELS[t]}
            </option>
          ))}
        </select>
      </div>

      <Textarea
        label="Quote or Paraphrase"
        value={quote}
        onChange={(e) => setQuote(e.target.value)}
        placeholder="Direct quote or paraphrase from the paper…"
        rows={3}
      />

      <Input
        label="Method"
        value={method}
        onChange={(e) => setMethod(e.target.value)}
        placeholder="e.g. RCT, ablation study, meta-analysis"
      />

      <Textarea
        label='Metrics (JSON, e.g. {"accuracy": "92%"})'
        value={metrics}
        onChange={(e) => setMetrics(e.target.value)}
        placeholder='{"accuracy": "92%", "f1": "0.91"}'
        rows={2}
        error={metricsError ?? undefined}
      />

      <Textarea
        label="Limitations"
        value={limitations}
        onChange={(e) => setLimitations(e.target.value)}
        placeholder="Any limitations acknowledged or observed…"
        rows={2}
      />

      <Textarea
        label="Notes"
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Personal notes…"
        rows={2}
      />

      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-gray-300">
          Confidence:{" "}
          <span className="text-indigo-400 font-semibold">
            {Math.round(confidence * 100)}%
          </span>
        </label>
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={confidence}
          onChange={(e) => setConfidence(parseFloat(e.target.value))}
          className="w-full accent-indigo-500"
        />
      </div>

      {error && (
        <p className="rounded bg-red-900/40 border border-red-700 px-3 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      <div className="flex justify-end gap-3 pt-1">
        <Button variant="ghost" type="button" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={saving} disabled={!claim.trim()}>
          {existing ? "Save Changes" : "Add Evidence"}
        </Button>
      </div>
    </form>
  );
}
