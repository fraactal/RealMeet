import type { PropsWithChildren } from "react";

interface CardProps extends PropsWithChildren {
  title?: string;
}

export function Card({ title, children }: CardProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white/90 p-6 shadow-sm backdrop-blur">
      {title ? <h3 className="mb-4 text-lg font-semibold text-ink">{title}</h3> : null}
      {children}
    </section>
  );
}
