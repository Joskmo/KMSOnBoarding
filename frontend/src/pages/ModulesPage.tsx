import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { contentApi } from '../api/client';
import { RoleGuard } from '../components/RoleGuard';
import type { Module } from '../types';

export function ModulesPage() {
  const [modules, setModules] = useState<Module[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [size] = useState(20);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchModules();
  }, [page, statusFilter]);

  const fetchModules = async () => {
    setLoading(true);
    try {
      const params: any = { page, size };
      if (statusFilter) params.status = statusFilter;
      
      const res = await contentApi.get('/modules', { params });
      setModules(res.data.items);
      setTotal(res.data.total);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка загрузки модулей');
    } finally {
      setLoading(false);
    }
  };

  const totalPages = Math.ceil(total / size);

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Модули</h1>
        
        <RoleGuard allowedRoles={['admin', 'methodist']}>
          <Link
            to="/modules/new"
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
          >
            + Создать модуль
          </Link>
        </RoleGuard>
      </div>

      <div className="mb-4 flex gap-4">
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="px-3 py-2 border border-gray-300 rounded"
        >
          <option value="">Все статусы</option>
          <option value="draft">Черновик</option>
          <option value="published">Опубликован</option>
          <option value="archived">В архиве</option>
        </select>
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 p-3 rounded mb-4">{error}</div>
      )}

      {loading ? (
        <div className="text-center py-8">Загрузка...</div>
      ) : (
        <>
          <div className="grid gap-4">
            {modules.map((module) => (
              <div key={module.id} className="bg-white p-6 rounded-lg shadow hover:shadow-md transition">
                <div className="flex justify-between items-start">
                  <div>
                    <Link 
                      to={`/modules/${module.id}`}
                      className="text-lg font-semibold text-indigo-600 hover:underline"
                    >
                      {module.title}
                    </Link>
                    <p className="text-gray-600 mt-1">{module.description}</p>
                    <div className="mt-2 flex gap-2">
                      <span className={`px-2 py-1 rounded text-xs ${
                        module.status === 'published' ? 'bg-green-100 text-green-800' :
                        module.status === 'draft' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {module.status}
                      </span>
                      <span className="text-xs text-gray-500">
                        Уроков: {module.lesson_count}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex justify-center gap-2 mt-6">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 border rounded disabled:opacity-50"
              >
                ← Назад
              </button>
              <span className="px-3 py-1">Страница {page} из {totalPages}</span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1 border rounded disabled:opacity-50"
              >
                Вперед →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
