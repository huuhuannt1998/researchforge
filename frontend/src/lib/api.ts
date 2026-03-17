import type {
  EvidenceCard,
  EvidenceCardCreateInput,
  EvidenceCardUpdateInput,
  ExperimentPlan,
  ExperimentPlanCreateInput,
  ExperimentPlanUpdateInput,
  LiteratureItem,
  LiteratureItemCreateInput,
  LiteratureItemUpdateInput,
  PipelineRun,
  PipelineStage,
  Project,
  ProjectCreateInput,
  ProjectSummary,
  ProjectUpdateInput,
  ResearchQuestion,
  ResearchQuestionCreateInput,
  ResearchQuestionUpdateInput,
} from "@/lib/types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ---------------------------------------------------------------------------
// Generic fetch wrapper
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });

  if (res.status === 204) return undefined as T;

  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = await res.json();
      message = body.detail ?? message;
    } catch {
      // ignore parse error
    }
    throw new ApiError(res.status, message);
  }

  return res.json() as T;
}

// ---------------------------------------------------------------------------
// API surface
// ---------------------------------------------------------------------------

export const api = {
  projects: {
    list: (params?: { skip?: number; limit?: number }) => {
      const qs = params
        ? "?" + new URLSearchParams(params as Record<string, string>).toString()
        : "";
      return request<ProjectSummary[]>(`/api/projects/${qs}`);
    },

    get: (id: string) => request<Project>(`/api/projects/${id}`),

    create: (data: ProjectCreateInput) =>
      request<Project>("/api/projects/", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    update: (id: string, data: ProjectUpdateInput) =>
      request<Project>(`/api/projects/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),

    delete: (id: string) =>
      request<void>(`/api/projects/${id}`, { method: "DELETE" }),
  },

  researchQuestions: {
    get: (projectId: string) =>
      request<ResearchQuestion>(
        `/api/projects/${projectId}/research-question`
      ),

    create: (projectId: string, data: ResearchQuestionCreateInput) =>
      request<ResearchQuestion>(
        `/api/projects/${projectId}/research-question`,
        { method: "POST", body: JSON.stringify(data) }
      ),

    update: (
      projectId: string,
      rqId: string,
      data: ResearchQuestionUpdateInput
    ) =>
      request<ResearchQuestion>(
        `/api/projects/${projectId}/research-question/${rqId}`,
        { method: "PATCH", body: JSON.stringify(data) }
      ),
  },

  literature: {
    list: (projectId: string) =>
      request<LiteratureItem[]>(`/api/projects/${projectId}/literature/items/`),

    get: (projectId: string, itemId: string) =>
      request<LiteratureItem>(
        `/api/projects/${projectId}/literature/items/${itemId}`
      ),

    create: (projectId: string, data: LiteratureItemCreateInput) =>
      request<LiteratureItem>(`/api/projects/${projectId}/literature/items/`, {
        method: "POST",
        body: JSON.stringify(data),
      }),

    update: (
      projectId: string,
      itemId: string,
      data: LiteratureItemUpdateInput
    ) =>
      request<LiteratureItem>(
        `/api/projects/${projectId}/literature/items/${itemId}`,
        { method: "PATCH", body: JSON.stringify(data) }
      ),

    delete: (projectId: string, itemId: string) =>
      request<void>(
        `/api/projects/${projectId}/literature/items/${itemId}`,
        { method: "DELETE" }
      ),

    uploadPdf: (projectId: string, itemId: string, file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return fetch(
        `${BASE_URL}/api/projects/${projectId}/literature/items/${itemId}/upload-pdf`,
        { method: "POST", body: formData }
      ).then(async (res) => {
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new ApiError(res.status, body.detail ?? res.statusText);
        }
        return res.json() as Promise<LiteratureItem>;
      });
    },

    runExtraction: (projectId: string, itemId: string) =>
      request<LiteratureItem>(
        `/api/projects/${projectId}/literature/items/${itemId}/extract`,
        { method: "POST" }
      ),
  },

  evidenceCards: {
    list: (projectId: string, literatureItemId?: string) => {
      const qs = literatureItemId
        ? `?literature_item_id=${literatureItemId}`
        : "";
      return request<EvidenceCard[]>(
        `/api/projects/${projectId}/literature/evidence/${qs}`
      );
    },

    get: (projectId: string, cardId: string) =>
      request<EvidenceCard>(
        `/api/projects/${projectId}/literature/evidence/${cardId}`
      ),

    create: (projectId: string, data: EvidenceCardCreateInput) =>
      request<EvidenceCard>(
        `/api/projects/${projectId}/literature/evidence/`,
        { method: "POST", body: JSON.stringify(data) }
      ),

    update: (
      projectId: string,
      cardId: string,
      data: EvidenceCardUpdateInput
    ) =>
      request<EvidenceCard>(
        `/api/projects/${projectId}/literature/evidence/${cardId}`,
        { method: "PATCH", body: JSON.stringify(data) }
      ),

    delete: (projectId: string, cardId: string) =>
      request<void>(
        `/api/projects/${projectId}/literature/evidence/${cardId}`,
        { method: "DELETE" }
      ),
  },

  experiments: {
    list: (projectId: string) =>
      request<ExperimentPlan[]>(`/api/projects/${projectId}/experiments/`),

    get: (projectId: string, planId: string) =>
      request<ExperimentPlan>(`/api/projects/${projectId}/experiments/${planId}`),

    create: (projectId: string, data: ExperimentPlanCreateInput = {}) =>
      request<ExperimentPlan>(`/api/projects/${projectId}/experiments/`, {
        method: "POST",
        body: JSON.stringify(data),
      }),

    update: (
      projectId: string,
      planId: string,
      data: ExperimentPlanUpdateInput
    ) =>
      request<ExperimentPlan>(
        `/api/projects/${projectId}/experiments/${planId}`,
        { method: "PATCH", body: JSON.stringify(data) }
      ),

    delete: (projectId: string, planId: string) =>
      request<void>(`/api/projects/${projectId}/experiments/${planId}`, {
        method: "DELETE",
      }),
  },

  pipeline: {
    list: (projectId: string, stage?: PipelineStage) => {
      const qs = stage ? `?stage=${stage}` : "";
      return request<PipelineRun[]>(
        `/api/projects/${projectId}/pipeline/${qs}`
      );
    },

    get: (projectId: string, runId: string) =>
      request<PipelineRun>(
        `/api/projects/${projectId}/pipeline/${runId}`
      ),

    triggerStage: (projectId: string, stage: PipelineStage) =>
      request<PipelineRun>(
        `/api/projects/${projectId}/pipeline/${stage}/run`,
        { method: "POST" }
      ),

    triggerAll: (projectId: string) =>
      request<PipelineRun[]>(
        `/api/projects/${projectId}/pipeline/run-all`,
        { method: "POST" }
      ),
  },
};
