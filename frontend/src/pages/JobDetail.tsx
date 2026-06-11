import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import {
  findJobContacts,
  generateMatches,
  getApolloPhoneWebhookStatus,
  getJob,
  listJobContacts,
  listMatches,
  reviewJob,
} from "../api/client";
import type { Contact } from "../types";
import {
  Badge,
  Button,
  Card,
  EmployerBadge,
  Loading,
  PageHeader,
  ScoreBar,
  StatusBadge,
} from "../components/ui";

const EMAIL_STATUS_TONE: Record<string, "green" | "amber" | "slate"> = {
  verified: "green",
  likely: "amber",
  guessed: "amber",
  unavailable: "slate",
};

function Field({ label, value }: { label: string; value?: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase tracking-wide text-slate-400">
        {label}
      </dt>
      <dd className="mt-0.5 text-sm text-slate-800">{value ?? "—"}</dd>
    </div>
  );
}

function ContactRow({ c }: { c: Contact }) {
  return (
    <div className="flex items-start justify-between gap-3 rounded-lg border border-slate-200 p-3">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-slate-900">{c.name}</span>
          {c.linkedin_url && (
            <a
              href={c.linkedin_url}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-blue-600 underline"
            >
              LinkedIn
            </a>
          )}
        </div>
        <div className="text-sm text-slate-500">{c.title ?? "—"}</div>
        <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
          {c.email ? (
            <a href={`mailto:${c.email}`} className="text-blue-600 underline">
              {c.email}
            </a>
          ) : (
            <span className="text-xs text-slate-400">
              {c.email_status === "unavailable" ? "no email on file" : "email not revealed"}
            </span>
          )}
          {c.email_status && (
            <Badge tone={EMAIL_STATUS_TONE[c.email_status] ?? "slate"}>
              {c.email_status}
            </Badge>
          )}
          {c.phone ? (
            <a href={`tel:${c.phone}`} className="text-blue-600 underline">
              {c.phone}
            </a>
          ) : c.phone_reveal_status === "pending" ? (
            <Badge tone="amber">phone pending</Badge>
          ) : null}
        </div>
      </div>
      <div className="shrink-0 text-right">
        <div className="text-xs text-slate-400">usefulness</div>
        <ScoreBar value={c.usefulness_score} />
      </div>
    </div>
  );
}

export default function JobDetail() {
  const { id } = useParams();
  const jobId = Number(id);
  const qc = useQueryClient();
  const [maxContacts, setMaxContacts] = useState(3);

  const { data: job, isLoading } = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => getJob(jobId),
  });
  const { data: matches } = useQuery({
    queryKey: ["matches", { job_id: jobId }],
    queryFn: () => listMatches({ job_id: jobId }),
  });
  const { data: contacts } = useQuery({
    queryKey: ["job-contacts", jobId, maxContacts],
    queryFn: () => listJobContacts(jobId, maxContacts),
    // Phone numbers arrive asynchronously via Apollo's webhook a few minutes
    // after reveal. Poll while any contact is still pending so they appear
    // automatically without a manual refresh.
    refetchInterval: (query) => {
      const data = query.state.data as { items: Contact[] } | undefined;
      const pending = data?.items?.some(
        (c) => c.phone_reveal_status === "pending",
      );
      return pending ? 5000 : false;
    },
  });
  const { data: phoneStatus } = useQuery({
    queryKey: ["apollo-phone-status"],
    queryFn: () => getApolloPhoneWebhookStatus(),
  });

  const review = useMutation({
    mutationFn: (status: "approved" | "rejected") => reviewJob(jobId, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["job", jobId] }),
  });
  const findContacts = useMutation({
    mutationFn: () => findJobContacts(jobId, maxContacts),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["job-contacts", jobId] });
      qc.invalidateQueries({ queryKey: ["contacts"] });
      qc.invalidateQueries({ queryKey: ["companies"] });
    },
  });
  const match = useMutation({
    mutationFn: () => generateMatches(jobId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["matches", { job_id: jobId }] });
      qc.invalidateQueries({ queryKey: ["job", jobId] });
    },
  });

  if (isLoading || !job) return <Loading />;

  return (
    <div>
      <PageHeader
        title={job.title}
        subtitle={`${job.company_name ?? "Unknown company"} · ${job.location ?? "—"}`}
        actions={
          <>
            <Button variant="secondary" onClick={() => review.mutate("approved")}>
              Approve
            </Button>
            <Button variant="ghost" onClick={() => review.mutate("rejected")}>
              Reject
            </Button>
            <Button onClick={() => match.mutate()} disabled={match.isPending}>
              {match.isPending ? "Matching…" : "Match candidates"}
            </Button>
          </>
        }
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="p-5 lg:col-span-2">
          <div className="mb-4 flex flex-wrap gap-2">
            <StatusBadge status={job.status} />
            <EmployerBadge isDirect={job.is_direct_employer} />
            {job.matched_role && <Badge tone="blue">{job.matched_role}</Badge>}
            <Badge tone="slate">{job.source}</Badge>
          </div>

          <dl className="grid grid-cols-2 gap-4 md:grid-cols-3">
            <Field label="Employment" value={job.employment_type} />
            <Field label="Seniority" value={job.seniority} />
            <Field label="Function" value={job.job_function} />
            <Field label="Industries" value={job.industries} />
            <Field label="Salary" value={job.salary_text} />
            <Field label="Applicants" value={job.applicants_count} />
            <Field label="Job poster" value={job.job_poster} />
            <Field
              label="Posted"
              value={job.posted_at ? job.posted_at.slice(0, 10) : null}
            />
            <Field
              label="Source"
              value={
                job.source_url ? (
                  <a
                    className="text-blue-600 underline"
                    href={job.source_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    View posting
                  </a>
                ) : null
              }
            />
          </dl>

          {job.description && (
            <div className="mt-5">
              <div className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-400">
                Description
              </div>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
                {job.description}
              </p>
            </div>
          )}
        </Card>

        <div className="space-y-4">
          <Card className="p-5">
            <div className="mb-3 text-sm font-semibold text-slate-700">
              Relevance
            </div>
            <ScoreBar value={job.relevance_score} />
            <p className="mt-2 text-xs leading-relaxed text-slate-500">
              {job.relevance_reason}
            </p>
          </Card>
          <Card className="p-5">
            <div className="mb-3 text-sm font-semibold text-slate-700">
              Direct employer check
            </div>
            <div className="flex items-center gap-2">
              <EmployerBadge isDirect={job.is_direct_employer} />
              {job.employer_confidence != null && (
                <span className="text-xs text-slate-400">
                  {Math.round(job.employer_confidence)}% confidence
                </span>
              )}
            </div>
            <p className="mt-2 text-xs leading-relaxed text-slate-500">
              {job.employer_explanation}
            </p>
          </Card>
        </div>
      </div>

      <Card className="mt-4 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-sm font-semibold text-slate-700">
              Contacts at {job.company_name ?? "this company"}
            </div>
            <p className="mt-0.5 text-xs text-slate-400">
              Apollo finds decision-makers at this company and reveals their email
              (and phone when configured). You choose how many — each revealed
              contact uses Apollo credits.
            </p>
            {phoneStatus && !phoneStatus.webhook_configured && (
              <p className="mt-1 text-xs text-amber-700">
                Phone numbers are not enabled yet — set{" "}
                <code className="rounded bg-amber-100 px-1">APP_PUBLIC_URL</code> in
                backend/.env to your ngrok HTTPS URL and restart the backend.
              </p>
            )}
          </div>
          <div className="flex items-end gap-2">
            <label className="text-xs text-slate-500">
              <span className="mb-1 block font-medium">Contacts to find & reveal</span>
              <input
                type="number"
                min={1}
                max={25}
                value={maxContacts}
                onChange={(e) => setMaxContacts(Number(e.target.value))}
                className="w-20 rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </label>
            <Button
              onClick={() => findContacts.mutate()}
              disabled={findContacts.isPending}
            >
              {findContacts.isPending ? "Finding contacts…" : "Find contacts"}
            </Button>
          </div>
        </div>

        {findContacts.isError && (
          <p className="mt-3 text-sm text-rose-600">
            Couldn't find contacts. Check that Apollo is configured (ENRICHMENT_PROVIDER=apollo)
            and try again.
          </p>
        )}
        {findContacts.isSuccess && findContacts.data && (
          <p className="mt-3 text-sm text-slate-600">
            {findContacts.data.items.length === 0
              ? "Apollo couldn't find contacts for this company. Try a larger employer."
              : (() => {
                  const withEmail = findContacts.data.items.filter((c) => c.email).length;
                  return `Showing top ${findContacts.data.items.length} contact(s). ${withEmail} email(s) revealed (uses credits).`;
                })()}
          </p>
        )}

        <div className="mt-4 space-y-2">
          {!contacts || contacts.items.length === 0 ? (
            <p className="text-sm text-slate-400">
              No contacts yet. Set how many you want above, then click “Find contacts”.
            </p>
          ) : (
            contacts.items.map((c) => <ContactRow key={c.id} c={c} />)
          )}
        </div>
        {contacts && contacts.total > contacts.items.length && (
          <p className="mt-2 text-xs text-slate-400">
            Showing top {contacts.items.length} of {contacts.total} saved at this company.
          </p>
        )}
        {contacts && contacts.items.length > 0 && (
          <div className="mt-3 text-right">
            <Link to="/contacts" className="text-xs font-medium text-slate-500 underline">
              Manage & approve contacts →
            </Link>
          </div>
        )}
      </Card>

      <Card className="mt-4 p-5">
        <div className="mb-3 text-sm font-semibold text-slate-700">
          Candidate matches
        </div>
        {!matches || matches.items.length === 0 ? (
          <p className="text-sm text-slate-400">
            No matches yet. Click “Match candidates” to score this job against active
            candidates.
          </p>
        ) : (
          <div className="space-y-3">
            {matches.items.map((m) => (
              <div
                key={m.id}
                className="rounded-lg border border-slate-200 p-3"
              >
                <div className="flex items-center justify-between">
                  <Link
                    to={`/candidates`}
                    className="text-sm font-medium text-slate-900"
                  >
                    Candidate #{m.candidate_id}
                  </Link>
                  <ScoreBar value={m.score} />
                </div>
                {m.pitch && (
                  <p className="mt-2 text-sm text-slate-600">{m.pitch}</p>
                )}
                <div className="mt-2 flex flex-wrap gap-1">
                  {(m.matched_skills ?? []).map((s) => (
                    <Badge key={s} tone="green">
                      {s}
                    </Badge>
                  ))}
                  {(m.missing_skills ?? []).slice(0, 5).map((s) => (
                    <Badge key={s} tone="slate">
                      missing: {s}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
