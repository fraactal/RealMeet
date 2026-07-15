import { Badge } from "../ui";

interface AdminStatusPillProps {
  active: boolean;
  activeLabel?: string;
  inactiveLabel?: string;
}

export function AdminStatusPill({ active, activeLabel = "Activo", inactiveLabel = "Inactivo" }: AdminStatusPillProps) {
  return <Badge label={active ? activeLabel : inactiveLabel} tone={active ? "success" : "neutral"} />;
}
