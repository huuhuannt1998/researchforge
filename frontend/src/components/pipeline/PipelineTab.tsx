"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { PipelineRun, PipelineStage, PipelineStatus } from "@/lib/types";
import {
  PIPELINE_STAGES,
  PIPELINE_STATUS_COLORS,
  STAGE_DESCRIPTIONS,
  STAGE_ICONS,
  STAGE_LABELS,
} from "@/lib/types";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Spinner from "@/components/ui/Spinner";

interface PipelineTabProps {
  projectId: string;
}

export default function PipelineTab({ projectId }: PipelineTabProps) {
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState<string | null>(null);
  const [expandedRun, setExpandedRun] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Fetch all pipeline runs
  const fetchRuns = useCallback(async () => {
    try {
      const data = await api.pipeline.list(projectId);
      setRuns(data);
    } catch {
      // ignore fetch errors during polling
    }
  }, [projectId]);

  useEffect(() => {
    fetchRuns().then(() => setLoading(false));
  }, [fetchRuns]);

  // Poll while any run is pending/running
  useEffect(() => {
    const hasActive = runs.some(
      (r) => r.status === "pending" || r.status === "running"
    );
    if (hasActive) {
      pollRef.current = setInterval(fetchRuns, 3000);
    } else if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [runs, fetchRuns]);

  // Get latest run for each stage
  const latestByStage = PIPELINE_STAGES.reduce(
    (acc, stage) => {
      const stageRuns = runs
        .filter((r) => r.stage === stage)
        .sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
      acc[stage] = stageRuns[0] ?? null;
      return acc;
    },
    {} as Record<PipelineStage, PipelineRun | null>
  );

  async function handleTriggerStage(stage: PipelineStage) {
    setTriggering(stage);
    try {
      await api.pipeline.triggerStage(projectId, stage);
      await fetchRuns();
    } catch (err) {
      alert((err as Error).message);
    } finally {
      setTriggering(null);
    }
  }

  async function handleRunAll() {
    setTriggering("all");
    try {
      await api.pipeline.triggerAll(projectId);
      await fetchRuns();
    } catch (err) {
      alert((err as Error).message);
    } finally {
      setTriggering(null);
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            AI Research Pipeline
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            Run autonomous agents to conduct your research end-to-end
          </p>
        </div>
        <Button
          onClick={handleRunAll}
          loading={triggering === "all"}
          disabled={triggering !== null}
        >
          🚀 Run Full Pipeline
        </Button>
      </div>

      {/* Stage cards */}
      <div className="space-y-4">
        {PIPELINE_STAGES.map((stage, index) => {
          const run = latestByStage[stage];
          const isActive =
            run?.status === "running" || run?.status === "pending";
          const prevStage = index > 0 ? PIPELINE_STAGES[index - 1] : null;
          const prevCompleted = prevStage
            ? latestByStage[prevStage]?.status === "completed"
            : true;

          return (
            <Card key={stage} className="overflow-hidden">
              {/* Stage header */}
              <div className="flex items-start justify-between p-5">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">{STAGE_ICONS[stage]}</span>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium text-gray-900">
                        {index + 1}. {STAGE_LABELS[stage]}
                      </h3>
                      {run && <StatusPill status={run.status} />}
                    </div>
                    <p className="text-sm text-gray-500 mt-0.5">
                      {STAGE_DESCRIPTIONS[stage]}
                    </p>
                  </div>
                </div>

                <Button
                  size="sm"
                  variant={run?.status === "completed" ? "secondary" : "primary"}
                  onClick={() => handleTriggerStage(stage)}
                  loading={triggering === stage}
                  disabled={triggering !== null || isActive}
                >
                  {isActive
                    ? "Running…"
                    : run?.status === "completed"
                      ? "Re-run"
                      : run?.status === "failed"
                        ? "Retry"
                        : "Run"}
                </Button>
              </div>

              {/* Run details (expandable) */}
              {run && (
                <div className="border-t border-gray-100">
                  <button
                    onClick={() =>
                      setExpandedRun(expandedRun === run.id ? null : run.id)
                    }
                    className="w-full px-5 py-2.5 text-left text-xs text-gray-500 hover:bg-gray-50 flex items-center gap-1"
                  >
                    <svg
                      className={`w-3 h-3 transition-transform ${
                        expandedRun === run.id ? "rotate-90" : ""
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                    {run.status === "running" && (
                      <Spinner size="sm" />
                    )}
                    {run.started_at
                      ? `Started ${new Date(run.started_at).toLocaleString()}`
                      : `Created ${new Date(run.created_at).toLocaleString()}`}
                    {run.completed_at &&
                      ` · Completed ${new Date(run.completed_at).toLocaleString()}`}
                  </button>

                  {expandedRun === run.id && (
                    <div className="px-5 pb-4 space-y-3">
                      {/* Result summary */}
                      {run.result_summary && (
                        <div>
                          <h4 className="text-xs font-medium text-gray-700 mb-1">
                            Summary
                          </h4>
                          <div className="text-sm text-gray-600 bg-gray-50 rounded-lg p-3 whitespace-pre-wrap max-h-64 overflow-y-auto">
                            {run.result_summary}
                          </div>
                        </div>
                      )}

                      {/* Error message */}
                      {run.error_message && (
                        <div>
                          <h4 className="text-xs font-medium text-red-700 mb-1">
                            Error
                          </h4>
                          <div className="text-sm text-red-600 bg-red-50 rounded-lg p-3">
                            {run.error_message}
                          </div>
                        </div>
                      )}

                      {/* Logs */}
                      {run.logs && (
                        <div>
                          <h4 className="text-xs font-medium text-gray-700 mb-1">
                            Logs
                          </h4>
                          <pre className="text-xs text-gray-600 bg-gray-900 text-gray-300 rounded-lg p-3 whitespace-pre-wrap max-h-48 overflow-y-auto font-mono">
                            {run.logs}
                          </pre>
                        </div>
                      )}

                      {/* Result data */}
                      {run.result_data && (
                        <div>
                          <h4 className="text-xs font-medium text-gray-700 mb-1">
                            Details
                          </h4>
                          <pre className="text-xs bg-gray-50 rounded-lg p-3 max-h-48 overflow-y-auto font-mono">
                            {JSON.stringify(run.result_data, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </Card>
          );
        })}
      </div>

      {/* All runs history */}
      {runs.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">
            Run History ({runs.length})
          </h3>
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-500 text-xs">
                <tr>
                  <th className="text-left px-4 py-2 font-medium">Stage</th>
                  <th className="text-left px-4 py-2 font-medium">Status</th>
                  <th className="text-left px-4 py-2 font-medium">Started</th>
                  <th className="text-left px-4 py-2 font-medium">Duration</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {runs.map((run) => (
                  <tr
                    key={run.id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() =>
                      setExpandedRun(expandedRun === run.id ? null : run.id)
                    }
                  >
                    <td className="px-4 py-2">
                      {STAGE_ICONS[run.stage]} {STAGE_LABELS[run.stage]}
                    </td>
                    <td className="px-4 py-2">
                      <StatusPill status={run.status} />
                    </td>
                    <td className="px-4 py-2 text-gray-500">
                      {run.started_at
                        ? new Date(run.started_at).toLocaleString()
                        : "—"}
                    </td>
                    <td className="px-4 py-2 text-gray-500">
                      {run.started_at && run.completed_at
                        ? formatDuration(run.started_at, run.completed_at)
                        : run.status === "running"
                          ? "…"
                          : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatusPill({ status }: { status: PipelineStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${PIPELINE_STATUS_COLORS[status]}`}
    >
      {status === "running" && <Spinner size="sm" />}
      {status}
    </span>
  );
}

function formatDuration(start: string, end: string): string {
  const ms = new Date(end).getTime() - new Date(start).getTime();
  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  if (minutes < 60) return `${minutes}m ${remainingSeconds}s`;
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return `${hours}h ${remainingMinutes}m`;
}
