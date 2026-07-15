import type { PropsWithChildren } from "react";

import { Button } from "./Button";

interface EmptyStateProps extends PropsWithChildren {
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({ actionLabel, children, description, onAction, title }: EmptyStateProps) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-white/70 p-8 text-center">
      <h3 className="text-base font-semibold text-ink-900">{title}</h3>
      {description ? <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-ink-500">{description}</p> : null}
      {children}
      {actionLabel && onAction ? (
        <Button className="mt-5" onClick={onAction}>
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}

export function LoadingState({ label = "Cargando informacion" }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-4 text-sm font-medium text-ink-700 shadow-sm">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-brand-700 border-t-transparent" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

export function ErrorState({ message = "No pudimos cargar la informacion.", title = "Algo no salio como esperabamos" }: { title?: string; message?: string }) {
  return (
    <div className="rounded-lg border border-danger-100 bg-danger-100/70 p-4 text-sm text-danger-700" role="alert">
      <p className="font-semibold">{title}</p>
      <p className="mt-1">{message}</p>
    </div>
  );
}
