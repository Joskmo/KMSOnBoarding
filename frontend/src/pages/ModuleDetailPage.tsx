import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { contentApi } from '../api/client';
import { updateLesson, deleteLesson, updateHeuristic, deleteHeuristic, approveHeuristicEdit, rejectHeuristicEdit } from '../api/content';
import { useAuth } from '../context/AuthContext';
import { RoleGuard } from '../components/RoleGuard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import MarkdownEditor from '../components/MarkdownEditor';
import type { Module, Lesson, Heuristic } from '../types';

export function ModuleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user, hasRole } = useAuth();

  const [module, setModule] = useState<Module | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [heuristics, setHeuristics] = useState<Heuristic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Lesson create form
  const [showLessonForm, setShowLessonForm] = useState(false);
  const [lessonTitle, setLessonTitle] = useState('');
  const [lessonR7Uri, setLessonR7Uri] = useState('');
  const [lessonContent, setLessonContent] = useState('');
  const [lessonSaving, setLessonSaving] = useState(false);
  const [r7Status, setR7Status] = useState<{ message: string; type: 'success' | 'warning' } | null>(null);

  // Heuristic create form
  const [showHeuristicForm, setShowHeuristicForm] = useState(false);
  const [heuristicContent, setHeuristicContent] = useState('');
  const [heuristicSaving, setHeuristicSaving] = useState(false);

  // Inline edit state
  const [lessonEdits, setLessonEdits] = useState<Record<string, { title: string; r7_uri: string; content: string }>>({});
  const [heuristicEdits, setHeuristicEdits] = useState<Record<string, { content: string }>>({});

  const canModerate = () => {
    if (!user) return false;
    if (hasRole(['admin'])) return true;
    if (hasRole(['methodist']) && module?.manager_id === user.id) return true;
    return false;
  };

  const canEditLesson = () => {
    return hasRole(['admin', 'methodist']);
  };

  const canEditHeuristic = (h: Heuristic) => {
    if (!user) return false;
    if (hasRole(['admin'])) return true;
    if (hasRole(['methodist']) && module?.manager_id === user.id) return true;
    if (h.author_id === user.id) return true;
    return false;
  };

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

  const handleDeleteModule = async () => {
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
        content: lessonContent || undefined,
      });
      setLessonTitle('');
      setLessonR7Uri('');
      setLessonContent('');
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

  const startEditLesson = (lesson: Lesson) => {
    setLessonEdits((prev) => ({
      ...prev,
      [lesson.id]: {
        title: lesson.title,
        r7_uri: lesson.r7_uri,
        content: lesson.content || '',
      },
    }));
  };

  const cancelEditLesson = (lessonId: string) => {
    setLessonEdits((prev) => {
      const next = { ...prev };
      delete next[lessonId];
      return next;
    });
  };

  const saveLesson = async (lessonId: string) => {
    const draft = lessonEdits[lessonId];
    if (!draft) return;
    setError('');
    try {
      await updateLesson(lessonId, {
        title: draft.title,
        r7_uri: draft.r7_uri,
        content: draft.content || null,
      });
      setLessonEdits((prev) => {
        const next = { ...prev };
        delete next[lessonId];
        return next;
      });
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка сохранения урока');
    }
  };

  const handleDeleteLesson = async (lessonId: string) => {
    if (!window.confirm('Удалить урок?')) return;
    setError('');
    try {
      await deleteLesson(lessonId);
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка удаления урока');
    }
  };

  const startEditHeuristic = (h: Heuristic) => {
    setHeuristicEdits((prev) => ({
      ...prev,
      [h.id]: {
        content: h.content,
      },
    }));
  };

  const cancelEditHeuristic = (hId: string) => {
    setHeuristicEdits((prev) => {
      const next = { ...prev };
      delete next[hId];
      return next;
    });
  };

  const saveHeuristic = async (hId: string) => {
    const draft = heuristicEdits[hId];
    if (!draft) return;
    setError('');
    try {
      await updateHeuristic(hId, { content: draft.content });
      setHeuristicEdits((prev) => {
        const next = { ...prev };
        delete next[hId];
        return next;
      });
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка сохранения эвристики');
    }
  };

  const handleDeleteHeuristic = async (hId: string) => {
    if (!window.confirm('Удалить эвристику?')) return;
    setError('');
    try {
      await deleteHeuristic(hId);
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка удаления эвристики');
    }
  };

  const handleApproveHeuristicEdit = async (hId: string) => {
    setError('');
    try {
      await approveHeuristicEdit(hId);
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка одобрения правок');
    }
  };

  const handleRejectHeuristicEdit = async (hId: string) => {
    setError('');
    try {
      await rejectHeuristicEdit(hId);
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка отклонения правок');
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
              onClick={handleDeleteModule}
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
        <div className="space-y-4">
          {lessons.map((lesson) => {
            const isEditing = lesson.id in lessonEdits;
            const draft = lessonEdits[lesson.id];
            return (
              <div key={lesson.id} className="bg-white p-4 rounded shadow">
                {!isEditing ? (
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-gray-500">#{lesson.order_index}</span>
                        <span className="font-medium text-lg">{lesson.title}</span>
                      </div>
                      {lesson.content && (
                        <div className="mt-2 prose prose-sm max-w-none text-gray-700">
                          <ReactMarkdown>{lesson.content}</ReactMarkdown>
                        </div>
                      )}
                      <div className="mt-3">
                        <iframe
                          src={lesson.r7_uri}
                          title={`Презентация: ${lesson.title}`}
                          width="100%"
                          height="500"
                          className="border border-gray-300 rounded"
                          allowFullScreen
                        />
                      </div>
                    </div>
                    {canEditLesson() && (
                      <div className="flex gap-2 ml-4">
                        <button
                          onClick={() => startEditLesson(lesson)}
                          className="text-sm text-indigo-600 hover:underline"
                        >
                          Редактировать
                        </button>
                        <button
                          onClick={() => handleDeleteLesson(lesson.id)}
                          className="text-sm text-red-600 hover:underline"
                        >
                          Удалить
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Название</label>
                      <input
                        type="text"
                        value={draft.title}
                        onChange={(e) =>
                          setLessonEdits((prev) => ({
                            ...prev,
                            [lesson.id]: { ...draft, title: e.target.value },
                          }))
                        }
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Ссылка на презентацию (R7 URI)</label>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={draft.r7_uri}
                          onChange={(e) =>
                            setLessonEdits((prev) => ({
                              ...prev,
                              [lesson.id]: { ...draft, r7_uri: e.target.value },
                            }))
                          }
                          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                        />
                        <button
                          type="button"
                          onClick={() => validateR7Uri(draft.r7_uri)}
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
                        value={draft.content}
                        onChange={(value) =>
                          setLessonEdits((prev) => ({
                            ...prev,
                            [lesson.id]: { ...draft, content: value },
                          }))
                        }
                        placeholder="Введите markdown-содержимое..."
                      />
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => saveLesson(lesson.id)}
                        className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                      >
                        Сохранить
                      </button>
                      <button
                        onClick={() => cancelEditLesson(lesson.id)}
                        className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
                      >
                        Отмена
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
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
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={lessonR7Uri}
                      onChange={(e) => setLessonR7Uri(e.target.value)}
                      placeholder="https://..."
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => validateR7Uri(lessonR7Uri)}
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
                    value={lessonContent}
                    onChange={setLessonContent}
                    placeholder="Введите markdown-содержимое..."
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
                    onClick={() => { setShowLessonForm(false); setLessonTitle(''); setLessonR7Uri(''); setLessonContent(''); setR7Status(null); }}
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
        <div className="space-y-4">
          {heuristics.map((h) => {
            const isEditing = h.id in heuristicEdits;
            const draft = heuristicEdits[h.id];
            const showPending = h.pending_content !== null && h.pending_content !== undefined;
            const isAuthor = user?.id === h.author_id;
            return (
              <div key={h.id} className="bg-white p-4 rounded shadow">
                {!isEditing ? (
                  <div>
                    <div className="prose prose-sm max-w-none text-gray-800">
                      <ReactMarkdown>{h.content}</ReactMarkdown>
                    </div>
                    <div className="mt-2 flex gap-2 items-center flex-wrap">
                      {h.is_approved ? (
                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">Одобрена</span>
                      ) : (
                        <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs">На модерации</span>
                      )}
                      {showPending && (isAuthor || canModerate()) && (
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">Редакция на рассмотрении</span>
                      )}
                      {canEditHeuristic(h) && (
                        <>
                          <button
                            onClick={() => startEditHeuristic(h)}
                            className="text-xs text-indigo-600 hover:underline"
                          >
                            Редактировать
                          </button>
                          <button
                            onClick={() => handleDeleteHeuristic(h.id)}
                            className="text-xs text-red-600 hover:underline"
                          >
                            Удалить
                          </button>
                        </>
                      )}
                      <RoleGuard allowedRoles={['admin', 'methodist']}>
                        {!h.is_approved && canModerate() && (
                          <button
                            onClick={() => handleApproveHeuristic(h.id)}
                            className="text-xs text-indigo-600 hover:underline"
                          >
                            Одобрить
                          </button>
                        )}
                      </RoleGuard>
                    </div>

                    {/* Pending edits moderation block */}
                    {showPending && canModerate() && (
                      <div className="mt-4 p-3 bg-gray-50 rounded border border-gray-200">
                        <p className="text-sm font-medium text-gray-700 mb-2">Предложенные правки:</p>
                        <div className="prose prose-sm max-w-none text-gray-600 bg-white p-2 rounded border border-gray-100">
                          <ReactMarkdown>{h.pending_content!}</ReactMarkdown>
                        </div>
                        <div className="mt-2 flex gap-2">
                          <button
                            onClick={() => handleApproveHeuristicEdit(h.id)}
                            className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700"
                          >
                            Одобрить правки
                          </button>
                          <button
                            onClick={() => handleRejectHeuristicEdit(h.id)}
                            className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700"
                          >
                            Отклонить правки
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Содержание</label>
                      <MarkdownEditor
                        value={draft.content}
                        onChange={(value) =>
                          setHeuristicEdits((prev) => ({
                            ...prev,
                            [h.id]: { ...draft, content: value },
                          }))
                        }
                        placeholder="Введите содержимое эвристики..."
                      />
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => saveHeuristic(h.id)}
                        className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                      >
                        Сохранить
                      </button>
                      <button
                        onClick={() => cancelEditHeuristic(h.id)}
                        className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
                      >
                        Отмена
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
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
                  <label className="block text-sm font-medium text-gray-700 mb-1">Содержание *</label>
                  <MarkdownEditor
                    value={heuristicContent}
                    onChange={setHeuristicContent}
                    placeholder="Введите содержимое эвристики..."
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
