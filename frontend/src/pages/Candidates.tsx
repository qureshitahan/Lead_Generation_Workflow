import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createCandidate, listCandidates } from "../api/client";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  Loading,
  PageHeader,
} from "../components/ui";

export default function Candidates() {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [resume, setResume] = useState("");
  const [showForm, setShowForm] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["candidates"],
    queryFn: () => listCandidates(),
  });

  const create = useMutation({
    mutationFn: () => createCandidate({ name, resume_text: resume }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["candidates"] });
      qc.invalidateQueries({ queryKey: ["stats"] });
      setName("");
      setResume("");
      setShowForm(false);
    },
  });

  return (
    <div>
      <PageHeader
        title="Candidates"
        subtitle="Paste a resume and the profile is parsed automatically (skills, roles, experience)."
        actions={
          <Button onClick={() => setShowForm((s) => !s)}>
            {showForm ? "Close" : "Add candidate"}
          </Button>
        }
      />

      {showForm && (
        <Card className="mb-4 p-5">
          <div className="space-y-3">
            <input
              placeholder="Candidate name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <textarea
              placeholder="Paste resume text here. Skills, target roles, and years of experience will be parsed automatically."
              value={resume}
              onChange={(e) => setResume(e.target.value)}
              rows={8}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <div className="flex justify-end">
              <Button
                onClick={() => create.mutate()}
                disabled={!name || create.isPending}
              >
                {create.isPending ? "Saving…" : "Save candidate"}
              </Button>
            </div>
          </div>
        </Card>
      )}

      {isLoading ? (
        <Loading />
      ) : !data || data.items.length === 0 ? (
        <Card>
          <EmptyState message="No candidates yet. Add one to start matching." />
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {data.items.map((c) => (
            <Card key={c.id} className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-lg font-semibold text-slate-900">
                    {c.name}
                  </div>
                  {c.summary && (
                    <p className="mt-1 text-sm text-slate-500">{c.summary}</p>
                  )}
                </div>
                {c.years_experience != null && (
                  <Badge tone="blue">{c.years_experience} yrs</Badge>
                )}
              </div>
              {c.target_roles && c.target_roles.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1">
                  {c.target_roles.map((r) => (
                    <Badge key={r} tone="purple">
                      {r}
                    </Badge>
                  ))}
                </div>
              )}
              {c.skills && c.skills.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {c.skills.slice(0, 12).map((s) => (
                    <Badge key={s} tone="slate">
                      {s}
                    </Badge>
                  ))}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
