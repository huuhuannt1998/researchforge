"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Project } from "@/lib/types";
import { formatRelativeDate } from "@/lib/utils";
import Button from "@/components/ui/Button";
import StatusBadge from "@/components/ui/StatusBadge";
import Spinner from "@/components/ui/Spinner";
import Card from "@/components/ui/Card";
import PageHeader from "@/components/layout/PageHeader";
import ProjectOverviewTab from "@/components/projects/ProjectOverviewTab";
import LiteratureTab from "@/components/literature/LiteratureTab";
import ExperimentPlanTab from "@/components/experiments/ExperimentPlanTab";

type Tab = "overview" | "literature" | "experiments" | "writing" | "review";

const TABS: { id: Tab; label: string; soon?: boolean }[] = [
  { id: "overview", label: "Overview" },
  { id: "literature", label: "Literature" },
  { id: "experiments", label: "Experiments" },
  { id: "writing", label: "Writing", soon: true },
  { id: "review", label: "Reviewer Arena", soon: true },
];

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (!id) return;
    api.projects
      .get(id)
      .then(setProject)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  async function handleDelete() {
    if (!project || !confirm(`Delete "${project.title}"? This cannot be undone.`)) return;
    setDeleting(true);
    try {
      await api.projects.delete(project.id);
      router.push("/");
    } catch (err) {
      alert((err as Error).message);
      setDeleting(false);
    }
  }

  function handleProjectUpdate(updated: Project) {
    setProject(updated);
  }

  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="p-8">
        <div className="rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700 mb-4">
          {error ?? "Project not found"}
        </div>
        <Link href="/">
          <Button variant="secondary">Back to Dashboard</Button>
        </Link>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title={project.title}
        subtitle={`Updated ${formatRelativeDate(project.updated_at)}`}
        back={
          <Link href="/" className="text-xs text-gray-500 hover:text-gray-800 flex items-center gap-1">
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Dashboard
          </Link>
        }
        action={
          <div className="flex items-center gap-2">
            <StatusBadge status={project.status} />
            <Button
              variant="danger"
              size="sm"
              loading={deleting}
              onClick={handleDelete}
            >
              Delete
            </Button>
          </div>
        }
      />

      {/* Tab bar */}
      <div className="border-b border-gray-200 bg-white px-8">
        <div className="flex gap-0 -mb-px">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => !tab.soon && setActiveTab(tab.id)}
              className={[
                "px-4 py-3 text-sm font-medium border-b-2 transition-colors",
                activeTab === tab.id
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700",
                tab.soon ? "opacity-40 cursor-not-allowed" : "",
              ]
                .join(" ")
                .trim()}
            >
              {tab.label}
              {tab.soon && (
                <span className="ml-1.5 text-xs bg-gray-100 text-gray-400 rounded px-1 py-0.5">
                  soon
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      {activeTab === "overview" && (
        <div className="p-8">
          <ProjectOverviewTab project={project} onUpdate={handleProjectUpdate} />
        </div>
      )}
      {activeTab === "literature" && (
        <div className="h-[calc(100vh-12rem)]">
          <LiteratureTab projectId={project.id} />
        </div>
      )}
      {activeTab === "experiments" && (
        <div className="h-[calc(100vh-12rem)]">
          <ExperimentPlanTab projectId={project.id} />
        </div>
      )}
    </div>
  );
}
