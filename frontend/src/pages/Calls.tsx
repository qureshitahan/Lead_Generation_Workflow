import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listCalls, setCallStatus } from "../api/client";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  Loading,
  PageHeader,
  StatusBadge,
} from "../components/ui";

export default function Calls() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["calls"],
    queryFn: () => listCalls({ limit: 100 }),
  });

  const status = useMutation({
    mutationFn: ({ id, s }: { id: number; s: string }) => setCallStatus(id, s),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["calls"] }),
  });

  return (
    <div>
      <PageHeader
        title="Call Queue"
        subtitle="Generated call scripts. Calls are never auto-placed — a human must approve each one."
      />
      {isLoading ? (
        <Loading />
      ) : !data || data.items.length === 0 ? (
        <Card>
          <EmptyState message="No calls queued. Generate one from a match." />
        </Card>
      ) : (
        <div className="space-y-3">
          {data.items.map((c) => (
            <Card key={c.id} className="p-5">
              <div className="mb-3 flex items-center justify-between">
                <div className="text-xs text-slate-400">
                  Job #{c.job_id} · Candidate #{c.candidate_id}
                  {c.contact_id ? ` · Contact #${c.contact_id}` : ""} ·{" "}
                  {c.phone_number ?? "no number"}
                </div>
                <div className="flex items-center gap-2">
                  {c.meeting_requested && <Badge tone="green">Meeting</Badge>}
                  {c.human_handoff_needed && <Badge tone="amber">Handoff</Badge>}
                  <StatusBadge status={c.status} />
                </div>
              </div>
              {c.script && (
                <pre className="whitespace-pre-wrap rounded-lg bg-slate-50 p-3 text-sm leading-relaxed text-slate-700">
                  {c.script}
                </pre>
              )}
              <div className="mt-3 flex justify-end gap-2">
                {c.status === "queued" && (
                  <Button onClick={() => status.mutate({ id: c.id, s: "approved" })}>
                    Approve call
                  </Button>
                )}
                {c.status === "approved" && (
                  <>
                    <Button
                      variant="secondary"
                      onClick={() => status.mutate({ id: c.id, s: "interested" })}
                    >
                      Mark interested
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={() => status.mutate({ id: c.id, s: "not_interested" })}
                    >
                      Not interested
                    </Button>
                  </>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
