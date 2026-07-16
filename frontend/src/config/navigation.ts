import type { IconName } from "../components/ui";
import type { UserRole } from "../types";

export interface NavigationItem {
  label: string;
  path: string;
  icon: IconName;
  roles: UserRole[];
  matchPaths?: string[];
  description?: string;
}

export const authenticatedNavigation: NavigationItem[] = [
  {
    label: "Inicio",
    path: "/dashboard",
    icon: "dashboard",
    roles: ["admin", "professional", "client"],
    matchPaths: ["/dashboard"],
    description: "Resumen principal",
  },
  {
    label: "Buscar profesionales",
    path: "/dashboard/professionals",
    icon: "search",
    roles: ["client"],
    matchPaths: ["/dashboard/professionals"],
    description: "Catalogo publico",
  },
  {
    label: "Mis reservas",
    path: "/dashboard/appointments",
    icon: "calendar",
    roles: ["client"],
    matchPaths: ["/dashboard/appointments"],
    description: "Reservas y atenciones",
  },
  {
    label: "Mis pagos",
    path: "/dashboard/payments",
    icon: "payment",
    roles: ["client"],
    matchPaths: ["/dashboard/payments"],
    description: "Ordenes de cobro",
  },
  {
    label: "Metricas",
    path: "/dashboard/professional",
    icon: "chart",
    roles: ["professional"],
    matchPaths: ["/dashboard/professional"],
    description: "Indicadores profesionales",
  },
  {
    label: "Reservas",
    path: "/dashboard/professional/appointments",
    icon: "calendar",
    roles: ["professional"],
    matchPaths: ["/dashboard/professional/appointments"],
    description: "Agenda y solicitudes",
  },
  {
    label: "Pagos",
    path: "/dashboard/professional/payments",
    icon: "payment",
    roles: ["professional"],
    matchPaths: ["/dashboard/professional/payments"],
    description: "Cobros vinculados",
  },
  {
    label: "Perfil publico",
    path: "/dashboard/professional/catalog",
    icon: "user",
    roles: ["professional"],
    matchPaths: ["/dashboard/professional/catalog"],
    description: "Publicacion y especialidades",
  },
  {
    label: "Disponibilidad",
    path: "/dashboard/professional/availability",
    icon: "clock",
    roles: ["professional"],
    matchPaths: ["/dashboard/professional/availability"],
    description: "Horarios y bloqueos",
  },
  {
    label: "Metricas admin",
    path: "/dashboard/admin",
    icon: "chart",
    roles: ["admin"],
    matchPaths: ["/dashboard/admin"],
    description: "Operacion global",
  },
  {
    label: "Backoffice",
    path: "/dashboard/admin/manage",
    icon: "users",
    roles: ["admin"],
    matchPaths: ["/dashboard/admin/manage"],
    description: "Usuarios, profesionales y reservas",
  },
  {
    label: "Catalogo",
    path: "/dashboard/admin/catalog",
    icon: "settings",
    roles: ["admin"],
    matchPaths: ["/dashboard/admin/catalog"],
    description: "Categorias y especialidades",
  },
  {
    label: "Integraciones",
    path: "/dashboard/admin/integrations",
    icon: "settings",
    roles: ["admin"],
    matchPaths: ["/dashboard/admin/integrations"],
    description: "Proveedores externos",
  },
  {
    label: "Pagos",
    path: "/dashboard/admin/payments",
    icon: "payment",
    roles: ["admin"],
    matchPaths: ["/dashboard/admin/payments"],
    description: "Ordenes y provider fake",
  },
];

export function getNavigationForRole(role: UserRole): NavigationItem[] {
  return authenticatedNavigation.filter((item) => item.roles.includes(role));
}

export function isNavigationItemActive(item: NavigationItem, pathname: string): boolean {
  const matchPaths = item.matchPaths ?? [item.path];
  return matchPaths.some((matchPath) => {
    if (matchPath === "/dashboard" || matchPath === "/dashboard/professional" || matchPath === "/dashboard/admin") {
      return pathname === matchPath;
    }

    return pathname === matchPath || pathname.startsWith(`${matchPath}/`);
  });
}

export function getActiveNavigationItem(role: UserRole, pathname: string): NavigationItem | undefined {
  const items = getNavigationForRole(role);
  return [...items].sort((a, b) => b.path.length - a.path.length).find((item) => isNavigationItemActive(item, pathname));
}
