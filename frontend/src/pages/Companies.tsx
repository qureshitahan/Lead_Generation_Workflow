import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { enrichCompany, listCompanies } from "../api/client";
import {
  Button,
  Card,
  EmployerBadge,
  EmptyState,
  Loading,
  PageHeader,
  StatusBadge,
  Table,
  Td,
  Th,
} from "../components/ui";

export default function Companies() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["companies"],
    queryFn: () => listCompanies(),
  });

  const enrich = useMutation({
    mutationFn: (id: number) => enrichCompany(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["companies"] });
      qc.invalidateQueries({ queryKey: ["contacts"] });
      qc.invalidateQueries({ queryKey: ["stats"] });
    },
  });

  return (
    <div>
      <PageHeader
        title="Companies"
        subtitle="Direct-employer classification and enrichment status. Enrich to discover contacts."
      />
      <Card>
        {isLoading ? (
          <Loading />
        ) : !data || data.items.length === 0 ? (
          <EmptyState message="No companies yet." />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Company</Th>
                <Th>Domain</Th>
                <Th>Industry</Th>
                <Th>Employees</Th>
                <Th>Phone</Th>
                <Th>Classification</Th>
                <Th>Enrichment</Th>
                <Th />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50">
                  <Td className="font-medium text-slate-900">
                    {c.name}
                    {c.linkedin_url && (
                      <a
                        href={c.linkedin_url}
                        target="_blank"
                        rel="noreferrer"
                        className="ml-2 text-xs text-blue-600 underline"
                      >
                        LinkedIn
                      </a>
                    )}
                  </Td>
                  <Td className="text-slate-500">{c.domain ?? "—"}</Td>
                  <Td className="text-slate-500">{c.industry ?? "—"}</Td>
                  <Td className="text-slate-500">{c.employee_count ?? "—"}</Td>
                  <Td className="text-slate-500">{c.phone ?? "—"}</Td>
                  <Td>
                    <EmployerBadge isDirect={c.is_direct_employer} />
                  </Td>
                  <Td>
                    <StatusBadge status={c.enrichment_status} />
                  </Td>
                  <Td>
                    <Button
                      variant="secondary"
                      onClick={() => enrich.mutate(c.id)}
                      disabled={enrich.isPending}
                    >
                      Enrich
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
