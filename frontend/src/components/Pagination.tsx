interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  return (
    <div className="flex justify-center gap-2 mt-6">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page === 1}
        className="px-3 py-1 border rounded disabled:opacity-50 hover:bg-gray-50"
      >
        ← Назад
      </button>
      <span className="px-3 py-1">
        Страница {page} из {totalPages}
      </span>
      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page === totalPages}
        className="px-3 py-1 border rounded disabled:opacity-50 hover:bg-gray-50"
      >
        Вперед →
      </button>
    </div>
  );
}
