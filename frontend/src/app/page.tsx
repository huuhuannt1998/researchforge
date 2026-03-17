"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ProjectSummary } from "@/lib/types";
import { formatRelativeDate } from "@/lib/utils";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import StatusBadge from "@/components/ui/StatusBadge";
import Spinner from "@/components/ui/Spinner";
import PageHeader from "@/components/layout/PageHeader";

export default function DashboardPage() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.projects
      .list()
      .then(setProjects)
      .catch((err: Error) => setError(err.message ?? "Failed to load projects"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle="All research projects"
        action={
          <Link href="/projects/new">
            <Button>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New Project
            </Button>
          </Link>
        }
      />

      <div className="p-8">
        {loading && (
          <div className="flex justify-center py-20">
            <Spinner size="lg" />
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
            <strong>Error:</strong> {error}
            <p className="mt-1 text-xs text-red-500">
              Make sure the backend is running at{" "}
              {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}.
            </p>
          </div>
        )}

        {!loading && !error && projects.length === 0 && (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-14 h-14 rounded-full bg-gray-100 flex items-center justify-center mb-4">
              <svg className="w-7 h-7 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-gray-900 mb-1">No projects yet</h3>
            <p className="text-sm text-gray-500 mb-5 max-w-xs">
              Start your first research project to begin tracking ideas, literature, experiments, and drafts.
            </p>
            <Link href="/projects/new">
              <Button>Create your first project</Button>
            </Link>
          </div>
        )}

        {!loading && !error && projects.length > 0 && (
          <>
            <div className="grid grid-cols-4 gap-4 mb-8">
              {[
                { label: "Total Projects", value: projects.length },
                { label: "Active", value: projects.filter((p) => p.status === "active").length },
                { label: "Drafts", value: projects.filter((p) => p.status === "draft").length },
                { label: "Submitted", value: projects.filter((p) => p.status === "submitted").length },
              ].map((stat) => (
                <Card key={stat.label} className="px-5 py-4">
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">{stat.label}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
                </Card>
              ))}
            </div>

            <div className="space-y-3">
              {projects.map((project) => (
                <ProjectRow key={project.id} project={project} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function ProjectRow({ project }: { project: ProjectSummary }) {
  return (
    <Link href={`/projects/${project.id}`}>
      <Card hoverable className="px-6 py-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-1">
              <h3 className="text-sm font-semibold text-gray-900 truncate">{project.title}</h3>
              <StatusBadge status={project.status} />
            </div>
            {project.short_idea && (
              <p className="text-sm text-gray-500 line-clamp-1">{project.short_idea}</p>
            )}
            <div className="flex items-center gap-3 mt-2 flex-wrap">
              {project.domain && (
                <span className="text-xs text-gray-400">{project.domain}</span>
              )}
              {project.target_venue && (
                <span className="text-xs text-gray-400">→ {project.target_venue}</span>
              )}
              {project.tags.slice(0, 4).map((tag) => (
                <span key={tag} className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                  {tag}
                </span>
              ))}
            </div>
          </div>
          <div className="flex-shrink-0 text-right">
            <p className="text-xs text-gray-400">{formatRelativeDate(project.updated_at)}</p>
          </div>
        </div>
      </Card>
    </Link>
  );
}
