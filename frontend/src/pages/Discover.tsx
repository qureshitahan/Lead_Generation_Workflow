import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { discoverJobs, listDiscoverySearches } from "../api/client";
import type { DiscoverImportSummary } from "../types";
import {
  Button,
  Card,
  EmptyState,
  Loading,
  PageHeader,
  StatusBadge,
} from "../components/ui";

const TIME_RANGES = [
  "",
  "Past 24 hours",
  "Past week",
  "Past month",
  "Any time",
];

const JOB_TYPES = ["", "Full-time", "Part-time", "Contract", "Temporary", "Internship"];

const REMOTE_OPTIONS = ["", "On-site", "Remote", "Hybrid"];

const EXPERIENCE = [
  "",
  "Internship",
  "Entry level",
  "Associate",
  "Mid-Senior level",
  "Director",
  "Executive",
];

export default function Discover() {
  const qc = useQueryClient();
  const [keyword, setKeyword] = useState("AI Engineer");
  const [location, setLocation] = useState("");
  const [timeRange, setTimeRange] = useState("Past week");
  const [jobType, setJobType] = useState("");
  const [experience, setExperience] = useState("");
  const [remote, setRemote] = useState("");
  const [limit, setLimit] = useState(25);
  const [summary, setSummary] = useState<DiscoverImportSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: ["discovery-searches"],
    queryFn: () => listDiscoverySearches({ limit: 10 }),
  });

  const search = useMutation({
    mutationFn: () =>
      discoverJobs({
        keyword,
        location,
        time_range: timeRange,
        job_type: jobType,
        experience_level: experience,
        remote,
        limit,
      }),
    onSuccess: (data) => {
      setSummary(data);
      setError(null);
      qc.invalidateQueries({ queryKey: ["jobs"] });
      qc.invalidateQueries({ queryKey: ["companies"] });
      qc.invalidateQueries({ queryKey: ["stats"] });
      qc.invalidateQueries({ queryKey: ["discovery-searches"] });
    },
    onError: (e: any) => {
      const detail = e?.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : "Search failed. Check Bright Data credentials or try stub mode."
      );
    },
  });

  return (
    <div>
      <PageHeader
        title="Discover Jobs"
        subtitle="Search LinkedIn jobs via Bright Data. Results are imported, scored, and classified automatically."
      />

      <Card className="mb-4 p-5">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-500">
              Keyword *
            </label>
            <input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder='e.g. "Machine Learning Engineer"'
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-500">
              Location
            </label>
            <input
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="San Francisco, CA or Remote"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-500">
              Time range
            </label>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            >
              {TIME_RANGES.map((t) => (
                <option key={t || "any"} value={t}>
                  {t || "Any time"}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-500">
              Max results
            </label>
            <input
              type="number"
              min={1}
              max={200}
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-500">
              Job type
            </label>
            <select
              value={jobType}
              onChange={(e) => setJobType(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            >
              {JOB_TYPES.map((t) => (
                <option key={t || "any"} value={t}>
                  {t || "Any"}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-500">
              Experience level
            </label>
            <select
              value={experience}
              onChange={(e) => setExperience(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            >
              {EXPERIENCE.map((t) => (
                <option key={t || "any"} value={t}>
                  {t || "Any"}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-500">
              Remote / on-site
            </label>
            <select
              value={remote}
              onChange={(e) => setRemote(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            >
              {REMOTE_OPTIONS.map((t) => (
                <option key={t || "any"} value={t}>
                  {t || "Any"}
                </option>
              ))}
            </select>
          </div>
        </div>

        <p className="mt-3 text-xs text-slate-400">
          Bright Data may take 30 seconds to a few minutes. Keep this page open
          while the search runs.
        </p>

        <div className="mt-4 flex justify-end">
          <Button
            onClick={() => search.mutate()}
            disabled={!keyword.trim() || search.isPending}
          >
            {search.isPending ? "Searching LinkedIn…" : "Search & import jobs"}
          </Button>
        </div>
      </Card>

      {error && (
        <Card className="mb-4 border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          {error}
        </Card>
      )}

      {summary && (
        <Card className="mb-4 p-5">
          <div className="mb-2 text-sm font-semibold text-slate-700">
            Search complete
          </div>
          <div className="flex flex-wrap gap-4 text-sm">
            <span>
              Fetched: <strong>{summary.records_fetched}</strong>
            </span>
            <span className="text-emerald-600">
              Imported: <strong>{summary.imported}</strong>
            </span>
            <span className="text-amber-600">
              Duplicates: <strong>{summary.duplicates}</strong>
            </span>
            {summary.errors > 0 && (
              <span className="text-rose-600">
                Errors: <strong>{summary.errors}</strong>
              </span>
            )}
          </div>
          {summary.snapshot_id && (
            <p className="mt-2 text-xs text-slate-400">
              Provider: {summary.provider} · Snapshot: {summary.snapshot_id}
            </p>
          )}
          <div className="mt-3">
            <Link to="/jobs" className="text-sm font-medium text-slate-900 underline">
              Review imported jobs →
            </Link>
          </div>
        </Card>
      )}

      <Card className="p-5">
        <div className="mb-3 text-sm font-semibold text-slate-700">
          Recent searches
        </div>
        {historyLoading ? (
          <Loading />
        ) : !history || history.items.length === 0 ? (
          <EmptyState message="No searches yet." />
        ) : (
          <ul className="divide-y divide-slate-100">
            {history.items.map((s) => (
              <li key={s.id} className="flex items-center justify-between py-2 text-sm">
                <div>
                  <span className="font-medium text-slate-800">{s.keyword}</span>
                  {s.location && (
                    <span className="text-slate-500"> · {s.location}</span>
                  )}
                  <div className="text-xs text-slate-400">
                    {s.records_imported ?? 0} imported · {s.created_at.slice(0, 16)}
                  </div>
                </div>
                <StatusBadge status={s.status} />
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
