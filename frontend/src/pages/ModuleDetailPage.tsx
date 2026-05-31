import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { contentApi } from '../api/client';
import {
  updateHeuristic,
  deleteHeuristic,
  approveHeuristicEdit,
  rejectHeuristicEdit,
  getModuleAssignments,
  assignModule,
  unassignModule,
} from '../api/content';
import { getTests } from '../api/assessment';
import { authApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { RoleGuard } from '../components/RoleGuard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import MarkdownEditor from '../components/MarkdownEditor';
import type { Module, Lesson, Heuristic, ModuleAssignment, User } from '../types';
import type { Test } from '../types';

export function ModuleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user, hasRole } = useAuth();

  const [module, setModule] = useState<Module | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [heuristics, setHeuristics] = useState<Heuristic[]>([]);
  const [tests, setTests] = useState<Test[]>([]);
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
  const [heuristicEdits, setHeuristicEdits] = useState<Record<string, { content: string }>>({});

  // Assignments
  const [assignments, setAssignments] = useState<ModuleAssignment[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [availableUsers, setAvailableUsers] = useState<User[]>([]);
  const [selectedUserIds, setSelectedUserIds] = useState<Set<string>>(new Set());
  const [assignLoading, setAssignLoading] = useState(false);

  const isOwnModule = module?.author_id === user?.id;
  const canManage = hasRole(['admin']) || (hasRole(['methodist']) && isOwnModule);

  const canModerate = () => {
    if (!user) return false;
    if (hasRole(['admin'])) return true;
    if (hasRole(['methodist']) && isOwnModule) return true;
    return false;
  };

  const canEditHeuristic = (h: Heuristic) => {
    if (!user) return false;
    if (hasRole(['admin'])) return true;
    if (hasRole(['methodist']) && isOwnModule) return true;
    if (h.author_id === user.id) return true;
    return false;
  };

  const fetchAssignments = async () => {
    if (!id) return;
    try {
      const res = await getModuleAssignments(id);
      setAssignments(res.data);
    } catch {
      // silent fail
    }
  };

  const handleOpenAssignModal = async () => {
    setError('');
    setSelectedUserIds(new Set());
    try {
      const res = await authApi.get('/users');
      const allUsers: User[] = res.data;
      const assignedIds = new Set(assignments.map((a) => a.user_id));
      let filtered: User[];
      if (hasRole(['admin'])) {
        filtered = allUsers.filter(
          (u) =>
            (u.role === 'candidate' || u.role === 'seminarist' || u.role === 'methodist') &&
            !assignedIds.has(u.id)
        );
      } else {
        filtered = allUsers.filter(
          (u) =>
            (u.role === 'candidate' || u.role === 'seminarist') &&
            u.manager_id === user?.id &&
            !assignedIds.has(u.id)
        );
      }
      setAvailableUsers(filtered);
      setShowAssignModal(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка загрузки пользователей');
    }
  };

  const toggleUserSelection = (userId: string) => {
    setSelectedUserIds((prev) => {
      const next = new Set(prev);
      if (next.has(userId)) {
        next.delete(userId);
      } else {
        next.add(userId);
      }
      return next;
    });
  };

  const selectAllAvailable = () => {
    const allIds = new Set(availableUsers.map((u) => u.id));
    setSelectedUserIds(allIds);
  };

  const handleAssign = async () => {
    if (!id || selectedUserIds.size === 0) return;
    setAssignLoading(true);
    setError('');
    try {
      await assignModule(id, Array.from(selectedUserIds));
      setShowAssignModal(false);
      fetchAssignments();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка назначения');
    } finally {
      setAssignLoading(false);
    }
  };

  const handleUnassign = async (userId: string) => {
    if (!id) return;
    setError('');
    try {
      await unassignModule(id, userId);
      fetchAssignments();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка отзыва назначения');
    }
  };

  const fetchData = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [modRes, lessonsRes, heurRes, testsRes] = await Promise.all([
        contentApi.get(`/modules/${id}`),
        contentApi.get(`/modules/${id}/lessons`),
        contentApi.get(`/modules/${id}/heuristics`),
        getTests({ module_id: id, size: 100 }),
      ]);
      setModule(modRes.data);
      setLessons(lessonsRes.data);
      setHeuristics(heurRes.data);
      setTests(testsRes.data.items || []);
      if (hasRole(['admin', 'methodist'])) {
        fetchAssignments();
        try {
          const usersRes = await authApi.get('/users');
          setUsers(usersRes.data);
        } catch {
          // silent fail
        }
      }
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

  const handlePublishModule = async () => {
    if (!window.confirm('Опубликовать модуль?')) return;
    setError('');
    try {
      await contentApi.patch(`/modules/${id}/status`, { status: 'published' });
      navigate('/modules');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка публикации');
    }
  };

  const handleArchiveModule = async () => {
    if (!window.confirm('Отправить модуль в архив?')) return;
    setError('');
    try {
      await contentApi.patch(`/modules/${id}/status`, { status: 'archived' });
      navigate('/modules');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка архивации');
    }
  };

  const handleRestoreToDraft = async () => {
    if (!window.confirm('Вернуть модуль в черновики?')) return;
    setError('');
    try {
      await contentApi.patch(`/modules/${id}/status`, { status: 'draft' });
      navigate('/modules');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка восстановления');
    }
  };

  const handleCreateLesson = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setLessonSaving(true);
    setError('');
    try {
      const payload: Record<string, unknown> = {
        title: lessonTitle,
        content: lessonContent || undefined,
      };
      if (lessonR7Uri.trim()) {
        payload.r7_uri = lessonR7Uri.trim();
      }
      await contentApi.post(`/modules/${id}/lessons`, payload);
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
              {module.status === 'published' ? 'Опубликован' : module.status === 'draft' ? 'Черновик' : 'В архиве'}
            </span>
            {hasRole(['methodist']) && !isOwnModule && (
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                Назначен
              </span>
            )}
          </div>
        </div>

        <div className="flex gap-2">
          {canManage && (
            <>
              {(module.status === 'draft' || module.status === 'archived') && (
                <button
                  onClick={handlePublishModule}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                >
                  Опубликовать
                </button>
              )}
              {(module.status === 'archived' || module.status === 'published') && (
                <button
                  onClick={handleRestoreToDraft}
                  className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
                >
                  В черновик
                </button>
              )}
              {(module.status === 'draft' || module.status === 'published') && (
                <button
                  onClick={handleArchiveModule}
                  className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                >
                  В архив
                </button>
              )}
              <Link
                to={`/tests/create?module_id=${id}`}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                + Создать тест
              </Link>
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
            </>
          )}
        </div>
      </div>

      {/* Назначения */}
      {canManage && (
        <div className="mt-6 bg-white p-6 rounded-lg shadow">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">Назначения ({assignments.length})</h2>
            {module.status === 'published' && (
              <button
                onClick={handleOpenAssignModal}
                className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 text-sm"
              >
                Назначить пользователей
              </button>
            )}
          </div>
          {assignments.length === 0 ? (
            <p className="text-gray-500 text-sm">Нет назначенных пользователей</p>
          ) : (
            <div className="space-y-2">
              {assignments.map((a) => {
                const assignedUser = users.find((u) => u.id === a.user_id);
                return (
                  <div key={a.id} className="flex justify-between items-center border-b border-gray-100 py-2">
                    <span className="text-sm text-gray-700">
                      {assignedUser ? `${assignedUser.full_name || assignedUser.email} (${assignedUser.role})` : a.user_id}
                    </span>
                    <button
                      onClick={() => handleUnassign(a.user_id)}
                      className="text-red-600 hover:text-red-800 text-xs"
                    >
                      Отозвать
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Assign Modal */}
      {showAssignModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-lg w-full max-h-[80vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Назначить пользователей</h3>
            {availableUsers.length === 0 ? (
              <p className="text-gray-500">Нет доступных пользователей</p>
            ) : (
              <div className="space-y-2 mb-4">
                <div className="flex gap-2 mb-2">
                  <button
                    onClick={selectAllAvailable}
                    className="text-xs text-indigo-600 hover:underline"
                  >
                    Выбрать всех
                  </button>
                  <button
                    onClick={() => setSelectedUserIds(new Set())}
                    className="text-xs text-gray-600 hover:underline"
                  >
                    Снять выделение
                  </button>
                </div>
                {availableUsers.map((u) => (
                  <label key={u.id} className="flex items-center gap-2 py-1 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedUserIds.has(u.id)}
                      onChange={() => toggleUserSelection(u.id)}
                      className="rounded"
                    />
                    <span className="text-sm">
                      {u.full_name || u.email} ({u.role})
                    </span>
                  </label>
                ))}
              </div>
            )}
            <div className="flex gap-2">
              <button
                onClick={handleAssign}
                disabled={assignLoading || selectedUserIds.size === 0}
                className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50 text-sm"
              >
                {assignLoading ? 'Сохранение...' : 'Назначить выбранным'}
              </button>
              <button
                onClick={() => setShowAssignModal(false)}
                className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50 text-sm"
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Уроки */}
      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-4">Материалы ({lessons.length})</h2>
        <div className="space-y-2">
          {lessons.map((lesson) => (
            <Link
              key={lesson.id}
              to={`/modules/${id}/lessons/${lesson.id}`}
              className="block bg-white p-4 rounded shadow hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-gray-400 text-sm">#{lesson.order_index}</span>
                  <span className="font-medium">{lesson.title}</span>
                </div>
                <span className="text-indigo-600 text-sm">Открыть →</span>
              </div>
            </Link>
          ))}
        </div>

        {canManage && (
          !showLessonForm ? (
            <button
              onClick={() => setShowLessonForm(true)}
              className="mt-4 px-4 py-2 border border-indigo-600 text-indigo-600 rounded hover:bg-indigo-50"
            >
              + Добавить материал
            </button>
          ) : (
            <form onSubmit={handleCreateLesson} className="mt-4 bg-white p-6 rounded-lg shadow border border-gray-200 max-w-2xl">
              <h3 className="text-lg font-semibold mb-4">Новый материал</h3>
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
                  <label className="block text-sm font-medium text-gray-700">Ссылка на презентацию (R7 URI)</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={lessonR7Uri}
                      onChange={(e) => setLessonR7Uri(e.target.value)}
                      placeholder="https://..."
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
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
          )
        )}
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
                      {!h.is_approved && canModerate() && (
                        <button
                          onClick={() => handleApproveHeuristic(h.id)}
                          className="text-xs text-indigo-600 hover:underline"
                        >
                          Одобрить
                        </button>
                      )}
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

      {/* Тесты */}
      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-4">Тесты ({tests.length})</h2>
        {tests.length === 0 ? (
          <p className="text-gray-500 text-sm">Нет тестов для этого модуля</p>
        ) : (
          <div className="space-y-4">
            {tests.map((test) => (
              <div key={test.id} className="bg-white p-4 rounded shadow flex justify-between items-center">
                <div>
                  <h3 className="font-semibold text-gray-900">{test.title}</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Вопросов: {test.question_count} | Проходной: {test.pass_score}%
                  </p>
                  <span className={`inline-block mt-1 px-2 py-0.5 rounded text-xs ${test.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                    {test.is_active ? 'Активен' : 'Неактивен'}
                  </span>
                </div>
                <div className="flex gap-2">
                  {hasRole(['admin', 'methodist']) && canManage && (
                    <>
                      <button
                        onClick={() => navigate(`/tests/${test.id}/edit`)}
                        className="px-3 py-1.5 text-sm text-indigo-600 border border-indigo-600 rounded hover:bg-indigo-50"
                      >
                        Редактировать
                      </button>
                      <button
                        onClick={() => navigate(`/tests/${test.id}/attempts`)}
                        className="px-3 py-1.5 text-sm text-gray-700 border border-gray-300 rounded hover:bg-gray-50"
                      >
                        Результаты
                      </button>
                    </>
                  )}
                  {hasRole(['methodist', 'seminarist', 'candidate']) && test.is_active && (
                    <button
                      onClick={() => navigate(`/tests/${test.id}/take`)}
                      className="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700"
                    >
                      Пройти тест
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
