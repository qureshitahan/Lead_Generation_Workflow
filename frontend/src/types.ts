// Types mirroring the backend Pydantic schemas (app/schemas/entities.py).

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface Job {
  id: number;
  source: string;
  source_job_id?: string | null;
  title: string;
  company_id?: number | null;
  company_name?: string | null;
  location?: string | null;
  description?: string | null;
  source_url?: string | null;
  company_linkedin_url?: string | null;
  employment_type?: string | null;
  seniority?: string | null;
  job_function?: string | null;
  industries?: string | null;
  salary_text?: string | null;
  job_poster?: string | null;
  applicants_count?: number | null;
  easy_apply?: boolean | null;
  posted_at?: string | null;
  relevance_score?: number | null;
  relevance_reason?: string | null;
  matched_role?: string | null;
  is_direct_employer?: boolean | null;
  is_staffing_or_recruiting?: boolean | null;
  employer_confidence?: number | null;
  employer_explanation?: string | null;
  best_match_score?: number | null;
  status: string;
  reviewed_by?: string | null;
  review_notes?: string | null;
  created_at: string;
}

export interface Company {
  id: number;
  name: string;
  domain?: string | null;
  website?: string | null;
  linkedin_url?: string | null;
  industry?: string | null;
  employee_count?: number | null;
  headquarters?: string | null;
  phone?: string | null;
  funding?: string | null;
  revenue?: string | null;
  is_direct_employer?: boolean | null;
  is_staffing_or_recruiting?: boolean | null;
  employer_confidence?: number | null;
  employer_explanation?: string | null;
  enrichment_status: string;
  enrichment_source?: string | null;
  do_not_contact: boolean;
  created_at: string;
}

export interface Contact {
  id: number;
  company_id: number;
  name: string;
  title?: string | null;
    email?: string | null;
    email_status?: string | null;
    phone?: string | null;
    phone_reveal_status?: string | null;
    linkedin_url?: string | null;
  source?: string | null;
  confidence_score?: number | null;
  usefulness_score?: number | null;
  rank_reason?: string | null;
  approved_for_outreach: boolean;
  do_not_contact: boolean;
  created_at: string;
}

export interface Candidate {
  id: number;
  name: string;
  target_roles?: string[] | null;
  skills?: string[] | null;
  years_experience?: number | null;
  location?: string | null;
  work_authorization?: string | null;
  availability?: string | null;
  expected_salary?: string | null;
  resume_text?: string | null;
  summary?: string | null;
  selling_points?: string[] | null;
  is_active: boolean;
  created_at: string;
}

export interface Match {
  id: number;
  job_id: number;
  candidate_id: number;
  score: number;
  matched_skills?: string[] | null;
  missing_skills?: string[] | null;
  concerns?: string[] | null;
  reason?: string | null;
  pitch?: string | null;
  created_at: string;
}

export interface EmailDraft {
  id: number;
  job_id?: number | null;
  company_id?: number | null;
  contact_id?: number | null;
  candidate_id?: number | null;
  match_id?: number | null;
  subject: string;
  body: string;
  status: string;
  provider?: string | null;
  provider_message_id?: string | null;
  approved_by?: string | null;
  created_at: string;
}

export interface Call {
  id: number;
  job_id?: number | null;
  company_id?: number | null;
  contact_id?: number | null;
  candidate_id?: number | null;
  match_id?: number | null;
  phone_number?: string | null;
  script?: string | null;
  status: string;
  transcript?: string | null;
  outcome_notes?: string | null;
  human_handoff_needed: boolean;
  meeting_requested: boolean;
  created_at: string;
}

export interface DashboardStats {
  jobs_total: number;
  jobs_by_status: Record<string, number>;
  companies_total: number;
  direct_employers: number;
  staffing_firms: number;
  contacts_total: number;
  candidates_total: number;
  matches_total: number;
  email_drafts_total: number;
  calls_total: number;
}

export interface DiscoverImportSummary {
  search_id: number;
  provider: string;
  snapshot_id?: string | null;
  records_fetched: number;
  source: string;
  batch_id: string;
  total_records: number;
  imported: number;
  duplicates: number;
  errors: number;
  job_ids: number[];
  error_messages: string[];
}

export interface JobSearchRecord {
  id: number;
  provider: string;
  keyword: string;
  location?: string | null;
  filters?: Record<string, unknown> | null;
  snapshot_id?: string | null;
  import_batch_id?: string | null;
  status: string;
  records_fetched?: number | null;
  records_imported?: number | null;
  records_duplicates?: number | null;
  error_message?: string | null;
  created_at: string;
}

export interface ImportSummary {
  source: string;
  batch_id: string;
  total_records: number;
  imported: number;
  duplicates: number;
  errors: number;
  job_ids: number[];
  error_messages: string[];
}
