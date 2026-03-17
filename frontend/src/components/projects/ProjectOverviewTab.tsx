"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { Project, ProjectStatus, ProjectUpdateInput } from "@/lib/types";
import { joinTags, parseTags } from "@/lib/utils";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Textarea from "@/components/ui/Textarea";
import Card from "@/components/ui/Card";

const STATUS_OPTIONS: { value: ProjectStatus; label: string }[] = [
  { value: "draft", label: "Draft" },
  { value: "active", label: "Active" },
  { value: "submitted", label: "Submitted" },
  { value: "published", label: "Published" },
  { value: "archived", label: "Archived" },
];

interface Props {
  project: Project;
  onUpdate: (updated: Project) => void;
}

export default function ProjectOverviewTab({ project, onUpdate }: Props) {
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    title: project.title,
    short_idea: project.short_idea ?? "",
    problem_statement: project.problem_statement ?? "",
    domain: project.domain ?? "",
    target_venue: project.target_venue ?? "",
    status: project.status as ProjectStatus,
    tags: joinTags(project.tags),
  });

  function set(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function handleCancel() {
    setForm({
      title: project.title,
      short_idea: project.short_idea ?? "",
      problem_statement: project.problem_statement ?? "",
      domain: project.domain ?? "",
      target_venue: project.target_venue ?? "",
      status: project.status,
      tags: joinTags(project.tags),
    });
    setEditing(false);
    setError(null);
  }

  async function handleSave() {
    if (!form.title.trim()) {
      setError("Title is required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const payload: ProjectUpdateInput = {
        title: form.title.trim(),
        short_idea: form.short_idea.trim() || undefined,
        problem_statement: form.problem_statement.trim() || undefined,
        domain: form.domain.trim() || undefined,
        target_venue: form.target_venue.trim() || undefined,
        status: form.status,
        tags: parseTags(form.tags),
      };
      const updated = await api.projects.update(project.id, payload);
      onUpdate(updated);
      setEditing(false);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  }

  if (!editing) {
    return (
      <div className="max-w-2xl space-y-5">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
            Project Brief
          </h2>
          <Button variant="secondary" size="sm" onClick={() => setEditing(true)}>
            Edit
          </Button>
        </div>

        <Card className="divide-y divide-gray-100">
          <FieldRow label="Title" value={project.title} />
          <FieldRow label="Status" value={project.status} />
          <FieldRow label="Domain" value={project.domain} />
          <FieldRow label="Target Venue" value={project.target_venue} />
          <FieldRow
            label="Tags"
            value={
              project.tags.length > 0
                ? project.tags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600 mr-1 mb-1"
                    >
                      {tag}
                    </span>
                  ))
                : undefined
            }
          />
          <FieldRow label="Short Idea" value={project.short_idea} wide />
          <FieldRow label="Problem Statement" value={project.problem_statement} wide />
        </Card>

        {/* Research metadata */}
        <div className="grid grid-cols-2 gap-4 text-xs text-gray-400">
          <p>Created: {new Date(project.created_at).toLocaleString()}</p>
          <p>Updated: {new Date(project.updated_at).toLocaleString()}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
          Edit Project
        </h2>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <Card className="p-6 space-y-5">
        <Input
          label="Title"
          value={form.title}
          onChange={(e) => set("title", e.target.value)}
          required
        />

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Domain"
            value={form.domain}
            onChange={(e) => set("domain", e.target.value)}
          />
          <Input
            label="Target Venue"
            value={form.target_venue}
            onChange={(e) => set("target_venue", e.target.value)}
          />
        </div>

        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">Status</label>
          <select
            value={form.status}
            onChange={(e) => set("status", e.target.value)}
            className="block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <Input
          label="Tags"
          hint="Comma-separated"
          value={form.tags}
          onChange={(e) => set("tags", e.target.value)}
        />
      </Card>

      <Card className="p-6 space-y-5">
        <Textarea
          label="Short Idea"
          rows={2}
          value={form.short_idea}
          onChange={(e) => set("short_idea", e.target.value)}
        />
        <Textarea
          label="Problem Statement"
          rows={5}
          value={form.problem_statement}
          onChange={(e) => set("problem_statement", e.target.value)}
        />
      </Card>

      <div className="flex items-center gap-3">
        <Button onClick={handleSave} loading={saving}>
          Save Changes
        </Button>
        <Button variant="secondary" onClick={handleCancel} disabled={saving}>
          Cancel
        </Button>
      </div>
    </div>
  );
}

interface FieldRowProps {
  label: string;
  value?: string | React.ReactNode | null;
  wide?: boolean;
}

function FieldRow({ label, value, wide }: FieldRowProps) {
  if (!value && value !== 0) {
    return (
      <div className={`px-5 py-3 ${wide ? "flex flex-col gap-1" : "flex items-start gap-4"}`}>
        <span className="text-sm font-medium text-gray-500 w-36 flex-shrink-0">{label}</span>
        <span className="text-sm text-gray-300 italic">—</span>
      </div>
    );
  }

  return (
    <div className={`px-5 py-3 ${wide ? "flex flex-col gap-1" : "flex items-start gap-4"}`}>
      <span className="text-sm font-medium text-gray-500 w-36 flex-shrink-0">{label}</span>
      <span className="text-sm text-gray-900 whitespace-pre-wrap">{value}</span>
    </div>
  );
}
