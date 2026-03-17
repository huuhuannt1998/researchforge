// ---------------------------------------------------------------------------
// Domain types — mirror the backend Pydantic schemas
// ---------------------------------------------------------------------------

export type ProjectStatus =
  | "draft"
  | "active"
  | "submitted"
  | "published"
  | "archived";

export interface ResearchQuestion {
  id: string;
  project_id: string;
  main_question: string;
  hypotheses: string[];
  assumptions: string[];
  novelty_claim: string | null;
  scope_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectSummary {
  id: string;
  title: string;
  short_idea: string | null;
  domain: string | null;
  target_venue: string | null;
  status: ProjectStatus;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface Project extends ProjectSummary {
  problem_statement: string | null;
  research_questions: ResearchQuestion[];
}

// ---------------------------------------------------------------------------
// Input types — used for create/update calls
// ---------------------------------------------------------------------------

export interface ProjectCreateInput {
  title: string;
  short_idea?: string;
  problem_statement?: string;
  domain?: string;
  target_venue?: string;
  status?: ProjectStatus;
  tags?: string[];
}

export type ProjectUpdateInput = Partial<ProjectCreateInput>;

export interface ResearchQuestionCreateInput {
  main_question: string;
  hypotheses?: string[];
  assumptions?: string[];
  novelty_claim?: string;
  scope_notes?: string;
}

export type ResearchQuestionUpdateInput = Partial<ResearchQuestionCreateInput>;

// ---------------------------------------------------------------------------
// UI helpers
// ---------------------------------------------------------------------------

export const STATUS_LABELS: Record<ProjectStatus, string> = {
  draft: "Draft",
  active: "Active",
  submitted: "Submitted",
  published: "Published",
  archived: "Archived",
};

export const STATUS_COLORS: Record<ProjectStatus, string> = {
  draft: "bg-gray-100 text-gray-600",
  active: "bg-blue-100 text-blue-700",
  submitted: "bg-amber-100 text-amber-700",
  published: "bg-green-100 text-green-700",
  archived: "bg-gray-100 text-gray-400",
};

// ---------------------------------------------------------------------------
// Literature types
// ---------------------------------------------------------------------------

export interface LiteratureItem {
  id: string;
  project_id: string;
  title: string;
  authors: string[];
  year: number | null;
  venue: string | null;
  doi_or_url: string | null;
  abstract: string | null;
  bibtex: string | null;
  tags: string[];
  relevance_score: number | null;
  pdf_path: string | null;
  extracted_summary: string | null;
  extracted_methods: string[] | null;
  extracted_datasets: string[] | null;
  extracted_metrics: string[] | null;
  extracted_limitations: string[] | null;
  created_at: string;
  updated_at: string;
}

/** Derived helper: has extraction been run on this item? */
export function isExtracted(item: LiteratureItem): boolean {
  return item.extracted_summary !== null;
}

export interface LiteratureItemCreateInput {
  title: string;
  authors?: string[];
  year?: number;
  venue?: string;
  doi_or_url?: string;
  abstract?: string;
  bibtex?: string;
  tags?: string[];
  relevance_score?: number;
}

export type LiteratureItemUpdateInput = Partial<
  LiteratureItemCreateInput & {
    extracted_summary: string;
    extracted_methods: string[];
    extracted_datasets: string[];
    extracted_metrics: string[];
    extracted_limitations: string[];
  }
>;

export type EvidenceType =
  | "empirical"
  | "theoretical"
  | "survey"
  | "case_study"
  | "benchmark"
  | "other";

export const EVIDENCE_TYPE_LABELS: Record<EvidenceType, string> = {
  empirical: "Empirical",
  theoretical: "Theoretical",
  survey: "Survey",
  case_study: "Case Study",
  benchmark: "Benchmark",
  other: "Other",
};

export const EVIDENCE_TYPE_COLORS: Record<EvidenceType, string> = {
  empirical: "bg-blue-100 text-blue-700",
  theoretical: "bg-purple-100 text-purple-700",
  survey: "bg-amber-100 text-amber-700",
  case_study: "bg-teal-100 text-teal-700",
  benchmark: "bg-green-100 text-green-700",
  other: "bg-gray-100 text-gray-600",
};

export interface EvidenceCard {
  id: string;
  project_id: string;
  literature_item_id: string | null;
  claim: string;
  evidence_type: EvidenceType | null;
  quote_or_paraphrase: string | null;
  method: string | null;
  metrics: Record<string, unknown> | null;
  limitations: string | null;
  notes: string | null;
  confidence: number | null;
  created_at: string;
  updated_at: string;
}

export interface EvidenceCardCreateInput {
  claim: string;
  literature_item_id?: string | null;
  evidence_type?: EvidenceType | null;
  quote_or_paraphrase?: string;
  method?: string;
  metrics?: Record<string, unknown>;
  limitations?: string;
  notes?: string;
  confidence?: number;
}

export type EvidenceCardUpdateInput = Partial<EvidenceCardCreateInput>;

// ---------------------------------------------------------------------------
// Experiment Planner types
// ---------------------------------------------------------------------------

export interface ExperimentPlan {
  id: string;
  project_id: string;
  objective: string | null;
  hypotheses: string[];
  baselines: string[];
  datasets: string[];
  metrics: string[];
  ablations: string[];
  expected_claims: string[];
  risks: string[];
  compute_notes: string | null;
  reproducibility_requirements: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExperimentPlanCreateInput {
  objective?: string;
  hypotheses?: string[];
  baselines?: string[];
  datasets?: string[];
  metrics?: string[];
  ablations?: string[];
  expected_claims?: string[];
  risks?: string[];
  compute_notes?: string;
  reproducibility_requirements?: string;
}

export type ExperimentPlanUpdateInput = Partial<ExperimentPlanCreateInput>;

/** Human-readable labels for each structured list field */
export const EXPERIMENT_FIELD_LABELS: Record<
  keyof Pick<
    ExperimentPlan,
    | "hypotheses"
    | "baselines"
    | "datasets"
    | "metrics"
    | "ablations"
    | "expected_claims"
    | "risks"
  >,
  { label: string; placeholder: string; description: string }
> = {
  hypotheses: {
    label: "Hypotheses",
    placeholder: "e.g. H1: Our model achieves >90% accuracy on SST-2",
    description: "Falsifiable claims you plan to test",
  },
  baselines: {
    label: "Baselines",
    placeholder: "e.g. BERT-base, GPT-4o-mini",
    description: "Methods / systems you compare against",
  },
  datasets: {
    label: "Datasets",
    placeholder: "e.g. GLUE, SQuAD 2.0",
    description: "Datasets used for training, evaluation, or few-shot testing",
  },
  metrics: {
    label: "Metrics",
    placeholder: "e.g. Accuracy, F1, BLEU",
    description: "Quantitative measures used to evaluate results",
  },
  ablations: {
    label: "Ablations",
    placeholder: "e.g. Without pre-training, Without layer-norm",
    description: "Component removal experiments to isolate contributions",
  },
  expected_claims: {
    label: "Expected Claims",
    placeholder: "e.g. State-of-the-art on GLUE benchmark",
    description: "Contributions you expect to be able to claim in the paper",
  },
  risks: {
    label: "Risks",
    placeholder: "e.g. Compute budget may be insufficient",
    description: "Potential blockers, failure modes, or uncertainties",
  },
};
