"use client";

import { useCallback, useEffect, useState } from "react";
import type { LiteratureItem, EvidenceCard } from "@/lib/types";
import {
  EVIDENCE_TYPE_LABELS,
  EVIDENCE_TYPE_COLORS,
} from "@/lib/types";
import { api } from "@/lib/api";
import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";
import LiteratureItemRow from "./LiteratureItemRow";
import LiteratureItemDetail from "./LiteratureItemDetail";
import AddLiteratureModal from "./AddLiteratureModal";

interface Props {
  projectId: string;
}

type SubTab = "library" | "evidence";

export default function LiteratureTab({ projectId }: Props) {
  const [subTab, setSubTab] = useState<SubTab>("library");
  const [items, setItems] = useState<LiteratureItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<LiteratureItem | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const loadItems = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.literature.list(projectId);
      setItems(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load literature");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  // Keep selectedItem in sync when the list refreshes
  useEffect(() => {
    if (selectedItem) {
      const updated = items.find((i) => i.id === selectedItem.id);
      if (updated) setSelectedItem(updated);
    }
  }, [items]); // eslint-disable-line react-hooks/exhaustive-deps

  function handleItemUpdated(updated: LiteratureItem) {
    setItems((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
    setSelectedItem(updated);
  }

  function handleItemDeleted(itemId: string) {
    setItems((prev) => prev.filter((i) => i.id !== itemId));
    setSelectedItem(null);
  }

  // Filter items by search query
  const filtered = items.filter((item) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.title.toLowerCase().includes(q) ||
      item.authors?.some((a) => a.toLowerCase().includes(q)) ||
      item.venue?.toLowerCase().includes(q) ||
      item.tags?.some((t) => t.toLowerCase().includes(q))
    );
  });

  return (
    <div className="flex flex-col h-full">
      {/* Sub-tab bar */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-gray-700 bg-gray-900 shrink-0">
        <div className="flex gap-1">
          {(["library", "evidence"] as SubTab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setSubTab(tab)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                subTab === tab
                  ? "bg-indigo-600 text-white"
                  : "text-gray-400 hover:text-white hover:bg-gray-800"
              }`}
            >
              {tab === "library" ? "Library" : "Evidence Map"}
            </button>
          ))}
        </div>
        <Button size="sm" onClick={() => setShowAddModal(true)}>
          + Add Paper
        </Button>
      </div>

      {/* Content */}
      <div className="flex flex-1 overflow-hidden">
        {subTab === "library" && (
          <LibraryPane
            items={filtered}
            loading={loading}
            error={error}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            selectedItem={selectedItem}
            onSelectItem={setSelectedItem}
            onRefresh={loadItems}
          />
        )}
        {subTab === "evidence" && (
          <EvidenceMapPane projectId={projectId} items={items} />
        )}

        {/* Detail panel (slides in from right) */}
        {selectedItem && (
          <div className="w-96 shrink-0 border-l border-gray-700 bg-gray-900 flex flex-col overflow-hidden">
            <LiteratureItemDetail
              key={selectedItem.id}
              item={selectedItem}
              projectId={projectId}
              onItemUpdated={handleItemUpdated}
              onItemDeleted={handleItemDeleted}
              onClose={() => setSelectedItem(null)}
            />
          </div>
        )}
      </div>

      {/* Add modal */}
      {showAddModal && (
        <AddLiteratureModal
          projectId={projectId}
          onAdded={(item) => {
            setItems((prev) => [item, ...prev]);
            setSelectedItem(item);
            setShowAddModal(false);
          }}
          onClose={() => setShowAddModal(false)}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Library pane
// ---------------------------------------------------------------------------

interface LibraryPaneProps {
  items: LiteratureItem[];
  loading: boolean;
  error: string | null;
  searchQuery: string;
  onSearchChange: (v: string) => void;
  selectedItem: LiteratureItem | null;
  onSelectItem: (item: LiteratureItem) => void;
  onRefresh: () => void;
}

function LibraryPane({
  items,
  loading,
  error,
  searchQuery,
  onSearchChange,
  selectedItem,
  onSelectItem,
  onRefresh,
}: LibraryPaneProps) {
  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Search bar */}
      <div className="px-4 py-3 border-b border-gray-800 shrink-0">
        <input
          type="search"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search title, authors, tags…"
          className="w-full rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
        />
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {loading ? (
          <div className="flex justify-center py-10">
            <Spinner />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center gap-3 py-10 text-center">
            <p className="text-sm text-red-400">{error}</p>
            <Button variant="secondary" size="sm" onClick={onRefresh}>
              Retry
            </Button>
          </div>
        ) : items.length === 0 ? (
          <EmptyState hasSearch={!!searchQuery} />
        ) : (
          <div className="flex flex-col gap-3">
            {items.map((item) => (
              <LiteratureItemRow
                key={item.id}
                item={item}
                selected={selectedItem?.id === item.id}
                onSelect={onSelectItem}
              />
            ))}
          </div>
        )}
      </div>

      {/* Footer count */}
      {!loading && !error && items.length > 0 && (
        <div className="px-4 py-2 border-t border-gray-800 shrink-0">
          <p className="text-xs text-gray-500">{items.length} paper{items.length !== 1 ? "s" : ""}</p>
        </div>
      )}
    </div>
  );
}

function EmptyState({ hasSearch }: { hasSearch: boolean }) {
  if (hasSearch) {
    return (
      <div className="flex flex-col items-center gap-2 py-10 text-center">
        <p className="text-sm text-gray-400">No papers match your search.</p>
        <p className="text-xs text-gray-500">Try different keywords.</p>
      </div>
    );
  }
  return (
    <div className="flex flex-col items-center gap-2 py-10 text-center">
      <p className="text-2xl">📚</p>
      <p className="text-sm font-medium text-gray-300">No literature yet</p>
      <p className="text-xs text-gray-500">
        Click &ldquo;+ Add Paper&rdquo; to import your first reference.
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Evidence Map pane
// ---------------------------------------------------------------------------

interface EvidenceMapPaneProps {
  projectId: string;
  items: LiteratureItem[];
}

function EvidenceMapPane({ projectId, items }: EvidenceMapPaneProps) {
  const [cards, setCards] = useState<EvidenceCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadCards = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.evidenceCards.list(projectId);
      setCards(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadCards();
  }, [loadCards]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3">
        <p className="text-sm text-red-400">{error}</p>
        <Button variant="secondary" size="sm" onClick={loadCards}>
          Retry
        </Button>
      </div>
    );
  }

  if (cards.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-2 text-center px-6">
        <p className="text-2xl">🗂️</p>
        <p className="text-sm font-medium text-gray-300">No evidence cards yet</p>
        <p className="text-xs text-gray-500">
          Open a paper in the Library tab, run extraction, then add evidence
          cards to build your map.
        </p>
      </div>
    );
  }

  // Group cards by literature_item_id
  const byItem = cards.reduce<Record<string, EvidenceCard[]>>((acc, card) => {
    const key = card.literature_item_id ?? "__unlinked__";
    (acc[key] ??= []).push(card);
    return acc;
  }, {});

  const itemMap = Object.fromEntries(items.map((i) => [i.id, i]));

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4">
      <div className="flex flex-col gap-6">
        {Object.entries(byItem).map(([itemId, group]) => {
          const paper = itemMap[itemId];
          return (
            <div key={itemId}>
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
                {paper ? paper.title : "Unlinked cards"}
              </p>
              <div className="flex flex-col gap-2">
                {group.map((card) => (
                  <EvidenceMapCard key={card.id} card={card} />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function EvidenceMapCard({ card }: { card: EvidenceCard }) {
  const pct = Math.round((card.confidence ?? 0) * 100);
  const color =
    pct >= 80 ? "text-green-400" : pct >= 50 ? "text-yellow-400" : "text-red-400";

  return (
    <div className="rounded-lg border border-gray-700 bg-gray-800/60 px-4 py-3">
      <div className="flex items-center gap-2 mb-1.5 flex-wrap">
        {card.evidence_type && (
          <span
            className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium border ${EVIDENCE_TYPE_COLORS[card.evidence_type]}`}
          >
            {EVIDENCE_TYPE_LABELS[card.evidence_type]}
          </span>
        )}
        <span className={`text-xs font-semibold ${color}`}>{pct}%</span>
      </div>
      <p className="text-sm text-white">{card.claim}</p>
      {card.quote_or_paraphrase && (
        <p className="mt-1 text-xs text-gray-400 italic line-clamp-2">
          &ldquo;{card.quote_or_paraphrase}&rdquo;
        </p>
      )}
    </div>
  );
}
