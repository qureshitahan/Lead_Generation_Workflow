import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { importFile, importPaste } from "../api/client";
import type { ImportSummary } from "../types";
import { Button, Card, PageHeader } from "../components/ui";

const SOURCES = [
  { value: "brightdata", label: "Bright Data" },
  { value: "apify", label: "Apify" },
  { value: "manual", label: "Manual (canonical columns)" },
];

export default function ImportPage() {
  const qc = useQueryClient();
  const [source, setSource] = useState("brightdata");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [summary, setSummary] = useState<ImportSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["jobs"] });
    qc.invalidateQueries({ queryKey: ["companies"] });
    qc.invalidateQueries({ queryKey: ["stats"] });
  };

  const paste = useMutation({
    mutationFn: () => importPaste(source, text),
    onSuccess: (data) => {
      setSummary(data);
      setError(null);
      invalidate();
    },
    onError: (e: any) => setError(e?.response?.data?.detail ?? "Import failed"),
  });

  const upload = useMutation({
    mutationFn: () => importFile(source, file as File),
    onSuccess: (data) => {
      setSummary(data);
      setError(null);
      invalidate();
    },
    onError: (e: any) => setError(e?.response?.data?.detail ?? "Import failed"),
  });

  return (
    <div>
      <PageHeader
        title="Import Jobs"
        subtitle="Upload a CSV/JSON export or paste raw text. Records are stored raw, normalized, deduplicated, and classified."
      />

      <Card className="mb-4 p-5">
        <label className="mb-2 block text-sm font-medium text-slate-700">
          Source
        </label>
        <select
          value={source}
          onChange={(e) => setSource(e.target.value)}
          className="mb-4 rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          {SOURCES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">
              Upload file
            </label>
            <input
              type="file"
              accept=".json,.csv"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="block w-full text-sm text-slate-500 file:mr-3 file:rounded-lg file:border-0 file:bg-slate-900 file:px-3 file:py-2 file:text-sm file:font-medium file:text-white"
            />
            <div className="mt-3">
              <Button
                onClick={() => upload.mutate()}
                disabled={!file || upload.isPending}
              >
                {upload.isPending ? "Importing…" : "Import file"}
              </Button>
            </div>
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">
              Or paste CSV / JSON
            </label>
            <textarea
              rows={6}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder='[{"job_title": "...", "company_name": "..."}]'
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <div className="mt-3">
              <Button
                onClick={() => paste.mutate()}
                disabled={!text || paste.isPending}
              >
                {paste.isPending ? "Importing…" : "Import pasted text"}
              </Button>
            </div>
          </div>
        </div>
      </Card>

      {error && (
        <Card className="mb-4 border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          {error}
        </Card>
      )}

      {summary && (
        <Card className="p-5">
          <div className="mb-2 text-sm font-semibold text-slate-700">
            Import complete (batch {summary.batch_id})
          </div>
          <div className="flex flex-wrap gap-6 text-sm">
            <div>
              <span className="text-slate-400">Total: </span>
              {summary.total_records}
            </div>
            <div className="font-medium text-emerald-600">
              Imported: {summary.imported}
            </div>
            <div className="text-amber-600">Duplicates: {summary.duplicates}</div>
            <div className="text-rose-600">Errors: {summary.errors}</div>
          </div>
          {summary.error_messages.length > 0 && (
            <ul className="mt-3 list-inside list-disc text-xs text-rose-600">
              {summary.error_messages.map((m, i) => (
                <li key={i}>{m}</li>
              ))}
            </ul>
          )}
        </Card>
      )}
    </div>
  );
}
