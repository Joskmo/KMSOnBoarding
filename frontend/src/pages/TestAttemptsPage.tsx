import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getTestAttempts } from '../api/assessment';
import { authApi } from '../api/client';
import { Pagination } from '../components/Pagination';
import { LoadingSpinner } from '../components/LoadingSpinner';
import type { AttemptListItem, User } from '../types';

export function TestAttemptsPage() {
  const { id } = useParams<{ id: string }>();
  const [attempts, setAttempts] = useState<AttemptListItem[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [size] = useState(20);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [attemptsRes, usersRes] = await Promise.all([
          getTestAttempts(id!, { page, size }),
          authApi.get('/users'),
        ]);
        setAttempts(attemptsRes.data.items);
        setTotal(attemptsRes.data.total);
        setUsers(usersRes.data || []);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Ошибка загрузки');
      } finally {
        setLoading(false);
      }
    };
    if (id) fetchData();
  }, [id, page, size]);

  const totalPages = Math.ceil(total / size);
  const userMap = new Map(users.map((u) => [u.id, u]));

  const userName = (userId: string) => {
    const u = userMap.get(userId);
    return u ? (u.full_name || u.email) : '—';
  };

  return (
    <div>
      <Link to="/tests" className="text-sm text-gray-500 hover:text-gray-700 mb-2 inline-block">
        ← К списку тестов
      </Link>
      <h1 className="text-2xl font-bold mb-6">Результаты по тесту</h1>

      {error && <div className="bg-red-50 text-red-700 p-3 rounded mb-4">{error}</div>}

      {loading ? <LoadingSpinner /> : (
        <>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Пользователь</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Результат</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Балл</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Дата завершения</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {attempts.map((a) => (
                  <tr key={a.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900 font-medium">{userName(a.user_id)}</td>
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
