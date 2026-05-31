import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { contentApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { RoleGuard } from '../components/RoleGuard';
import type { Module } from '../types';

export function ModulesPage() {
  const { hasRole } = useAuth();
  const isManager = hasRole(['admin', 'methodist']);

  const [modules, setModules] = useState<Module[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'published' | 'draft' | 'archived'>('published');

  useEffect(() => {
    const fetchModules = async () => {
      setLoading(true);
      try {
        const res = await contentApi.get('/modules', { params: { page: 1, size: 100 } });
        setModules(res.data.items);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Ошибка загрузки модулей');
      } finally {
        setLoading(false);
      }
    };
    fetchModules();
  }, []);

  const publishedModules = modules.filter((m) => m.status === 'published');
  const draftModules = modules.filter((m) => m.status === 'draft');
  const archivedModules = modules.filter((m) => m.status === 'archived');

  const displayedModules =
    activeTab === 'published'
      ? publishedModules
      : activeTab === 'draft'
        ? draftModules
        : archivedModules;

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

      {/* Tabs — only for admin/methodist */}
      {isManager && (
        <div className="mb-4 border-b border-gray-200">
          <nav className="flex gap-6">
            <button
              onClick={() => setActiveTab('published')}
              className={`pb-2 text-sm font-medium border-b-2 transition ${
                activeTab === 'published'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Опубликованные {publishedModules.length > 0 && `(${publishedModules.length})`}
            </button>
            <button
              onClick={() => setActiveTab('draft')}
              className={`pb-2 text-sm font-medium border-b-2 transition ${
                activeTab === 'draft'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Черновики {draftModules.length > 0 && `(${draftModules.length})`}
            </button>
            <button
              onClick={() => setActiveTab('archived')}
              className={`pb-2 text-sm font-medium border-b-2 transition ${
                activeTab === 'archived'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Архив {archivedModules.length > 0 && `(${archivedModules.length})`}
            </button>
          </nav>
        </div>
      )}

      {error && (
        <div className="bg-red-50 text-red-700 p-3 rounded mb-4">{error}</div>
      )}

      {loading ? (
        <div className="text-center py-8">Загрузка...</div>
      ) : (
        <div className="grid gap-4">
          {(isManager ? displayedModules : publishedModules).map((module) => (
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
                    {isManager && (
                      <span className={`px-2 py-1 rounded text-xs ${
                        module.status === 'published' ? 'bg-green-100 text-green-800' :
                        module.status === 'draft' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {module.status === 'published' ? 'Опубликован' : module.status === 'draft' ? 'Черновик' : 'В архиве'}
                      </span>
                    )}
                    <span className="text-xs text-gray-500">
                      Уроков: {module.lesson_count}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
          {(isManager ? displayedModules : publishedModules).length === 0 && (
            <div className="text-center py-8 text-gray-500">
              {isManager
                ? (activeTab === 'published'
                    ? 'Нет опубликованных модулей'
                    : activeTab === 'draft'
                      ? 'Нет черновиков'
                      : 'Нет архивных модулей')
                : 'Нет доступных модулей'}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
