import type { AppointmentStatus } from "../../types";
import { getAppointmentStatusLabel } from "../../utils/labels";
import { Badge } from "./Badge";

const statusTone: Record<AppointmentStatus, "success" | "warning" | "danger" | "info" | "neutral"> = {
  pending: "warning",
  pending_payment: "warning",
  confirmed: "info",
  cancelled: "danger",
  completed: "success",
  no_show: "neutral",
};

interface StatusBadgeProps {
  status: AppointmentStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return <Badge label={getAppointmentStatusLabel(status)} tone={statusTone[status]} />;
}
