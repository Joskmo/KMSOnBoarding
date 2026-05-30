import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { contentApi } from '../api/client';
import { updateLesson, deleteLesson } from '../api/content';
import { useAuth } from '../context/AuthContext';
import { LoadingSpinner } from '../components/LoadingSpinner';
import MarkdownEditor from '../components/MarkdownEditor';
import type { Lesson, Module } from '../types';

export function LessonDetailPage() {
  const { id, lessonId } = useParams<{ id: string; lessonId: string }>();
  const navigate = useNavigate();
  const { user, hasRole } = useAuth();

  const [module, setModule] = useState<Module | null>(null);
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [isEditing, setIsEditing] = useState(false);
  const [draftTitle, setDraftTitle] = useState('');
  const [draftR7Uri, setDraftR7Uri] = useState('');
  const [draftContent, setDraftContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [r7Status, setR7Status] = useState<{ message: string; type: 'success' | 'warning' } | null>(null);

  const canEdit = () => {
    if (!user || !module) return false;
    if (hasRole(['admin'])) return true;
    if (hasRole(['methodist']) && module.manager_id === user.id) return true;
    return false;
  };

  const fetchData = async () => {
    if (!id || !lessonId) return;
    setLoading(true);
    try {
      const [modRes, lessonRes] = await Promise.all([
        contentApi.get(`/modules/${id}`),
        contentApi.get(`/lessons/${lessonId}`),
      ]);
      setModule(modRes.data);
      setLesson(lessonRes.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка загрузки');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id, lessonId]);

  const startEdit = () => {
    if (!lesson) return;
    setDraftTitle(lesson.title);
    setDraftR7Uri(lesson.r7_uri);
    setDraftContent(lesson.content || '');
    setIsEditing(true);
    setR7Status(null);
  };

  const cancelEdit = () => {
    setIsEditing(false);
    setR7Status(null);
  };

  const handleSave = async () => {
    if (!lessonId) return;
    setSaving(true);
    setError('');
    try {
      await updateLesson(lessonId, {
        title: draftTitle,
        r7_uri: draftR7Uri,
        content: draftContent || null,
      });
      setIsEditing(false);
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!lessonId) return;
    if (!window.confirm('Удалить материал?')) return;
    setError('');
    try {
      await deleteLesson(lessonId);
      navigate(`/modules/${id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка удаления');
    }
  };

  const validateR7Uri = async (uri: string) => {
    if (!uri) {
      setR7Status(null);
      return;
    }
    try {
      new URL(uri);
      const response = await fetch(uri, { method: 'HEAD' });
      if (response.ok) {
        setR7Status({ message: 'Ссылка доступна', type: 'success' });
      } else {
        setR7Status({ message: `Сервер ответил со статусом ${response.status}. Ссылка может быть недоступна.`, type: 'warning' });
      }
    } catch {
      setR7Status({ message: 'Не удалось проверить ссылку. Убедитесь, что URI корректен.', type: 'warning' });
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="text-red-600 py-8">{error}</div>;
  if (!lesson) return <div>Материал не найден</div>;

  return (
    <div>
      {/* Breadcrumbs */}
      <div className="mb-4 text-sm text-gray-600">
        <Link to="/modules" className="hover:underline">Модули</Link>
        <span className="mx-2">/</span>
        <Link to={`/modules/${id}`} className="hover:underline">{module?.title || 'Модуль'}</Link>
        <span className="mx-2">/</span>
        <span className="text-gray-900">{lesson.title}</span>
      </div>

      {!isEditing ? (
        <>
          <div className="flex justify-between items-start mb-4">
            <h1 className="text-2xl font-bold">{lesson.title}</h1>
            {canEdit() && (
              <div className="flex gap-2">
                <button
                  onClick={startEdit}
                  className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                >
                  Редактировать
                </button>
                <button
                  onClick={handleDelete}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                >
                  Удалить
                </button>
              </div>
            )}
          </div>

          {lesson.content && (
            <div className="prose prose-sm max-w-none text-gray-700 mb-6">
              <ReactMarkdown>{lesson.content}</ReactMarkdown>
            </div>
          )}

          <div className="mt-4">
            <iframe
              src={lesson.r7_uri}
              title={`Презентация: ${lesson.title}`}
              width="100%"
              height="600"
              className="border border-gray-300 rounded"
              allowFullScreen
            />
          </div>
        </>
      ) : (
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200 max-w-3xl">
          <h2 className="text-xl font-semibold mb-4">Редактирование материала</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Название</label>
              <input
                type="text"
                value={draftTitle}
                onChange={(e) => setDraftTitle(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Ссылка на презентацию (R7 URI)</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={draftR7Uri}
                  onChange={(e) => setDraftR7Uri(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                />
                <button
                  type="button"
                  onClick={() => validateR7Uri(draftR7Uri)}
                  className="mt-1 px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm"
                >
                  Проверить
                </button>
              </div>
              {r7Status && (
                <p className={`text-xs mt-1 ${r7Status.type === 'success' ? 'text-green-600' : 'text-yellow-600'}`}>
                  {r7Status.message}
                </p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Содержание (Markdown)</label>
              <MarkdownEditor
                value={draftContent}
                onChange={setDraftContent}
                placeholder="Введите markdown-содержимое..."
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
              >
                {saving ? 'Сохранение...' : 'Сохранить'}
              </button>
              <button
                onClick={cancelEdit}
                className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
