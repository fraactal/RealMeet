import { createBrowserRouter } from "react-router-dom";

import { DashboardLayout } from "../layouts/DashboardLayout";
import { PublicLayout } from "../layouts/PublicLayout";
import { AdminMetricsPage } from "../pages/AdminMetricsPage";
import { AppointmentsPage } from "../pages/AppointmentsPage";
import { DashboardHomePage } from "../pages/DashboardHomePage";
import { HomePage } from "../pages/HomePage";
import { LoginPage } from "../pages/LoginPage";
import { ProfessionalMetricsPage } from "../pages/ProfessionalMetricsPage";
import { ProfessionalsPage } from "../pages/ProfessionalsPage";
import { RequireAuth } from "./RequireAuth";

export const router = createBrowserRouter([
  {
    element: <PublicLayout />,
    children: [
      { path: "/", element: <HomePage /> },
      { path: "/professionals", element: <ProfessionalsPage /> },
      { path: "/login", element: <LoginPage /> },
    ],
  },
  {
    element: <RequireAuth />,
    children: [
      {
        path: "/dashboard",
        element: <DashboardLayout />,
        children: [
          { index: true, element: <DashboardHomePage /> },
          { path: "appointments", element: <AppointmentsPage /> },
          {
            path: "professional",
            element: (
              <RequireAuth allowedRoles={["professional"]}>
                <ProfessionalMetricsPage />
              </RequireAuth>
            ),
          },
          {
            path: "admin",
            element: (
              <RequireAuth allowedRoles={["admin"]}>
                <AdminMetricsPage />
              </RequireAuth>
            ),
          },
        ],
      },
    ],
  },
]);
