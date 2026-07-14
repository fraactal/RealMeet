import { type PropsWithChildren, useEffect } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";

import { fetchMe } from "../api/queries";
import { useAuthStore } from "../store/auth";
import type { UserRole } from "../types";

interface RequireAuthProps {
  allowedRoles?: UserRole[];
}

export function RequireAuth({ allowedRoles, children }: PropsWithChildren<RequireAuthProps>) {
  const { token, user, isRestoring, setUser, setRestoring, logout } = useAuthStore();
  const location = useLocation();

  useEffect(() => {
    if (!token) {
      setRestoring(false);
      return;
    }
    if (user) {
      setRestoring(false);
      return;
    }
    let active = true;
    setRestoring(true);
    fetchMe()
      .then((currentUser) => {
        if (active) {
          setUser(currentUser);
        }
      })
      .catch(() => {
        if (active) {
          logout();
        }
      })
      .finally(() => {
        if (active) {
          setRestoring(false);
        }
      });

    return () => {
      active = false;
    };
  }, [logout, setRestoring, setUser, token, user]);

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (isRestoring || !user) {
    return <div className="mx-auto max-w-7xl px-6 py-8 text-sm text-slate-600">Validando sesion...</div>;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return children ?? <Outlet />;
}
