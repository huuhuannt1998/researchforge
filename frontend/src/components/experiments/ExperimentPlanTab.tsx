"use client";

import { useCallback, useEffect, useState } from "react";
import type { ExperimentPlan } from "@/lib/types";
import { api } from "@/lib/api";
import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";
import ExperimentPlanEditor from "./ExperimentPlanEditor";

interface Props {
  projectId: string;
}

export default function ExperimentPlanTab({ projectId }: Props) {
  const [plans, setPlans] = useState<ExperimentPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const loadPlans = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.experiments.list(projectId);
      setPlans(data);
      // Auto-select the first plan
      if (data.length > 0 && !selectedId) {
        setSelectedId(data[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load plans");
    } finally {
      setLoading(false);
    }
  }, [projectId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    loadPlans();
  }, [loadPlans]);

  async function handleCreate() {
    setCreating(true);
    try {
      const plan = await api.experiments.create(projectId, {});
      setPlans((prev) => [plan, ...prev]);
      setSelectedId(plan.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create plan");
    } finally {
      setCreating(false);
    }
  }

  function handleUpdated(updated: ExperimentPlan) {
    setPlans((prev) =>
      prev.map((p) => (p.id === updated.id ? updated : p))
    );
  }

  function handleDeleted(planId: string) {
    const remaining = plans.filter((p) => p.id !== planId);
    setPlans(remaining);
    setSelectedId(remaining.length > 0 ? remaining[0].id : null);
  }

  const selectedPlan = plans.find((p) => p.id === selectedId) ?? null;

  // -------------------------------------------------------------------------
  // Loading / error states
  // -------------------------------------------------------------------------
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4">
        <p className="text-sm text-red-400">{error}</p>
        <Button variant="secondary" size="sm" onClick={loadPlans}>
          Retry
        </Button>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Empty state
  // -------------------------------------------------------------------------
  if (plans.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-5 px-8 text-center">
        <div className="text-5xl">🧪</div>
        <div>
          <p className="text-lg font-semibold text-white">
            No experiment plans yet
          </p>
          <p className="mt-1 text-sm text-gray-400 max-w-sm">
            Create a structured experiment plan to track hypotheses, baselines,
            datasets, metrics, ablations, and risks.
          </p>
        </div>
        <Button loading={creating} onClick={handleCreate}>
          Create First Plan
        </Button>
        {error && (
          <p className="text-xs text-red-400">{error}</p>
        )}
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Main split view: plan list (sidebar) + editor (main)
  // -------------------------------------------------------------------------
  return (
    <div className="flex h-full overflow-hidden">
      {/* Left sidebar — plan list */}
      <div className="w-64 shrink-0 flex flex-col border-r border-gray-700 bg-gray-900">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
            Plans ({plans.length})
          </span>
          <button
            onClick={handleCreate}
            disabled={creating}
            className="text-xs text-indigo-400 hover:text-indigo-300 disabled:opacity-50 font-medium"
          >
            {creating ? "…" : "+ New"}
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-2 px-2 flex flex-col gap-1">
          {plans.map((plan) => (
            <PlanListItem
              key={plan.id}
              plan={plan}
              selected={plan.id === selectedId}
              onSelect={() => setSelectedId(plan.id)}
            />
          ))}
        </div>
      </div>

      {/* Right editor pane */}
      <div className="flex-1 flex flex-col overflow-hidden bg-gray-950">
        {selectedPlan ? (
          <ExperimentPlanEditor
            key={selectedPlan.id}
            plan={selectedPlan}
            projectId={projectId}
            onUpdated={handleUpdated}
            onDeleted={handleDeleted}
          />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-gray-500">
            Select a plan to edit
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Plan list sidebar item
// ---------------------------------------------------------------------------

function PlanListItem({
  plan,
  selected,
  onSelect,
}: {
  plan: ExperimentPlan;
  selected: boolean;
  onSelect: () => void;
}) {
  const title =
    plan.objective?.slice(0, 60) ||
    `Plan — ${new Date(plan.created_at).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    })}`;

  const hypothesisCount = plan.hypotheses.length;
  const baselineCount = plan.baselines.length;

  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full text-left rounded-lg px-3 py-2.5 transition-colors ${
        selected
          ? "bg-indigo-900/40 border border-indigo-700"
          : "hover:bg-gray-800 border border-transparent"
      }`}
    >
      <p
        className={`text-sm font-medium leading-snug truncate ${
          selected ? "text-white" : "text-gray-300"
        }`}
      >
        {title}
      </p>
      <div className="mt-1 flex gap-2 text-[11px] text-gray-500">
        {hypothesisCount > 0 && (
          <span>{hypothesisCount} hypothesis{hypothesisCount !== 1 ? "es" : ""}</span>
        )}
        {baselineCount > 0 && <span>{baselineCount} baseline{baselineCount !== 1 ? "s" : ""}</span>}
        {hypothesisCount === 0 && baselineCount === 0 && (
          <span>Empty plan</span>
        )}
      </div>
    </button>
  );
}
