import type { ReactNode } from "react";

import { Card, Icon } from "../ui";
import type { IconName } from "../ui";

interface ProfessionalStatCardProps {
  label: string;
  value: number | string;
  description?: string;
  icon?: IconName;
}

export function ProfessionalStatCard({ description, icon = "chart", label, value }: ProfessionalStatCardProps) {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-ink-700">{label}</p>
          <p className="mt-3 text-3xl font-bold text-ink-900">{value}</p>
          {description ? <p className="mt-2 text-sm leading-5 text-ink-500">{description}</p> : null}
        </div>
        <span className="rounded-lg bg-brand-50 p-2 text-brand-700">
          <Icon name={icon} />
        </span>
      </div>
    </Card>
  );
}

interface ProfessionalConfigStatusProps {
  title: string;
  description: string;
  state: "ready" | "attention" | "neutral";
  action?: ReactNode;
}

const stateClasses = {
  ready: "border-success-100 bg-success-100/45 text-success-700",
  attention: "border-warning-100 bg-warning-100/60 text-warning-700",
  neutral: "border-info-100 bg-info-100/45 text-info-700",
};

export function ProfessionalConfigStatus({ action, description, state, title }: ProfessionalConfigStatusProps) {
  return (
    <div className={`rounded-lg border p-4 ${stateClasses[state]}`}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="font-semibold">{title}</p>
          <p className="mt-1 text-sm leading-5 opacity-90">{description}</p>
        </div>
        {action ? <div className="shrink-0">{action}</div> : null}
      </div>
    </div>
  );
}
