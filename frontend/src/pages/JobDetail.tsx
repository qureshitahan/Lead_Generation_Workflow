import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import {
  generateMatches,
  getJob,
  listMatches,
  reviewJob,
} from "../api/client";
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

export default function JobDetail() {
  const { id } = useParams();
  const jobId = Number(id);
  const qc = useQueryClient();

  const { data: job, isLoading } = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => getJob(jobId),
  });
  const { data: matches } = useQuery({
    queryKey: ["matches", { job_id: jobId }],
    queryFn: () => listMatches({ job_id: jobId }),
  });

  const review = useMutation({
    mutationFn: (status: "approved" | "rejected") => reviewJob(jobId, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["job", jobId] }),
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
