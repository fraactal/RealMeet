import { Link } from "react-router-dom";

import type { NavigationItem } from "../../config/navigation";
import { isNavigationItemActive } from "../../config/navigation";
import type { User } from "../../types";
import { getRoleLabel } from "../../utils/labels";
import { Avatar, Button, Icon } from "../ui";

interface SidebarProps {
  activePath: string;
  items: NavigationItem[];
  onLogout: () => void;
  user: User;
}

export function Sidebar({ activePath, items, onLogout, user }: SidebarProps) {
  const fullName = `${user.first_name} ${user.last_name}`.trim() || user.email;

  return (
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-72 border-r border-slate-200/80 bg-white/95 px-4 py-5 shadow-soft lg:flex lg:flex-col">
      <Link className="mb-6 flex items-center gap-3 rounded-lg px-2 py-2 focus-visible:outline-brand-500" to="/dashboard">
        <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-700 text-sm font-bold text-white">RM</span>
        <div>
          <p className="text-lg font-bold text-brand-700">RealMeet</p>
          <p className="text-xs font-medium text-ink-500">Agenda profesional</p>
        </div>
      </Link>

      <div className="mb-6 rounded-lg border border-brand-100 bg-brand-50 p-3">
        <div className="flex items-center gap-3">
          <Avatar name={fullName} />
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-ink-900">{fullName}</p>
            <p className="truncate text-xs text-brand-700">{getRoleLabel(user.role)}</p>
          </div>
        </div>
        <p className="mt-2 truncate text-xs text-ink-500">{user.email}</p>
      </div>

      <nav aria-label="Navegacion principal" className="flex flex-1 flex-col gap-1">
        {items.map((item) => (
          <SidebarNavItem active={isNavigationItemActive(item, activePath)} item={item} key={item.path} />
        ))}
      </nav>

      <div className="border-t border-slate-200 pt-4">
        <Button className="w-full justify-start" onClick={onLogout} variant="ghost">
          <Icon name="logout" />
          Salir
        </Button>
      </div>
    </aside>
  );
}

function SidebarNavItem({ active, item }: { active: boolean; item: NavigationItem }) {
  return (
    <Link
      aria-current={active ? "page" : undefined}
      className={
        active
          ? "flex items-center gap-3 rounded-lg bg-brand-700 px-3 py-3 text-sm font-semibold text-white shadow-sm"
          : "flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-semibold text-ink-700 transition hover:bg-brand-50 hover:text-brand-700"
      }
      to={item.path}
    >
      <Icon className="shrink-0" name={item.icon} />
      <span>{item.label}</span>
    </Link>
  );
}
