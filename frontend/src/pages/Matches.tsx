import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { generateCall, generateEmail, listMatches } from "../api/client";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  Loading,
  PageHeader,
  ScoreBar,
} from "../components/ui";

export default function Matches() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["matches", {}],
    queryFn: () => listMatches({ limit: 100 }),
  });

  const email = useMutation({
    mutationFn: (m: { job_id: number; candidate_id: number; match_id: number }) =>
      generateEmail(m),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["emails"] }),
  });
  const call = useMutation({
    mutationFn: (m: { job_id: number; candidate_id: number; match_id: number }) =>
      generateCall(m),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["calls"] }),
  });

  return (
    <div>
      <PageHeader
        title="Matches"
        subtitle="Candidate-to-job matches with pitch summaries. Generate an email draft or call script from a match."
      />
      {isLoading ? (
        <Loading />
      ) : !data || data.items.length === 0 ? (
        <Card>
          <EmptyState message="No matches yet. Open a job and click 'Match candidates'." />
        </Card>
      ) : (
        <div className="space-y-3">
          {data.items.map((m) => (
            <Card key={m.id} className="p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-semibold text-slate-900">
                      Job #{m.job_id}
                    </span>
                    <span className="text-slate-300">·</span>
                    <span className="text-sm text-slate-600">
                      Candidate #{m.candidate_id}
                    </span>
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
                    {(m.concerns ?? []).map((s) => (
                      <Badge key={s} tone="amber">
                        {s}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <ScoreBar value={m.score} />
                  <div className="flex gap-1">
                    <Button
                      variant="secondary"
                      onClick={() =>
                        email.mutate({
                          job_id: m.job_id,
                          candidate_id: m.candidate_id,
                          match_id: m.id,
                        })
                      }
                    >
                      Draft email
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={() =>
                        call.mutate({
                          job_id: m.job_id,
                          candidate_id: m.candidate_id,
                          match_id: m.id,
                        })
                      }
                    >
                      Queue call
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
