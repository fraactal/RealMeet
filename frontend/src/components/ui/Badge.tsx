import { cn } from "../../utils/cn";

type BadgeTone = "neutral" | "brand" | "success" | "warning" | "danger" | "info";

const toneClasses: Record<BadgeTone, string> = {
  neutral: "bg-slate-100 text-slate-700",
  brand: "bg-brand-100 text-brand-700",
  success: "bg-success-100 text-success-700",
  warning: "bg-warning-100 text-warning-700",
  danger: "bg-danger-100 text-danger-700",
  info: "bg-info-100 text-info-700",
};

interface BadgeProps {
  label: string;
  tone?: BadgeTone;
  className?: string;
}

export function Badge({ label, tone = "brand", className }: BadgeProps) {
  return (
    <span className={cn("inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold", toneClasses[tone], className)}>
      {label}
    </span>
  );
}
