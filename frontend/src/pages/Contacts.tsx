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
                  <Td className="text-slate-500">{c.email ?? "—"}</Td>
                  <Td className="text-slate-500">{c.phone ?? "—"}</Td>
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
