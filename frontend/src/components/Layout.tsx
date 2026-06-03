import { NavLink, Outlet } from "react-router-dom";

const NAV = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/discover", label: "Discover Jobs" },
  { to: "/jobs", label: "Jobs" },
  { to: "/companies", label: "Companies" },
  { to: "/contacts", label: "Contacts" },
  { to: "/candidates", label: "Candidates" },
  { to: "/matches", label: "Matches" },
  { to: "/emails", label: "Email Drafts" },
  { to: "/calls", label: "Call Queue" },
  { to: "/import", label: "Import Jobs" },
];

export default function Layout() {
  return (
    <div className="flex min-h-screen">
      <aside className="flex w-60 flex-shrink-0 flex-col border-r border-slate-200 bg-white">
        <div className="px-5 py-5">
          <div className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Lead Gen
          </div>
          <div className="text-lg font-bold text-slate-900">Outreach Console</div>
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `block rounded-lg px-3 py-2 text-sm font-medium transition ${
                  isActive
                    ? "bg-slate-900 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-5 py-4 text-xs text-slate-400">
          MVP · human-in-the-loop
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-7xl px-8 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
