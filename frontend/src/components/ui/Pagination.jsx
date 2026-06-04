/**
 * Pagination controls.
 */
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export default function Pagination({ page, pages, total, perPage, onPageChange }) {
  const { t } = useTranslation();
  if (pages <= 1) return null;

  return (
    <div className="flex items-center justify-between mt-4 text-sm text-text-muted">
      <span>
        {t('common.page')} {page} / {pages} &nbsp;·&nbsp; {total} items
      </span>
      <div className="flex gap-1">
        <button
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          className="p-1.5 rounded hover:bg-border disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        {Array.from({ length: Math.min(pages, 7) }, (_, i) => {
          const p = i + 1;
          return (
            <button
              key={p}
              onClick={() => onPageChange(p)}
              className={`w-8 h-8 rounded text-xs font-medium transition-colors ${
                p === page ? 'bg-primary text-white' : 'hover:bg-border'
              }`}
            >
              {p}
            </button>
          );
        })}
        <button
          disabled={page >= pages}
          onClick={() => onPageChange(page + 1)}
          className="p-1.5 rounded hover:bg-border disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
