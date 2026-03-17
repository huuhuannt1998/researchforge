"use client";

import { useRef, useState } from "react";
import type { LiteratureItem, LiteratureItemCreateInput } from "@/lib/types";
import { api } from "@/lib/api";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Textarea from "@/components/ui/Textarea";

interface Props {
  projectId: string;
  onAdded: (item: LiteratureItem) => void;
  onClose: () => void;
}

export default function AddLiteratureModal({ projectId, onAdded, onClose }: Props) {
  const [title, setTitle] = useState("");
  const [authorsRaw, setAuthorsRaw] = useState("");
  const [year, setYear] = useState("");
  const [venue, setVenue] = useState("");
  const [url, setUrl] = useState("");
  const [abstract, setAbstract] = useState("");
  const [bibtex, setBibtex] = useState("");
  const [tagsRaw, setTagsRaw] = useState("");
  const [relevance, setRelevance] = useState("");
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;

    setSaving(true);
    setError(null);
    try {
      const payload: LiteratureItemCreateInput = {
        title: title.trim(),
        authors: authorsRaw
          ? authorsRaw.split(",").map((a) => a.trim()).filter(Boolean)
          : undefined,
        year: year ? parseInt(year, 10) : undefined,
        venue: venue.trim() || undefined,
        doi_or_url: url.trim() || undefined,
        abstract: abstract.trim() || undefined,
        bibtex: bibtex.trim() || undefined,
        tags: tagsRaw
          ? tagsRaw.split(",").map((t) => t.trim()).filter(Boolean)
          : undefined,
        relevance_score: relevance ? parseFloat(relevance) : undefined,
      };
      const item = await api.literature.create(projectId, payload);

      // Upload PDF if provided
      let finalItem = item;
      if (pdfFile) {
        try {
          finalItem = await api.literature.uploadPdf(projectId, item.id, pdfFile);
        } catch {
          // PDF upload failed — item still created
        }
      }

      onAdded(finalItem);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add paper");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-xl rounded-xl border border-gray-700 bg-gray-900 shadow-2xl flex flex-col max-h-[90vh]">
        {/* Modal header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700 shrink-0">
          <h2 className="text-base font-semibold text-white">Add Literature</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-lg"
          >
            ✕
          </button>
        </div>

        {/* Scrollable form */}
        <form
          onSubmit={handleSubmit}
          className="flex-1 overflow-y-auto px-6 py-4 flex flex-col gap-4"
        >
          <Input
            label="Title *"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Paper title"
            required
          />

          <Input
            label="Authors (comma-separated)"
            value={authorsRaw}
            onChange={(e) => setAuthorsRaw(e.target.value)}
            placeholder="Alice Smith, Bob Jones"
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Year"
              type="number"
              value={year}
              onChange={(e) => setYear(e.target.value)}
              placeholder="2024"
              min={1900}
              max={new Date().getFullYear() + 1}
            />
            <Input
              label="Venue"
              value={venue}
              onChange={(e) => setVenue(e.target.value)}
              placeholder="NeurIPS 2024"
            />
          </div>

          <Input
            label="DOI or URL"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://arxiv.org/abs/..."
          />

          <Textarea
            label="Abstract"
            value={abstract}
            onChange={(e) => setAbstract(e.target.value)}
            placeholder="Paste the abstract…"
            rows={4}
          />

          <Textarea
            label="BibTeX"
            value={bibtex}
            onChange={(e) => setBibtex(e.target.value)}
            placeholder="@article{...}"
            rows={3}
          />

          <Input
            label="Tags (comma-separated)"
            value={tagsRaw}
            onChange={(e) => setTagsRaw(e.target.value)}
            placeholder="deep-learning, NLP, benchmark"
          />

          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-300">
              Relevance Score:{" "}
              <span className="text-indigo-400 font-semibold">
                {relevance ? parseFloat(relevance).toFixed(1) : "—"}
                {relevance && "/5"}
              </span>
            </label>
            <input
              type="range"
              min={0}
              max={5}
              step={0.5}
              value={relevance || 0}
              onChange={(e) => setRelevance(e.target.value)}
              className="w-full accent-indigo-500"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-300">
              PDF Upload (optional)
            </label>
            <div className="flex items-center gap-3">
              <input
                ref={fileRef}
                type="file"
                accept="application/pdf"
                className="hidden"
                onChange={(e) => setPdfFile(e.target.files?.[0] ?? null)}
              />
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => fileRef.current?.click()}
              >
                Choose PDF
              </Button>
              {pdfFile ? (
                <span className="text-xs text-gray-300 truncate">
                  {pdfFile.name}
                </span>
              ) : (
                <span className="text-xs text-gray-500">No file chosen</span>
              )}
              {pdfFile && (
                <button
                  type="button"
                  onClick={() => setPdfFile(null)}
                  className="text-xs text-gray-500 hover:text-red-400 ml-auto"
                >
                  Remove
                </button>
              )}
            </div>
            <p className="text-xs text-gray-500">
              PDF will be uploaded and AI extraction will run automatically.
            </p>
          </div>

          {error && (
            <p className="rounded bg-red-900/40 border border-red-700 px-3 py-2 text-sm text-red-300">
              {error}
            </p>
          )}
        </form>

        {/* Footer actions */}
        <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-700 shrink-0">
          <Button variant="ghost" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            loading={saving}
            disabled={!title.trim()}
            onClick={handleSubmit}
          >
            Add Paper
          </Button>
        </div>
      </div>
    </div>
  );
}
