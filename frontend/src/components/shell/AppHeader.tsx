import type { User } from "../../types";
import { Avatar, Button, Icon } from "../ui";

interface AppHeaderProps {
  onLogout: () => void;
  onOpenMobileNavigation: () => void;
  pageTitle: string;
  roleLabel: string;
  user: User;
}

export function AppHeader({ onLogout, onOpenMobileNavigation, pageTitle, roleLabel, user }: AppHeaderProps) {
  const fullName = `${user.first_name} ${user.last_name}`.trim() || user.email;

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 backdrop-blur">
      <div className="flex min-h-16 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <Button
            aria-label="Abrir navegacion"
            className="lg:hidden"
            onClick={onOpenMobileNavigation}
            size="sm"
            variant="secondary"
          >
            <Icon name="menu" />
          </Button>
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase text-brand-700">RealMeet</p>
            <h1 className="truncate text-xl font-bold text-ink-900">{pageTitle}</h1>
          </div>
        </div>
        <div className="flex min-w-0 items-center gap-3">
          <div className="hidden min-w-0 text-right sm:block">
            <p className="truncate text-sm font-semibold text-ink-900">{fullName}</p>
            <p className="truncate text-xs text-ink-500">{roleLabel}</p>
          </div>
          <Avatar name={fullName} />
          <Button className="hidden md:inline-flex" onClick={onLogout} size="sm" variant="ghost">
            <Icon name="logout" />
            Salir
          </Button>
        </div>
      </div>
    </header>
  );
}
