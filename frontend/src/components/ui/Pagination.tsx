import { clsx } from 'clsx'

interface PaginationProps {
  page: number
  pages: number
  onPageChange: (page: number) => void
}

export function Pagination({ page, pages, onPageChange }: PaginationProps) {
  if (pages <= 1) return null

  return (
    <div className="flex items-center justify-center gap-2 py-4">
      <button
        className="rounded-md px-3 py-1 text-sm disabled:opacity-40"
        disabled={page <= 1}
        onClick={() => onPageChange(page - 1)}
      >
        Anterior
      </button>
      <span className="text-sm text-slate-600">
        Página {page} de {pages}
      </span>
      <button
        className={clsx('rounded-md px-3 py-1 text-sm', page >= pages && 'opacity-40')}
        disabled={page >= pages}
        onClick={() => onPageChange(page + 1)}
      >
        Siguiente
      </button>
    </div>
  )
}
