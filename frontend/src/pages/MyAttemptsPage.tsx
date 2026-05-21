import { useState, useEffect } from 'react';
import { getMyAttempts } from '../api/assessment';
import { Pagination } from '../components/Pagination';
import { LoadingSpinner } from '../components/LoadingSpinner';
import type { AttemptListItem } from '../types';

export function MyAttemptsPage() {
  const [attempts, setAttempts] = useState<AttemptListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [size] = useState(20);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchAttempts();
  }, [page]);

  const fetchAttempts = async () => {
    setLoading(true);
    try {
      const res = await getMyAttempts({ page, size });
      setAttempts(res.data.items);
      setTotal(res.data.total);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка загрузки');
    } finally {
      setLoading(false);
    }
  };

  const totalPages = Math.ceil(total / size);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Мои попытки</h1>
      {error && <div className="bg-red-50 text-red-700 p-3 rounded mb-4">{error}</div>}

      {loading ? <LoadingSpinner /> : (
        <>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Тест (ID)</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Результат</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Балл</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Дата</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {attempts.map((a) => (
                  <tr key={a.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900">{a.test_id}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-xs ${a.is_passed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {a.is_passed ? 'Пройден' : 'Не пройден'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">{a.score}%</td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {new Date(a.finished_at).toLocaleString('ru-RU')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}