import { createBrowserRouter } from "react-router-dom";

import { DashboardLayout } from "../layouts/DashboardLayout";
import { PublicLayout } from "../layouts/PublicLayout";
import { AdminCatalogPage } from "../pages/AdminCatalogPage";
import { AdminManagementPage } from "../pages/AdminManagementPage";
import { AdminMetricsPage } from "../pages/AdminMetricsPage";
import { AppointmentsPage } from "../pages/AppointmentsPage";
import { DashboardHomePage } from "../pages/DashboardHomePage";
import { HomePage } from "../pages/HomePage";
import { LoginPage } from "../pages/LoginPage";
import { MockMeetingPage } from "../pages/MockMeetingPage";
import { ProfessionalAvailabilityPage } from "../pages/ProfessionalAvailabilityPage";
import { ProfessionalAppointmentsPage } from "../pages/ProfessionalAppointmentsPage";
import { ProfessionalCatalogPage } from "../pages/ProfessionalCatalogPage";
import { ProfessionalMetricsPage } from "../pages/ProfessionalMetricsPage";
import { ProfessionalsPage } from "../pages/ProfessionalsPage";
import { RequireAuth } from "./RequireAuth";

export const router = createBrowserRouter([
  {
    element: <PublicLayout />,
    children: [
      { path: "/", element: <HomePage /> },
      { path: "/professionals", element: <ProfessionalsPage /> },
      { path: "/mock-meeting/:meetingId", element: <MockMeetingPage /> },
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
            path: "professional/appointments",
            element: (
              <RequireAuth allowedRoles={["professional"]}>
                <ProfessionalAppointmentsPage />
              </RequireAuth>
            ),
          },
          {
            path: "professional/catalog",
            element: (
              <RequireAuth allowedRoles={["professional"]}>
                <ProfessionalCatalogPage />
              </RequireAuth>
            ),
          },
          {
            path: "professional/availability",
            element: (
              <RequireAuth allowedRoles={["professional"]}>
                <ProfessionalAvailabilityPage />
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
          {
            path: "admin/manage",
            element: (
              <RequireAuth allowedRoles={["admin"]}>
                <AdminManagementPage />
              </RequireAuth>
            ),
          },
          {
            path: "admin/catalog",
            element: (
              <RequireAuth allowedRoles={["admin"]}>
                <AdminCatalogPage />
              </RequireAuth>
            ),
          },
        ],
      },
    ],
  },
]);
