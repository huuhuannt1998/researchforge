"use client";

import type { LiteratureItem } from "@/lib/types";
import { isExtracted } from "@/lib/types";

interface Props {
  item: LiteratureItem;
  selected: boolean;
  onSelect: (item: LiteratureItem) => void;
}

export default function LiteratureItemRow({ item, selected, onSelect }: Props) {
  const extracted = isExtracted(item);
  const authors = item.authors?.join(", ") ?? "";
  const tags = item.tags ?? [];

  return (
    <button
      type="button"
      onClick={() => onSelect(item)}
      className={`w-full text-left rounded-lg border p-4 transition-colors ${
        selected
          ? "border-indigo-500 bg-indigo-900/20"
          : "border-gray-700 bg-gray-800/60 hover:border-gray-600"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          {/* Title */}
          <p className="text-sm font-semibold text-white leading-snug line-clamp-2">
            {item.title}
          </p>

          {/* Authors + year + venue */}
          <p className="mt-0.5 text-xs text-gray-400 truncate">
            {[authors, item.year, item.venue].filter(Boolean).join(" · ")}
          </p>

          {/* Tags */}
          {tags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {tags.slice(0, 5).map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-gray-700 px-2 py-0.5 text-[11px] text-gray-300"
                >
                  {tag}
                </span>
              ))}
              {tags.length > 5 && (
                <span className="rounded-full bg-gray-700 px-2 py-0.5 text-[11px] text-gray-500">
                  +{tags.length - 5}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Right column: relevance + extraction badge */}
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          {item.relevance_score != null && (
            <span
              className={`text-xs font-bold ${
                item.relevance_score >= 4
                  ? "text-green-400"
                  : item.relevance_score >= 2
                    ? "text-yellow-400"
                    : "text-gray-400"
              }`}
            >
              ★ {item.relevance_score}/5
            </span>
          )}
          <span
            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ${
              extracted
                ? "bg-green-900/40 text-green-300 border border-green-700"
                : "bg-gray-700 text-gray-400"
            }`}
          >
            {extracted ? "✓ Extracted" : "No extraction"}
          </span>
        </div>
      </div>
    </button>
  );
}
