import type { PropsWithChildren, ReactNode } from "react";

interface PageHeaderProps extends PropsWithChildren {
  title: string;
  description?: string;
  actions?: ReactNode;
}

export function PageHeader({ actions, children, description, title }: PageHeaderProps) {
  return (
    <header className="mb-6 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
      <div className="max-w-3xl">
        <h1 className="text-2xl font-bold text-ink-900 md:text-3xl">{title}</h1>
        {description ? <p className="mt-2 text-sm leading-6 text-ink-500">{description}</p> : null}
        {children}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap gap-2">{actions}</div> : null}
    </header>
  );
}
