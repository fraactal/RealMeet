interface BadgeProps {
  label: string;
}

export function Badge({ label }: BadgeProps) {
  return <span className="rounded-full bg-mist px-3 py-1 text-xs font-semibold uppercase tracking-wide text-brand">{label}</span>;
}
