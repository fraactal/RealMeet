import type { PageMeta } from "../../types";
import { Button } from "../ui";

interface AdminPaginationProps {
  meta?: PageMeta;
  onPageChange: (page: number) => void;
}

export function AdminPagination({ meta, onPageChange }: AdminPaginationProps) {
  if (!meta || meta.total_pages <= 1) {
    return null;
  }

  return (
    <div className="flex flex-col items-stretch justify-between gap-3 border-t border-slate-100 pt-4 sm:flex-row sm:items-center">
      <p className="text-sm text-ink-500">
        Pagina {meta.page} de {meta.total_pages} · {meta.total} registros
      </p>
      <div className="flex gap-2">
        <Button disabled={meta.page <= 1} onClick={() => onPageChange(Math.max(meta.page - 1, 1))} size="sm" variant="secondary">
          Anterior
        </Button>
        <Button disabled={meta.page >= meta.total_pages} onClick={() => onPageChange(meta.page + 1)} size="sm" variant="secondary">
          Siguiente
        </Button>
      </div>
    </div>
  );
}
