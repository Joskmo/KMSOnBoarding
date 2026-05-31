import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { contentApi } from '../api/client';
import { getTests, deleteTest, getMyAttempts } from '../api/assessment';
import { Pagination } from '../components/Pagination';
import { LoadingSpinner } from '../components/LoadingSpinner';
import type { Test, Module, AttemptListItem } from '../types';

export function TestsListPage() {
  const { hasRole } = useAuth();
  const navigate = useNavigate();
  const [tests, setTests] = useState<Test[]>([]);
  const [modules, setModules] = useState<Module[]>([]);
  const [myAttempts, setMyAttempts] = useState<AttemptListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [size] = useState(20);
  const [moduleFilter, setModuleFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const isManager = hasRole(['admin', 'methodist']);
  const isTestTaker = hasRole(['methodist', 'seminarist', 'candidate']);

  const fetchTests = useCallback(async () => {
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
  }, [page, moduleFilter, size]);

  useEffect(() => {
    const fetchModules = async () => {
      try {
        const res = await contentApi.get('/modules?page=1&size=100');
        setModules(res.data.items || []);
      } catch (err: any) {
        console.error('Failed to load modules', err);
      }
    };
    const fetchAttempts = async () => {
      try {
        const res = await getMyAttempts({ size: 100 });
        setMyAttempts(res.data.items || []);
      } catch (err: any) {
        console.error('Failed to load attempts', err);
      }
    };
    fetchModules();
    fetchTests();
    fetchAttempts();
  }, [page, moduleFilter, fetchTests]);

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

  // --- Test taker view (methodist, seminarist, candidate) ---
  if (isTestTaker && !isManager) {
    const accessibleModuleIds = new Set(modules.map((m) => m.id));
    const accessibleTests = tests.filter((t) => accessibleModuleIds.has(t.module_id));

    // Build a map of best attempt per test
    const bestAttemptByTest = new Map<string, AttemptListItem>();
    myAttempts.forEach((a) => {
      const existing = bestAttemptByTest.get(a.test_id);
      if (!existing || a.score > existing.score) {
        bestAttemptByTest.set(a.test_id, a);
      }
    });

    const passedTests = accessibleTests.filter((t) => bestAttemptByTest.get(t.id)?.is_passed);
    const notPassedTests = accessibleTests.filter((t) => !bestAttemptByTest.get(t.id)?.is_passed);

    return (
      <div>
        <button
          type="button"
          onClick={() => navigate('/modules')}
          className="text-sm text-gray-500 hover:text-gray-700 mb-2"
        >
          ← Назад
        </button>
        <h1 className="text-2xl font-bold mb-6">Доступные тесты</h1>
        {error && <div className="bg-red-50 text-red-700 p-3 rounded mb-4">{error}</div>}
        {loading ? <LoadingSpinner /> : (
          <>
            {/* Not passed / available tests */}
            {notPassedTests.length === 0 && passedTests.length === 0 ? (
              <div className="text-center py-8 text-gray-500">Нет доступных тестов</div>
            ) : (
              <>
                {notPassedTests.length > 0 && (
                  <>
                    <h2 className="text-lg font-semibold mb-3 text-gray-700">Новые тесты</h2>
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 mb-8">
                      {notPassedTests.map((test) => {
                        const attempt = bestAttemptByTest.get(test.id);
                        return (
                          <div key={test.id} className="bg-white p-6 rounded-lg shadow hover:shadow-md transition">
                            <h3 className="text-lg font-semibold">{test.title}</h3>
                            <p className="text-gray-600 mt-1 text-sm">{test.description}</p>
                            <div className="mt-3 flex gap-2 text-sm text-gray-500">
                              <span>Вопросов: {test.question_count}</span>
                              <span>Проходной: {test.pass_score}%</span>
                            </div>
                            {attempt && !attempt.is_passed && (
                              <div className="mt-2 text-sm text-red-600">
                                Последняя попытка: {attempt.score}% (не пройден)
                              </div>
                            )}
                            <button
                              onClick={() => navigate(`/tests/${test.id}/take`)}
                              className="mt-4 w-full px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                            >
                              {attempt ? 'Повторить тест' : 'Начать тест'}
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  </>
                )}

                {/* Passed tests history */}
                {passedTests.length > 0 && (
                  <>
                    <h2 className="text-lg font-semibold mb-3 text-gray-700">Пройденные тесты</h2>
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                      {passedTests.map((test) => {
                        const attempt = bestAttemptByTest.get(test.id)!;
                        return (
                          <div key={test.id} className="bg-white p-6 rounded-lg shadow border border-green-200">
                            <div className="flex justify-between items-start">
                              <h3 className="text-lg font-semibold">{test.title}</h3>
                              <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">
                                Пройден
                              </span>
                            </div>
                            <p className="text-gray-600 mt-1 text-sm">{test.description}</p>
                            <div className="mt-3 flex gap-2 text-sm text-gray-500">
                              <span>Вопросов: {test.question_count}</span>
                              <span>Проходной: {test.pass_score}%</span>
                            </div>
                            <div className="mt-2 text-sm text-green-700 font-medium">
                              Результат: {attempt.score}%
                            </div>
                            <button
                              onClick={() => navigate(`/tests/${test.id}/take`)}
                              className="mt-4 w-full px-4 py-2 border border-indigo-600 text-indigo-600 rounded hover:bg-indigo-50"
                            >
                              Пройти снова
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  </>
                )}
                <Pagination page={page} totalPages={Math.ceil(accessibleTests.length / size)} onPageChange={setPage} />
              </>
            )}
          </>
        )}
      </div>
    );
  }

  // --- Admin / Methodist view ---
  return (
    <div>
      <button
        type="button"
        onClick={() => navigate('/modules')}
        className="text-sm text-gray-500 hover:text-gray-700 mb-2"
      >
        ← Назад
      </button>
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

      {loading ? <LoadingSpinner /> : tests.length === 0 ? (
        <div className="text-center py-8 text-gray-500">Нет тестов</div>
      ) : (
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
