import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { startAttempt, submitAttempt } from '../api/assessment';
import { LoadingSpinner } from '../components/LoadingSpinner';
import type { AttemptStart } from '../types';

export function TestTakePage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [attemptData, setAttemptData] = useState<AttemptStart | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string[]>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<{ score: number; is_passed: boolean } | null>(null);

  useEffect(() => {
    const startTest = async () => {
      setLoading(true);
      try {
        const res = await startAttempt(id!);
        setAttemptData(res.data);
        const init: Record<string, string[]> = {};
        res.data.questions.forEach((q) => { init[q.id] = []; });
        setAnswers(init);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Ошибка запуска теста');
      } finally {
        setLoading(false);
      }
    };
    if (id) startTest();
  }, [id]);

  const handleSelect = (questionId: string, optionId: string, qtype: 'single' | 'multiple') => {
    setAnswers((prev) => {
      const current = prev[questionId] || [];
      if (qtype === 'single') {
        return { ...prev, [questionId]: [optionId] };
      } else {
        const has = current.includes(optionId);
        const next = has ? current.filter((c) => c !== optionId) : [...current, optionId];
        return { ...prev, [questionId]: next };
      }
    });
  };

  const handleSubmit = async () => {
    if (attemptData) {
      const unanswered = attemptData.questions.filter((q) => !answers[q.id]?.length);
      if (unanswered.length > 0) {
        setError(`Ответьте на все вопросы. Пропущено: ${unanswered.length}`);
        return;
      }
    }

    setSubmitting(true);
    setError('');
    try {
      const res = await submitAttempt({ test_id: id!, answers });
      setResult({ score: res.data.score, is_passed: res.data.is_passed });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка отправки ответов');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error && !attemptData) return <div className="text-red-600 py-8">{error}</div>;
  if (!attemptData) return <div>Не удалось загрузить тест</div>;
  if (attemptData.questions.length === 0) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <h2 className="text-2xl font-bold mb-4 text-gray-800">{attemptData.title}</h2>
        <p className="text-gray-600 mb-8">В тесте пока нет вопросов. Попробуйте позже.</p>
        <button
          onClick={() => navigate('/tests')}
          className="px-6 py-3 bg-indigo-600 text-white rounded hover:bg-indigo-700"
        >
          К списку тестов
        </button>
      </div>
    );
  }

  // Result screen
  if (result) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <h2 className="text-3xl font-bold mb-4">Тест завершен!</h2>
        <div className={`text-6xl font-bold mb-4 ${result.is_passed ? 'text-green-600' : 'text-red-600'}`}>
          {result.score}%
        </div>
        <p className={`text-xl mb-8 ${result.is_passed ? 'text-green-700' : 'text-red-700'}`}>
          {result.is_passed ? 'Пройден' : 'Не пройден'}
        </p>
        <p className="text-gray-600 mb-8">
          Проходной балл: {attemptData.pass_score}%
        </p>
        <div className="flex justify-center gap-4">
          <button
            onClick={() => navigate('/attempts/my')}
            className="px-6 py-3 bg-indigo-600 text-white rounded hover:bg-indigo-700"
          >
            Мои попытки
          </button>
          <button
            onClick={() => navigate('/tests')}
            className="px-6 py-3 border border-gray-300 rounded hover:bg-gray-50"
          >
            К списку тестов
          </button>
        </div>
      </div>
    );
  }

  const question = attemptData.questions[currentIndex];
  const progress = ((currentIndex + 1) / attemptData.questions.length) * 100;
  const selected = answers[question.id] || [];

  return (
    <div className="max-w-3xl mx-auto">
      {/* Progress bar */}
      <div className="mb-6">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>Вопрос {currentIndex + 1} из {attemptData.questions.length}</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      </div>

      {error && <div className="bg-red-50 text-red-700 p-3 rounded mb-4">{error}</div>}

      <div className="bg-white p-8 rounded-lg shadow mb-6">
        <h2 className="text-xl font-semibold mb-6">{question.text}</h2>
        <div className="space-y-3">
          {question.options.map((opt) => {
            const isSelected = selected.includes(opt.id);
            return (
              <label
                key={opt.id}
                className={`flex items-center p-4 rounded-lg border cursor-pointer transition ${
                  isSelected
                    ? 'border-indigo-600 bg-indigo-50'
                    : 'border-gray-200 hover:bg-gray-50'
                }`}
              >
                <input
                  type={question.qtype === 'single' ? 'radio' : 'checkbox'}
                  name={`q-${question.id}`}
                  checked={isSelected}
                  onChange={() => handleSelect(question.id, opt.id, question.qtype)}
                  className="h-5 w-5 text-indigo-600"
                />
                <span className="ml-3 text-gray-800">{opt.text}</span>
              </label>
            );
          })}
        </div>
      </div>

      <div className="flex justify-between">
        <button
          onClick={() => setCurrentIndex((i) => Math.max(0, i - 1))}
          disabled={currentIndex === 0}
          className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
        >
          ← Назад
        </button>

        {currentIndex < attemptData.questions.length - 1 ? (
          <button
            onClick={() => setCurrentIndex((i) => i + 1)}
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
          >
            Далее →
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
          >
            {submitting ? 'Отправка...' : 'Завершить тест'}
          </button>
        )}
      </div>
    </div>
  );
}
