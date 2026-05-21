import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getTest, updateTest, getQuestions, createQuestion, updateQuestion,
  reorderQuestion, deleteQuestion,
} from '../api/assessment';
import { QuestionEditor } from '../components/tests/QuestionEditor';
import { QuestionList } from '../components/tests/QuestionList';
import { LoadingSpinner } from '../components/LoadingSpinner';
import type { Test, Question } from '../types';

type Tab = 'general' | 'questions';

export function TestEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [test, setTest] = useState<Test | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [tab, setTab] = useState<Tab>('general');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [passScore, setPassScore] = useState(70);
  const [isActive, setIsActive] = useState(true);

  const [editingQuestion, setEditingQuestion] = useState<Question | null>(null);
  const [showEditor, setShowEditor] = useState(false);

  useEffect(() => {
    if (id) fetchData();
  }, [id]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [testRes, qRes] = await Promise.all([
        getTest(id!),
        getQuestions(id!),
      ]);
      const t = testRes.data;
      setTest(t);
      setTitle(t.title);
      setDescription(t.description || '');
      setPassScore(t.pass_score);
      setIsActive(t.is_active);
      setQuestions(qRes.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка загрузки');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveGeneral = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await updateTest(id!, { title, description, pass_score: passScore, is_active: isActive });
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveQuestion = async (data: {
    text: string;
    qtype: 'single' | 'multiple';
    options: { id: string; text: string; is_correct: boolean }[];
  }) => {
    setError('');
    try {
      if (editingQuestion) {
        await updateQuestion(editingQuestion.id, data);
      } else {
        await createQuestion(id!, data);
      }
      setShowEditor(false);
      setEditingQuestion(null);
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка сохранения вопроса');
    }
  };

  const handleReorder = async (newQuestions: Question[]) => {
    setQuestions(newQuestions);
    for (let i = 0; i < newQuestions.length; i++) {
      const q = newQuestions[i];
      if (q.order_index !== i) {
        try {
          await reorderQuestion(q.id, i);
        } catch (err: any) {
          console.error('Reorder failed', err);
        }
      }
    }
    fetchData();
  };

  const handleDeleteQuestion = async (questionId: string) => {
    if (!window.confirm('Удалить вопрос?')) return;
    try {
      await deleteQuestion(questionId);
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка удаления');
    }
  };

  if (loading) return <LoadingSpinner />;
  if (!test) return <div className="text-red-600 py-8">{error || 'Тест не найден'}</div>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Редактирование теста</h1>
      {error && <div className="bg-red-50 text-red-700 p-3 rounded mb-4">{error}</div>}

      <div className="border-b border-gray-200 mb-6">
        <nav className="flex gap-4">
          <button
            onClick={() => setTab('general')}
            className={`pb-2 px-1 border-b-2 font-medium text-sm ${tab === 'general' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
          >
            Основное
          </button>
          <button
            onClick={() => setTab('questions')}
            className={`pb-2 px-1 border-b-2 font-medium text-sm ${tab === 'questions' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
          >
            Вопросы ({questions.length})
          </button>
        </nav>
      </div>

      {tab === 'general' && (
        <form onSubmit={handleSaveGeneral} className="max-w-2xl space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700">Название</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Описание</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Проходной балл: {passScore}%</label>
            <input
              type="range"
              min={0}
              max={100}
              value={passScore}
              onChange={(e) => setPassScore(Number(e.target.value))}
              className="mt-1 block w-full"
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
            />
            <label htmlFor="is_active" className="text-sm font-medium text-gray-700">Активен</label>
          </div>
          <div className="flex gap-4">
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
            >
              {saving ? 'Сохранение...' : 'Сохранить'}
            </button>
            <button
              type="button"
              onClick={() => navigate('/tests')}
              className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
            >
              Назад к списку
            </button>
          </div>
        </form>
      )}

      {tab === 'questions' && (
        <div>
          {!showEditor && (
            <button
              onClick={() => { setEditingQuestion(null); setShowEditor(true); }}
              className="mb-4 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
            >
              + Добавить вопрос
            </button>
          )}
          {showEditor && (
            <QuestionEditor
              question={editingQuestion}
              onSave={handleSaveQuestion}
              onCancel={() => { setShowEditor(false); setEditingQuestion(null); }}
            />
          )}
          <QuestionList
            questions={questions}
            onReorder={handleReorder}
            onEdit={(q) => { setEditingQuestion(q); setShowEditor(true); }}
            onDelete={handleDeleteQuestion}
          />
        </div>
      )}
    </div>
  );
}
