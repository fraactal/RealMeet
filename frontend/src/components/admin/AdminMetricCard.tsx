import type { IconName } from "../ui";
import { Icon } from "../ui";

interface AdminMetricCardProps {
  icon: IconName;
  label: string;
  value: number | string;
  description?: string;
}

export function AdminMetricCard({ description, icon, label, value }: AdminMetricCardProps) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-soft">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-ink-500">{label}</p>
          <p className="mt-2 text-3xl font-bold text-ink-900">{value}</p>
          {description ? <p className="mt-2 text-sm leading-6 text-ink-500">{description}</p> : null}
        </div>
        <span className="flex h-10 w-10 items-center justify-center rounded-md bg-brand-100 text-brand-700">
          <Icon className="h-5 w-5" name={icon} />
        </span>
      </div>
    </article>
  );
}
