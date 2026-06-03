import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listEmails, setEmailStatus, updateEmail } from "../api/client";
import type { EmailDraft } from "../types";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  Loading,
  PageHeader,
  StatusBadge,
} from "../components/ui";

function DraftCard({ draft }: { draft: EmailDraft }) {
  const qc = useQueryClient();
  const [subject, setSubject] = useState(draft.subject);
  const [body, setBody] = useState(draft.body);
  const dirty = subject !== draft.subject || body !== draft.body;

  const save = useMutation({
    mutationFn: () => updateEmail(draft.id, { subject, body }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["emails"] }),
  });
  const status = useMutation({
    mutationFn: (s: string) => setEmailStatus(draft.id, s),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["emails"] }),
  });

  const locked = draft.status === "sent";

  return (
    <Card className="p-5">
      <div className="mb-3 flex items-center justify-between">
        <div className="text-xs text-slate-400">
          Job #{draft.job_id} · Candidate #{draft.candidate_id}
          {draft.contact_id ? ` · Contact #${draft.contact_id}` : ""}
        </div>
        <StatusBadge status={draft.status} />
      </div>
      <input
        value={subject}
        disabled={locked}
        onChange={(e) => setSubject(e.target.value)}
        className="mb-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium"
      />
      <textarea
        value={body}
        disabled={locked}
        onChange={(e) => setBody(e.target.value)}
        rows={9}
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm leading-relaxed"
      />
      <div className="mt-3 flex flex-wrap justify-end gap-2">
        {dirty && !locked && (
          <Button variant="secondary" onClick={() => save.mutate()}>
            Save edits
          </Button>
        )}
        {draft.status === "draft" && (
          <Button onClick={() => status.mutate("approved")}>Approve</Button>
        )}
        {draft.status === "approved" && (
          <>
            <Button variant="ghost" onClick={() => status.mutate("draft")}>
              Unapprove
            </Button>
            <Badge>Ready to send (sending is gated)</Badge>
          </>
        )}
        {(draft.status === "sent" || draft.status === "approved") && (
          <Button variant="ghost" onClick={() => status.mutate("replied")}>
            Mark replied
          </Button>
        )}
      </div>
    </Card>
  );
}

export default function Emails() {
  const { data, isLoading } = useQuery({
    queryKey: ["emails"],
    queryFn: () => listEmails({ limit: 100 }),
  });

  return (
    <div>
      <PageHeader
        title="Email Drafts"
        subtitle="Review and edit drafts. Nothing is sent automatically — approval is required, and the default provider does not transmit."
      />
      {isLoading ? (
        <Loading />
      ) : !data || data.items.length === 0 ? (
        <Card>
          <EmptyState message="No email drafts yet. Generate one from a match." />
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {data.items.map((d) => (
            <DraftCard key={d.id} draft={d} />
          ))}
        </div>
      )}
    </div>
  );
}
