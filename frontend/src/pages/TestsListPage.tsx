import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { contentApi } from '../api/client';
import { getTests, deleteTest } from '../api/assessment';
import { Pagination } from '../components/Pagination';
import { LoadingSpinner } from '../components/LoadingSpinner';
import type { Test, Module } from '../types';

export function TestsListPage() {
  const { hasRole } = useAuth();
  const navigate = useNavigate();
  const [tests, setTests] = useState<Test[]>([]);
  const [modules, setModules] = useState<Module[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [size] = useState(20);
  const [moduleFilter, setModuleFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const isManager = hasRole(['admin', 'methodist']);
  const isTestTaker = hasRole(['seminarist', 'candidate']);

  useEffect(() => {
    if (isManager) {
      fetchModules();
    }
    fetchTests();
  }, [page, moduleFilter, isManager]);

  const fetchModules = async () => {
    try {
      const res = await contentApi.get('/modules?page=1&size=100');
      setModules(res.data.items || []);
    } catch (err: any) {
      console.error('Failed to load modules', err);
    }
  };

  const fetchTests = async () => {
    setLoading(true);
    setError('');
    try {
      const params: any = { page, size };
      if (moduleFilter) params.module_id = moduleFilter;
      const res = await getTests(params);
      setTests(res.data.items);
      setTotal(res.data.total);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка загрузки тестов');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Удалить тест?')) return;
    try {
      await deleteTest(id);
      fetchTests();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка удаления');
    }
  };

  const totalPages = Math.ceil(total / size);

  // --- Seminarist / Candidate view ---
  if (isTestTaker && !isManager) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">Доступные тесты</h1>
        {error && <div className="bg-red-50 text-red-700 p-3 rounded mb-4">{error}</div>}
        {loading ? <LoadingSpinner /> : (
          <>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {tests.map((test) => (
                <div key={test.id} className="bg-white p-6 rounded-lg shadow hover:shadow-md transition">
                  <h3 className="text-lg font-semibold">{test.title}</h3>
                  <p className="text-gray-600 mt-1 text-sm">{test.description}</p>
                  <div className="mt-3 flex gap-2 text-sm text-gray-500">
                    <span>Вопросов: {test.question_count}</span>
                    <span>Проходной: {test.pass_score}%</span>
                  </div>
                  <button
                    onClick={() => navigate(`/tests/${test.id}/take`)}
                    className="mt-4 w-full px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                  >
                    Начать тест
                  </button>
                </div>
              ))}
            </div>
            <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
          </>
        )}
      </div>
    );
  }

  // --- Admin / Methodist view ---
  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Тесты</h1>
        <Link
          to="/tests/create"
          className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
        >
          + Создать тест
        </Link>
      </div>

      {error && <div className="bg-red-50 text-red-700 p-3 rounded mb-4">{error}</div>}

      <div className="mb-4">
        <select
          value={moduleFilter}
          onChange={(e) => { setModuleFilter(e.target.value); setPage(1); }}
          className="px-3 py-2 border border-gray-300 rounded"
        >
          <option value="">Все модули</option>
          {modules.map((m) => (
            <option key={m.id} value={m.id}>{m.title}</option>
          ))}
        </select>
      </div>

      {loading ? <LoadingSpinner /> : (
        <>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Название</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Вопросов</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Проходной</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Статус</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Действия</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {tests.map((test) => (
                  <tr key={test.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <Link to={`/tests/${test.id}`} className="text-indigo-600 hover:underline font-medium">
                        {test.title}
                      </Link>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">{test.question_count}</td>
                    <td className="px-6 py-4 text-sm text-gray-500">{test.pass_score}%</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-xs ${test.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                        {test.is_active ? 'Активен' : 'Неактивен'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right text-sm">
                      <Link to={`/tests/${test.id}/edit`} className="text-indigo-600 hover:underline mr-3">Редактировать</Link>
                      <Link to={`/tests/${test.id}/attempts`} className="text-indigo-600 hover:underline mr-3">Результаты</Link>
                      <button onClick={() => handleDelete(test.id)} className="text-red-600 hover:underline">Удалить</button>
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
