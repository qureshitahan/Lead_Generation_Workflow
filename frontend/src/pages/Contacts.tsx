import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listContacts, setContactApproval } from "../api/client";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  Loading,
  PageHeader,
  ScoreBar,
  Table,
  Td,
  Th,
} from "../components/ui";

const EMAIL_STATUS_TONE: Record<string, "green" | "amber" | "slate"> = {
  verified: "green",
  likely: "amber",
  guessed: "amber",
  unavailable: "slate",
};

function PhoneCell({
  phone,
  status,
}: {
  phone?: string | null;
  status?: string | null;
}) {
  if (phone) {
    return (
      <a href={`tel:${phone}`} className="text-blue-600 underline">
        {phone}
      </a>
    );
  }
  if (status === "pending") {
    return <Badge tone="amber">pending</Badge>;
  }
  if (status === "unavailable") {
    return <span className="text-xs text-slate-400">no phone on file</span>;
  }
  return <span className="text-slate-400">—</span>;
}

function EmailCell({ email, status }: { email?: string | null; status?: string | null }) {
  if (!email) {
    if (status === "unavailable") {
      return <span className="text-xs text-slate-400">no email on file</span>;
    }
    return <span className="text-slate-400">—</span>;
  }
  return (
    <div className="flex flex-col gap-1">
      <a href={`mailto:${email}`} className="text-blue-600 underline">
        {email}
      </a>
      {status && (
        <Badge tone={EMAIL_STATUS_TONE[status] ?? "slate"}>{status}</Badge>
      )}
    </div>
  );
}

export default function Contacts() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["contacts"],
    queryFn: () => listContacts(),
  });

  const approve = useMutation({
    mutationFn: ({ id, approved }: { id: number; approved: boolean }) =>
      setContactApproval(id, approved),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["contacts"] }),
  });

  return (
    <div>
      <PageHeader
        title="Contacts"
        subtitle="Discovered contacts ranked by usefulness. Approve a contact before any outreach."
      />
      <Card>
        {isLoading ? (
          <Loading />
        ) : !data || data.items.length === 0 ? (
          <EmptyState message="No contacts yet. Enrich a company to discover contacts." />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Name</Th>
                <Th>Title</Th>
                <Th>Email</Th>
                <Th>Phone</Th>
                <Th>Confidence</Th>
                <Th>Usefulness</Th>
                <Th>Approved</Th>
                <Th />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50">
                  <Td className="font-medium text-slate-900">{c.name}</Td>
                  <Td className="text-slate-600">{c.title ?? "—"}</Td>
                  <Td className="text-slate-500">
                    <EmailCell email={c.email} status={c.email_status} />
                  </Td>
                  <Td className="text-slate-500">
                    <PhoneCell phone={c.phone} status={c.phone_reveal_status} />
                  </Td>
                  <Td>
                    <ScoreBar value={c.confidence_score} />
                  </Td>
                  <Td>
                    <ScoreBar value={c.usefulness_score} />
                  </Td>
                  <Td>
                    {c.approved_for_outreach ? (
                      <Badge tone="green">Approved</Badge>
                    ) : (
                      <Badge tone="slate">Not approved</Badge>
                    )}
                  </Td>
                  <Td>
                    <Button
                      variant={c.approved_for_outreach ? "ghost" : "secondary"}
                      onClick={() =>
                        approve.mutate({
                          id: c.id,
                          approved: !c.approved_for_outreach,
                        })
                      }
                    >
                      {c.approved_for_outreach ? "Revoke" : "Approve"}
                    </Button>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </div>
  );
}
