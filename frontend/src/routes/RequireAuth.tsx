import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuthStore } from "../store/auth";

export function RequireAuth() {
  const { token } = useAuthStore();
  const location = useLocation();

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
