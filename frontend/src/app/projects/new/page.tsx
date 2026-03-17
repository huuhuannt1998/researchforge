"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import type { ProjectCreateInput } from "@/lib/types";
import { parseTags } from "@/lib/utils";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Textarea from "@/components/ui/Textarea";
import Card from "@/components/ui/Card";
import PageHeader from "@/components/layout/PageHeader";
import Link from "next/link";

export default function NewProjectPage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState<
    Omit<ProjectCreateInput, "tags"> & { tags: string }
  >({
    title: "",
    short_idea: "",
    problem_statement: "",
    domain: "",
    target_venue: "",
    status: "draft",
    tags: "",
  });

  function set(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!form.title.trim()) {
      setError("Title is required.");
      return;
    }

    setSaving(true);
    try {
      const payload: ProjectCreateInput = {
        title: form.title.trim(),
        short_idea: form.short_idea?.trim() || undefined,
        problem_statement: form.problem_statement?.trim() || undefined,
        domain: form.domain?.trim() || undefined,
        target_venue: form.target_venue?.trim() || undefined,
        status: form.status,
        tags: parseTags(form.tags),
      };

      const project = await api.projects.create(payload);
      router.push(`/projects/${project.id}`);
    } catch (err) {
      setError((err as Error).message ?? "Failed to create project.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="New Project"
        subtitle="Define your research project"
        back={
          <Link href="/" className="text-xs text-gray-500 hover:text-gray-800 flex items-center gap-1">
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Dashboard
          </Link>
        }
      />

      <div className="p-8 max-w-2xl">
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <Card className="p-6 space-y-5">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
              Project Identity
            </h2>

            <Input
              label="Project Title"
              placeholder="e.g. Adversarial Robustness in RAG Pipelines"
              value={form.title}
              onChange={(e) => set("title", e.target.value)}
              required
            />

            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Domain"
                placeholder="e.g. AI Security"
                value={form.domain ?? ""}
                onChange={(e) => set("domain", e.target.value)}
              />
              <Input
                label="Target Venue"
                placeholder="e.g. IEEE S&P 2027"
                value={form.target_venue ?? ""}
                onChange={(e) => set("target_venue", e.target.value)}
              />
            </div>

            <Input
              label="Tags"
              placeholder="llm, security, adversarial"
              hint="Comma-separated list of tags"
              value={form.tags}
              onChange={(e) => set("tags", e.target.value)}
            />
          </Card>

          <Card className="p-6 space-y-5">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
              Research Idea
            </h2>

            <Textarea
              label="Short Idea"
              placeholder="One or two sentences capturing the core idea..."
              rows={2}
              value={form.short_idea ?? ""}
              onChange={(e) => set("short_idea", e.target.value)}
            />

            <Textarea
              label="Problem Statement"
              placeholder="Describe the problem you're solving in more detail. What gap does this address? Why does it matter?"
              rows={5}
              value={form.problem_statement ?? ""}
              onChange={(e) => set("problem_statement", e.target.value)}
            />
          </Card>

          <div className="flex items-center gap-3">
            <Button type="submit" loading={saving}>
              Create Project
            </Button>
            <Link href="/">
              <Button variant="secondary" type="button">
                Cancel
              </Button>
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
