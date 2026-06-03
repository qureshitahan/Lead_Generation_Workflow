import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getStats } from "../api/client";
import { Card, Loading, PageHeader, StatusBadge } from "../components/ui";

function Stat({
  label,
  value,
  to,
  hint,
}: {
  label: string;
  value: number | string;
  to?: string;
  hint?: string;
}) {
  const inner = (
    <Card className="p-5 transition hover:shadow-md">
      <div className="text-sm font-medium text-slate-500">{label}</div>
      <div className="mt-2 text-3xl font-bold text-slate-900">{value}</div>
      {hint && <div className="mt-1 text-xs text-slate-400">{hint}</div>}
    </Card>
  );
  return to ? <Link to={to}>{inner}</Link> : inner;
}

export default function Dashboard() {
  const { data, isLoading } = useQuery({ queryKey: ["stats"], queryFn: getStats });

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle="Pipeline overview — import jobs, review, match candidates, and run reviewed outreach."
      />
      {isLoading || !data ? (
        <Loading />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <Stat label="Jobs" value={data.jobs_total} to="/jobs" />
            <Stat
              label="Direct employers"
              value={data.direct_employers}
              to="/companies"
              hint={`${data.staffing_firms} staffing/recruiting flagged`}
            />
            <Stat label="Candidates" value={data.candidates_total} to="/candidates" />
            <Stat label="Matches" value={data.matches_total} to="/matches" />
            <Stat label="Companies" value={data.companies_total} to="/companies" />
            <Stat label="Contacts" value={data.contacts_total} to="/contacts" />
            <Stat label="Email drafts" value={data.email_drafts_total} to="/emails" />
            <Stat label="Calls queued" value={data.calls_total} to="/calls" />
          </div>

          <Card className="mt-6 p-5">
            <div className="mb-3 text-sm font-semibold text-slate-700">
              Jobs by status
            </div>
            {Object.keys(data.jobs_by_status).length === 0 ? (
              <p className="text-sm text-slate-400">
                No jobs yet. Head to{" "}
                <Link to="/import" className="font-medium text-slate-900 underline">
                  Import Jobs
                </Link>{" "}
                to load a Bright Data file.
              </p>
            ) : (
              <div className="flex flex-wrap gap-3">
                {Object.entries(data.jobs_by_status).map(([status, count]) => (
                  <div
                    key={status}
                    className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2"
                  >
                    <StatusBadge status={status} />
                    <span className="text-sm font-semibold text-slate-700">
                      {count}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
