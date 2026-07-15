import type { IconName } from "../ui";
import { Icon } from "../ui";

interface ClientStatSummaryProps {
  icon: IconName;
  label: string;
  value: number | string;
}

export function ClientStatSummary({ icon, label, value }: ClientStatSummaryProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-md bg-slate-100 text-ink-600">
          <Icon className="h-4 w-4" name={icon} />
        </span>
        <div>
          <p className="text-2xl font-semibold text-ink-900">{value}</p>
          <p className="text-sm text-ink-500">{label}</p>
        </div>
      </div>
    </div>
  );
}
