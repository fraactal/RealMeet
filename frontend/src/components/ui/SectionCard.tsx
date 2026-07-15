import type { PropsWithChildren, ReactNode } from "react";

import { cn } from "../../utils/cn";

interface SectionCardProps extends PropsWithChildren {
  title?: string;
  description?: string;
  actions?: ReactNode;
  className?: string;
}

export function SectionCard({ actions, children, className, description, title }: SectionCardProps) {
  return (
    <section className={cn("rounded-lg border border-slate-200/80 bg-white p-5 shadow-soft", className)}>
      {title || description || actions ? (
        <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            {title ? <h2 className="text-lg font-semibold text-ink-900">{title}</h2> : null}
            {description ? <p className="mt-1 text-sm leading-6 text-ink-500">{description}</p> : null}
          </div>
          {actions ? <div className="flex shrink-0 flex-wrap gap-2">{actions}</div> : null}
        </div>
      ) : null}
      {children}
    </section>
  );
}
