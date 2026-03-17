"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { ExperimentPlan, ExperimentPlanUpdateInput } from "@/lib/types";
import { EXPERIMENT_FIELD_LABELS } from "@/lib/types";
import { api } from "@/lib/api";
import Button from "@/components/ui/Button";
import Textarea from "@/components/ui/Textarea";
import EditableList from "./EditableList";

interface Props {
  plan: ExperimentPlan;
  projectId: string;
  onUpdated: (plan: ExperimentPlan) => void;
  onDeleted: (planId: string) => void;
}

type SaveState = "idle" | "saving" | "saved" | "error";

const LIST_FIELDS = [
  "hypotheses",
  "baselines",
  "datasets",
  "metrics",
  "ablations",
  "expected_claims",
  "risks",
] as const;

type ListField = (typeof LIST_FIELDS)[number];

export default function ExperimentPlanEditor({
  plan,
  projectId,
  onUpdated,
  onDeleted,
}: Props) {
  // Local copy for instant UI feedback
  const [local, setLocal] = useState<ExperimentPlan>(plan);
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [deleting, setDeleting] = useState(false);

  const pendingRef = useRef<ExperimentPlanUpdateInput>({});
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Reset local state when a different plan is selected
  useEffect(() => {
    setLocal(plan);
    pendingRef.current = {};
    setSaveState("idle");
  }, [plan.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const scheduleAutoSave = useCallback(
    (patch: ExperimentPlanUpdateInput) => {
      // Merge new changes into the pending diff
      pendingRef.current = { ...pendingRef.current, ...patch };

      if (timerRef.current) clearTimeout(timerRef.current);
      setSaveState("saving");

      timerRef.current = setTimeout(async () => {
        const diff = pendingRef.current;
        pendingRef.current = {};
        try {
          const updated = await api.experiments.update(projectId, plan.id, diff);
          onUpdated(updated);
          setSaveState("saved");
          // Fade "Saved" back to idle after 2s
          setTimeout(() => setSaveState("idle"), 2000);
        } catch {
          setSaveState("error");
        }
      }, 1200);
    },
    [projectId, plan.id, onUpdated]
  );

  function setTextField(
    field: "objective" | "compute_notes" | "reproducibility_requirements",
    value: string
  ) {
    setLocal((prev) => ({ ...prev, [field]: value }));
    scheduleAutoSave({ [field]: value || undefined });
  }

  function setListField(field: ListField, items: string[]) {
    const cleaned = items.filter((s) => s.trim() !== "");
    setLocal((prev) => ({ ...prev, [field]: items })); // keep blank during editing
    scheduleAutoSave({ [field]: cleaned });
  }

  async function handleDelete() {
    if (!confirm("Delete this experiment plan? This cannot be undone.")) return;
    setDeleting(true);
    try {
      await api.experiments.delete(projectId, plan.id);
      onDeleted(plan.id);
    } finally {
      setDeleting(false);
    }
  }

  const createdDate = new Date(local.created_at).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Sticky header */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-gray-700 bg-gray-900 shrink-0">
        <div className="flex items-center gap-3">
          <SaveIndicator state={saveState} />
          <span className="text-xs text-gray-600">Created {createdDate}</span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          loading={deleting}
          onClick={handleDelete}
          className="text-red-400 hover:text-red-300"
        >
          Delete Plan
        </Button>
      </div>

      {/* Scrollable body */}
      <div className="flex-1 overflow-y-auto px-6 py-5 flex flex-col gap-7">
        {/* Objective */}
        <Section
          title="Objective"
          description="The single overarching goal this experiment set aims to achieve"
        >
          <textarea
            value={local.objective ?? ""}
            onChange={(e) => setTextField("objective", e.target.value)}
            placeholder="Describe the primary objective of this experiment…"
            rows={3}
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white placeholder-gray-600 focus:border-indigo-500 focus:outline-none resize-none"
          />
        </Section>

        {/* List fields */}
        {LIST_FIELDS.map((field) => {
          const meta = EXPERIMENT_FIELD_LABELS[field];
          return (
            <Section
              key={field}
              title={meta.label}
              description={meta.description}
            >
              <EditableList
                value={local[field]}
                onChange={(items) => setListField(field, items)}
                placeholder={meta.placeholder}
              />
            </Section>
          );
        })}

        {/* Compute Notes */}
        <Section
          title="Compute Notes"
          description="Hardware, estimated runtime, and resource requirements"
        >
          <textarea
            value={local.compute_notes ?? ""}
            onChange={(e) => setTextField("compute_notes", e.target.value)}
            placeholder="e.g. 4× A100 80 GB, ~72 h training, $800 estimated cost"
            rows={2}
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white placeholder-gray-600 focus:border-indigo-500 focus:outline-none resize-none"
          />
        </Section>

        {/* Reproducibility */}
        <Section
          title="Reproducibility Requirements"
          description="Seeds, deterministic ops, containerisation, data access"
        >
          <textarea
            value={local.reproducibility_requirements ?? ""}
            onChange={(e) =>
              setTextField("reproducibility_requirements", e.target.value)
            }
            placeholder="e.g. Fixed seed 42, deterministic CUDA, Docker image pushed to registry"
            rows={2}
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white placeholder-gray-600 focus:border-indigo-500 focus:outline-none resize-none"
          />
        </Section>

        {/* Bottom spacer */}
        <div className="h-4 shrink-0" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function Section({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2">
      <div>
        <h3 className="text-sm font-semibold text-white">{title}</h3>
        <p className="text-xs text-gray-500 mt-0.5">{description}</p>
      </div>
      <div>{children}</div>
    </div>
  );
}

function SaveIndicator({ state }: { state: SaveState }) {
  if (state === "idle") return null;

  const configs: Record<
    Exclude<SaveState, "idle">,
    { text: string; color: string; dot: string }
  > = {
    saving: {
      text: "Saving…",
      color: "text-gray-400",
      dot: "bg-yellow-400 animate-pulse",
    },
    saved: {
      text: "Saved",
      color: "text-green-400",
      dot: "bg-green-400",
    },
    error: {
      text: "Save failed",
      color: "text-red-400",
      dot: "bg-red-400",
    },
  };

  const cfg = configs[state as Exclude<SaveState, "idle">];
  return (
    <span className={`flex items-center gap-1.5 text-xs font-medium ${cfg.color}`}>
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${cfg.dot}`} />
      {cfg.text}
    </span>
  );
}
