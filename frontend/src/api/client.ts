import axios from "axios";
import type {
  Call,
  Candidate,
  Company,
  Contact,
  DashboardStats,
  DiscoverImportSummary,
  EmailDraft,
  ImportSummary,
  Job,
  JobSearchRecord,
  Match,
  Page,
} from "../types";

// Same-origin in dev thanks to the Vite proxy (see vite.config.ts).
export const api = axios.create({ baseURL: "/" });

// --- Stats ---
export const getStats = () =>
  api.get<DashboardStats>("/api/stats").then((r) => r.data);

// --- Jobs ---
export interface JobFilters {
  status?: string;
  source?: string;
  min_relevance?: number;
  direct_employer?: boolean;
  search?: string;
  batch_id?: string;
  sort?: string;
  limit?: number;
  offset?: number;
}
export const listJobs = (params: JobFilters = {}) =>
  api.get<Page<Job>>("/api/jobs", { params }).then((r) => r.data);
export const getJob = (id: number) =>
  api.get<Job>(`/api/jobs/${id}`).then((r) => r.data);
export const reviewJob = (
  id: number,
  status: "approved" | "rejected",
  notes?: string
) =>
  api
    .post<Job>(`/api/jobs/${id}/review`, { status, notes })
    .then((r) => r.data);
export const listJobContacts = (jobId: number, limit = 25) =>
  api
    .get<Page<Contact>>(`/api/jobs/${jobId}/contacts`, { params: { limit } })
    .then((r) => r.data);
export const findJobContacts = (jobId: number, maxContacts: number) =>
  api
    .post<Page<Contact>>(
      `/api/jobs/${jobId}/find-contacts`,
      { max_contacts: maxContacts },
      { timeout: 120000 }
    )
    .then((r) => r.data);
export const getApolloPhoneWebhookStatus = () =>
  api
    .get<{
      phone_reveal_enabled: boolean;
      webhook_configured: boolean;
    }>("/api/webhooks/apollo/phone/status")
    .then((r) => r.data);

// --- Companies ---
export const listCompanies = (params: Record<string, unknown> = {}) =>
  api.get<Page<Company>>("/api/companies", { params }).then((r) => r.data);
export const enrichCompany = (id: number) =>
  api.post<Contact[]>(`/api/companies/${id}/enrich`).then((r) => r.data);

// --- Contacts ---
export const listContacts = (params: Record<string, unknown> = {}) =>
  api.get<Page<Contact>>("/api/contacts", { params }).then((r) => r.data);
export const setContactApproval = (id: number, approved: boolean) =>
  api
    .post<Contact>(`/api/contacts/${id}/approval`, {
      approved_for_outreach: approved,
    })
    .then((r) => r.data);

// --- Candidates ---
export const listCandidates = (params: Record<string, unknown> = {}) =>
  api.get<Page<Candidate>>("/api/candidates", { params }).then((r) => r.data);
export interface CandidateCreate {
  name: string;
  resume_text?: string;
  target_roles?: string[];
  skills?: string[];
  years_experience?: number;
  location?: string;
}
export const createCandidate = (payload: CandidateCreate) =>
  api.post<Candidate>("/api/candidates", payload).then((r) => r.data);

// --- Matches ---
export const listMatches = (params: Record<string, unknown> = {}) =>
  api.get<Page<Match>>("/api/matches", { params }).then((r) => r.data);
export const generateMatches = (jobId: number, minScore = 0) =>
  api
    .post<Match[]>(`/api/matches/generate/${jobId}`, { min_score: minScore })
    .then((r) => r.data);

// --- Emails ---
export const listEmails = (params: Record<string, unknown> = {}) =>
  api.get<Page<EmailDraft>>("/api/emails", { params }).then((r) => r.data);
export const generateEmail = (payload: {
  job_id: number;
  candidate_id: number;
  contact_id?: number;
  match_id?: number;
}) => api.post<EmailDraft>("/api/emails/generate", payload).then((r) => r.data);
export const updateEmail = (
  id: number,
  payload: { subject?: string; body?: string }
) => api.patch<EmailDraft>(`/api/emails/${id}`, payload).then((r) => r.data);
export const setEmailStatus = (id: number, status: string) =>
  api
    .post<EmailDraft>(`/api/emails/${id}/status`, { status })
    .then((r) => r.data);

// --- Calls ---
export const listCalls = (params: Record<string, unknown> = {}) =>
  api.get<Page<Call>>("/api/calls", { params }).then((r) => r.data);
export const generateCall = (payload: {
  job_id: number;
  candidate_id: number;
  contact_id?: number;
  match_id?: number;
}) => api.post<Call>("/api/calls/generate", payload).then((r) => r.data);
export const setCallStatus = (id: number, status: string) =>
  api.post<Call>(`/api/calls/${id}/status`, { status }).then((r) => r.data);

// --- Job discovery (Bright Data / stub) ---
export interface JobDiscoverPayload {
  keyword: string;
  location?: string;
  time_range?: string;
  country?: string;
  job_type?: string;
  experience_level?: string;
  remote?: string;
  company?: string;
  location_radius?: string;
  limit?: number;
  provider?: string;
}
export const discoverJobs = (payload: JobDiscoverPayload) =>
  api
    .post<DiscoverImportSummary>("/api/discover/jobs", payload, {
      timeout: 360000, // Bright Data collection can take several minutes
    })
    .then((r) => r.data);
export const listDiscoverySearches = (params: Record<string, unknown> = {}) =>
  api
    .get<Page<JobSearchRecord>>("/api/discover/searches", { params })
    .then((r) => r.data);

// --- Import ---
export const importPaste = (source: string, content: string) =>
  api
    .post<ImportSummary>("/api/imports/paste", { source, content })
    .then((r) => r.data);
export const importFile = (source: string, file: File) => {
  const form = new FormData();
  form.append("source", source);
  form.append("file", file);
  return api
    .post<ImportSummary>("/api/imports/file", form)
    .then((r) => r.data);
};
