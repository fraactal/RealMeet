import { Link } from "react-router-dom";

import type { NavigationItem } from "../../config/navigation";
import { isNavigationItemActive } from "../../config/navigation";
import type { User } from "../../types";
import { getRoleLabel } from "../../utils/labels";
import { Avatar, Button, Icon } from "../ui";

interface MobileNavigationProps {
  activePath: string;
  isOpen: boolean;
  items: NavigationItem[];
  onClose: () => void;
  onLogout: () => void;
  user: User;
}

export function MobileNavigation({ activePath, isOpen, items, onClose, onLogout, user }: MobileNavigationProps) {
  const fullName = `${user.first_name} ${user.last_name}`.trim() || user.email;

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label="Navegacion mobile">
      <button className="absolute inset-0 bg-ink-900/35" onClick={onClose} aria-label="Cerrar navegacion" />
      <aside className="relative flex h-full w-[min(22rem,calc(100vw-2rem))] flex-col bg-white p-4 shadow-lift">
        <div className="mb-5 flex items-center justify-between gap-3">
          <Link className="flex items-center gap-3 rounded-lg py-2" onClick={onClose} to="/dashboard">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-700 text-sm font-bold text-white">RM</span>
            <div>
              <p className="font-bold text-brand-700">RealMeet</p>
              <p className="text-xs text-ink-500">Agenda profesional</p>
            </div>
          </Link>
          <Button aria-label="Cerrar navegacion" onClick={onClose} size="sm" variant="secondary">
            <Icon name="x" />
          </Button>
        </div>

        <div className="mb-5 rounded-lg border border-brand-100 bg-brand-50 p-3">
          <div className="flex items-center gap-3">
            <Avatar name={fullName} />
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-ink-900">{fullName}</p>
              <p className="truncate text-xs text-brand-700">{getRoleLabel(user.role)}</p>
            </div>
          </div>
        </div>

        <nav aria-label="Navegacion mobile" className="flex flex-1 flex-col gap-1 overflow-y-auto">
          {items.map((item) => {
            const active = isNavigationItemActive(item, activePath);
            return (
              <Link
                aria-current={active ? "page" : undefined}
                className={
                  active
                    ? "flex items-center gap-3 rounded-lg bg-brand-700 px-3 py-3 text-sm font-semibold text-white shadow-sm"
                    : "flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-semibold text-ink-700 hover:bg-brand-50 hover:text-brand-700"
                }
                key={item.path}
                onClick={onClose}
                to={item.path}
              >
                <Icon name={item.icon} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-slate-200 pt-4">
          <Button className="w-full justify-start" onClick={onLogout} variant="ghost">
            <Icon name="logout" />
            Salir
          </Button>
        </div>
      </aside>
    </div>
  );
}
