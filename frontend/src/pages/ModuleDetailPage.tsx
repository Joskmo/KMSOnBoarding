import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { contentApi } from '../api/client';
import { RoleGuard } from '../components/RoleGuard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import type { Module, Lesson, Heuristic } from '../types';

export function ModuleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [module, setModule] = useState<Module | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [heuristics, setHeuristics] = useState<Heuristic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Lesson form state
  const [showLessonForm, setShowLessonForm] = useState(false);
  const [lessonTitle, setLessonTitle] = useState('');
  const [lessonR7Uri, setLessonR7Uri] = useState('');
  const [lessonSaving, setLessonSaving] = useState(false);

  // Heuristic form state
  const [showHeuristicForm, setShowHeuristicForm] = useState(false);
  const [heuristicContent, setHeuristicContent] = useState('');
  const [heuristicSaving, setHeuristicSaving] = useState(false);

  const fetchData = async () => {
    if (!id) return;
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

  useEffect(() => {
    fetchData();
  }, [id]);

  const handleDelete = async () => {
    if (!window.confirm('Удалить модуль?')) return;
    try {
      await contentApi.delete(`/modules/${id}`);
      navigate('/modules');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка удаления');
    }
  };

  const handleCreateLesson = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setLessonSaving(true);
    setError('');
    try {
      await contentApi.post(`/modules/${id}/lessons`, {
        title: lessonTitle,
        r7_uri: lessonR7Uri,
      });
      setLessonTitle('');
      setLessonR7Uri('');
      setShowLessonForm(false);
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка создания урока');
    } finally {
      setLessonSaving(false);
    }
  };

  const handleCreateHeuristic = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setHeuristicSaving(true);
    setError('');
    try {
      await contentApi.post(`/modules/${id}/heuristics`, {
        content: heuristicContent,
      });
      setHeuristicContent('');
      setShowHeuristicForm(false);
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка создания эвристики');
    } finally {
      setHeuristicSaving(false);
    }
  };

  const handleApproveHeuristic = async (heuristicId: string) => {
    setError('');
    try {
      await contentApi.patch(`/heuristics/${heuristicId}/approve`);
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка одобрения');
    }
  };

  if (loading) return <LoadingSpinner />;
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
          {!showLessonForm ? (
            <button
              onClick={() => setShowLessonForm(true)}
              className="mt-4 px-4 py-2 border border-indigo-600 text-indigo-600 rounded hover:bg-indigo-50"
            >
              + Добавить урок
            </button>
          ) : (
            <form onSubmit={handleCreateLesson} className="mt-4 bg-white p-6 rounded-lg shadow border border-gray-200 max-w-2xl">
              <h3 className="text-lg font-semibold mb-4">Новый урок</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Название *</label>
                  <input
                    type="text"
                    value={lessonTitle}
                    onChange={(e) => setLessonTitle(e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Ссылка на презентацию (R7 URI) *</label>
                  <input
                    type="text"
                    value={lessonR7Uri}
                    onChange={(e) => setLessonR7Uri(e.target.value)}
                    placeholder="https://..."
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                    required
                  />
                </div>
                <div className="flex gap-4">
                  <button
                    type="submit"
                    disabled={lessonSaving}
                    className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
                  >
                    {lessonSaving ? 'Сохранение...' : 'Сохранить'}
                  </button>
                  <button
                    type="button"
                    onClick={() => { setShowLessonForm(false); setLessonTitle(''); setLessonR7Uri(''); }}
                    className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
                  >
                    Отмена
                  </button>
                </div>
              </div>
            </form>
          )}
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
                    <button
                      onClick={() => handleApproveHeuristic(h.id)}
                      className="text-xs text-indigo-600 hover:underline"
                    >
                      Одобрить
                    </button>
                  )}
                </RoleGuard>
              </div>
            </div>
          ))}
        </div>

        <RoleGuard allowedRoles={['admin', 'seminarist', 'candidate']}>
          {!showHeuristicForm ? (
            <button
              onClick={() => setShowHeuristicForm(true)}
              className="mt-4 px-4 py-2 border border-indigo-600 text-indigo-600 rounded hover:bg-indigo-50"
            >
              + Добавить эвристику
            </button>
          ) : (
            <form onSubmit={handleCreateHeuristic} className="mt-4 bg-white p-6 rounded-lg shadow border border-gray-200 max-w-2xl">
              <h3 className="text-lg font-semibold mb-4">Новая эвристика</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Содержание *</label>
                  <textarea
                    value={heuristicContent}
                    onChange={(e) => setHeuristicContent(e.target.value)}
                    rows={3}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                    required
                  />
                </div>
                <div className="flex gap-4">
                  <button
                    type="submit"
                    disabled={heuristicSaving}
                    className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
                  >
                    {heuristicSaving ? 'Сохранение...' : 'Сохранить'}
                  </button>
                  <button
                    type="button"
                    onClick={() => { setShowHeuristicForm(false); setHeuristicContent(''); }}
                    className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
                  >
                    Отмена
                  </button>
                </div>
              </div>
            </form>
          )}
        </RoleGuard>
      </div>
    </div>
  );
}
