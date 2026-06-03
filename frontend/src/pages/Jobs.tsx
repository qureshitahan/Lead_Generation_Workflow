import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listJobs, reviewJob, type JobFilters } from "../api/client";
import {
  Button,
  Card,
  EmployerBadge,
  EmptyState,
  Loading,
  PageHeader,
  ScoreBar,
  StatusBadge,
  Table,
  Td,
  Th,
} from "../components/ui";

export default function Jobs() {
  const qc = useQueryClient();
  const [filters, setFilters] = useState<JobFilters>({ sort: "relevance" });

  const { data, isLoading } = useQuery({
    queryKey: ["jobs", filters],
    queryFn: () => listJobs(filters),
  });

  const review = useMutation({
    mutationFn: ({ id, status }: { id: number; status: "approved" | "rejected" }) =>
      reviewJob(id, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["jobs"] });
      qc.invalidateQueries({ queryKey: ["stats"] });
    },
  });

  const set = (patch: Partial<JobFilters>) =>
    setFilters((f) => ({ ...f, ...patch }));

  return (
    <div>
      <PageHeader
        title="Jobs"
        subtitle="Imported postings with relevance + direct-employer scoring. Approve the ones worth pursuing."
      />

      <Card className="mb-4 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <input
            placeholder="Search title or company…"
            className="flex-1 rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
            onChange={(e) => set({ search: e.target.value || undefined })}
          />
          <select
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
            onChange={(e) => set({ status: e.target.value || undefined })}
          >
            <option value="">All statuses</option>
            {["review", "approved", "rejected", "matched", "new"].map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <select
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
            onChange={(e) =>
              set({
                direct_employer:
                  e.target.value === "" ? undefined : e.target.value === "true",
              })
            }
          >
            <option value="">All employers</option>
            <option value="true">Direct employers</option>
            <option value="false">Staffing/recruiting</option>
          </select>
          <select
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
            value={filters.sort}
            onChange={(e) => set({ sort: e.target.value })}
          >
            <option value="relevance">Sort: relevance</option>
            <option value="match">Sort: match score</option>
            <option value="posted">Sort: posted date</option>
            <option value="created">Sort: newest imported</option>
          </select>
        </div>
      </Card>

      <Card>
        {isLoading ? (
          <Loading />
        ) : !data || data.items.length === 0 ? (
          <EmptyState message="No jobs found. Import a Bright Data file to get started." />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Title</Th>
                <Th>Company</Th>
                <Th>Location</Th>
                <Th>Posted</Th>
                <Th>Source</Th>
                <Th>Relevance</Th>
                <Th>Employer</Th>
                <Th>Match</Th>
                <Th>Status</Th>
                <Th />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((job) => (
                <tr key={job.id} className="hover:bg-slate-50">
                  <Td className="font-medium text-slate-900">
                    <Link to={`/jobs/${job.id}`} className="hover:underline">
                      {job.title}
                    </Link>
                    {job.matched_role && (
                      <div className="text-xs text-slate-400">{job.matched_role}</div>
                    )}
                  </Td>
                  <Td>{job.company_name ?? "—"}</Td>
                  <Td className="text-slate-500">{job.location ?? "—"}</Td>
                  <Td className="text-slate-500">
                    {job.posted_at ? job.posted_at.slice(0, 10) : "—"}
                  </Td>
                  <Td>
                    <span className="text-xs uppercase text-slate-400">
                      {job.source}
                    </span>
                  </Td>
                  <Td>
                    <ScoreBar value={job.relevance_score} />
                  </Td>
                  <Td>
                    <EmployerBadge isDirect={job.is_direct_employer} />
                  </Td>
                  <Td>
                    <ScoreBar value={job.best_match_score} />
                  </Td>
                  <Td>
                    <StatusBadge status={job.status} />
                  </Td>
                  <Td>
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="secondary"
                        onClick={() => review.mutate({ id: job.id, status: "approved" })}
                      >
                        Approve
                      </Button>
                      <Button
                        variant="ghost"
                        onClick={() => review.mutate({ id: job.id, status: "rejected" })}
                      >
                        Reject
                      </Button>
                    </div>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
      {data && (
        <p className="mt-3 text-xs text-slate-400">{data.total} job(s) total</p>
      )}
    </div>
  );
}
