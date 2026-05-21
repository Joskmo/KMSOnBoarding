import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { contentApi } from '../api/client';
import { RoleGuard } from '../components/RoleGuard';
import type { Module, Lesson, Heuristic } from '../types';

export function ModuleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [module, setModule] = useState<Module | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [heuristics, setHeuristics] = useState<Heuristic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (id) fetchData();
  }, [id]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [modRes, lessonsRes, heurRes] = await Promise.all([
        contentApi.get(`/modules/${id}`),
        contentApi.get(`/modules/${id}/lessons`),
        contentApi.get(`/modules/${id}/heuristics`),
      ]);
      setModule(modRes.data);
      setLessons(lessonsRes.data);
      setHeuristics(heurRes.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка загрузки');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Удалить модуль?')) return;
    try {
      await contentApi.delete(`/modules/${id}`);
      navigate('/modules');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка удаления');
    }
  };

  if (loading) return <div className="text-center py-8">Загрузка...</div>;
  if (error) return <div className="text-red-600 py-8">{error}</div>;
  if (!module) return <div>Модуль не найден</div>;

  return (
    <div>
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-3xl font-bold">{module.title}</h1>
          <p className="text-gray-600 mt-2">{module.description}</p>
          <div className="mt-2 flex gap-2">
            <span className={`px-2 py-1 rounded text-xs ${
              module.status === 'published' ? 'bg-green-100 text-green-800' :
              module.status === 'draft' ? 'bg-yellow-100 text-yellow-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {module.status}
            </span>
          </div>
        </div>
        
        <div className="flex gap-2">
          <RoleGuard allowedRoles={['admin', 'methodist']}>
            <Link
              to={`/modules/${id}/edit`}
              className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
            >
              Редактировать
            </Link>
            <button
              onClick={handleDelete}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Удалить
            </button>
          </RoleGuard>
        </div>
      </div>

      {/* Уроки */}
      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-4">Уроки ({lessons.length})</h2>
        <div className="space-y-2">
          {lessons.map((lesson) => (
            <div key={lesson.id} className="bg-white p-4 rounded shadow flex justify-between items-center">
              <div>
                <span className="text-gray-500 mr-2">#{lesson.order_index}</span>
                <span className="font-medium">{lesson.title}</span>
              </div>
              <a 
                href={lesson.r7_uri} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-indigo-600 hover:underline text-sm"
              >
                Открыть презентацию →
              </a>
            </div>
          ))}
        </div>
        
        <RoleGuard allowedRoles={['admin', 'methodist']}>
          <button className="mt-4 px-4 py-2 border border-indigo-600 text-indigo-600 rounded hover:bg-indigo-50">
            + Добавить урок
          </button>
        </RoleGuard>
      </div>

      {/* Эвристики */}
      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-4">Эвристики ({heuristics.length})</h2>
        <div className="space-y-2">
          {heuristics.map((h) => (
            <div key={h.id} className="bg-white p-4 rounded shadow">
              <p className="text-gray-800">{h.content}</p>
              <div className="mt-2 flex gap-2 items-center">
                {h.is_approved ? (
                  <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">Одобрена</span>
                ) : (
                  <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs">На модерации</span>
                )}
                <RoleGuard allowedRoles={['admin', 'methodist']}>
                  {!h.is_approved && (
                    <button className="text-xs text-indigo-600 hover:underline">
                      Одобрить
                    </button>
                  )}
                </RoleGuard>
              </div>
            </div>
          ))}
        </div>
        
        <RoleGuard allowedRoles={['admin', 'seminarist', 'candidate']}>
          <button className="mt-4 px-4 py-2 border border-indigo-600 text-indigo-600 rounded hover:bg-indigo-50">
            + Добавить эвристику
          </button>
        </RoleGuard>
      </div>
    </div>
  );
}
