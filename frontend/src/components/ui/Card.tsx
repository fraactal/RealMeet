import type { PropsWithChildren } from "react";

import { cn } from "../../utils/cn";

interface CardProps extends PropsWithChildren {
  title?: string;
  className?: string;
}

export function Card({ title, children, className }: CardProps) {
  return (
    <section className={cn("rounded-lg border border-slate-200/80 bg-white p-6 shadow-soft", className)}>
      {title ? <h3 className="mb-4 text-lg font-semibold text-ink-900">{title}</h3> : null}
      {children}
    </section>
  );
}
