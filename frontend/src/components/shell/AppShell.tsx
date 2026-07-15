import { useEffect, useMemo, useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";

import { getActiveNavigationItem, getNavigationForRole } from "../../config/navigation";
import { useAuthStore } from "../../store/auth";
import { getRoleLabel } from "../../utils/labels";
import { AppHeader } from "./AppHeader";
import { MobileNavigation } from "./MobileNavigation";
import { Sidebar } from "./Sidebar";

export function AppShell() {
  const { user, logout } = useAuthStore();
  const location = useLocation();
  const navigate = useNavigate();
  const [isMobileNavigationOpen, setMobileNavigationOpen] = useState(false);

  const navigationItems = useMemo(() => (user ? getNavigationForRole(user.role) : []), [user]);
  const activeItem = user ? getActiveNavigationItem(user.role, location.pathname) : undefined;
  const pageTitle = activeItem?.label ?? "Panel";

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  useEffect(() => {
    setMobileNavigationOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!isMobileNavigationOpen) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setMobileNavigationOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isMobileNavigationOpen]);

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-surface-page text-ink-900">
      <Sidebar activePath={location.pathname} items={navigationItems} onLogout={handleLogout} user={user} />
      <MobileNavigation
        activePath={location.pathname}
        isOpen={isMobileNavigationOpen}
        items={navigationItems}
        onClose={() => setMobileNavigationOpen(false)}
        onLogout={handleLogout}
        user={user}
      />
      <div className="min-h-screen lg:pl-72">
        <AppHeader
          onLogout={handleLogout}
          onOpenMobileNavigation={() => setMobileNavigationOpen(true)}
          pageTitle={pageTitle}
          roleLabel={getRoleLabel(user.role)}
          user={user}
        />
        <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
