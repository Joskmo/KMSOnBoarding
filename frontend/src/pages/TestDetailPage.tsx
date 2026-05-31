import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getTest, getQuestions } from '../api/assessment';
import { LoadingSpinner } from '../components/LoadingSpinner';
import type { Test, Question } from '../types';

export function TestDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { hasRole } = useAuth();
  const [test, setTest] = useState<Test | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const isManager = hasRole(['admin', 'methodist']);

  useEffect(() => {
    const fetchTest = async () => {
      try {
        const [testRes, qRes] = await Promise.all([
          getTest(id!),
          getQuestions(id!),
        ]);
        setTest(testRes.data);
        setQuestions(qRes.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Ошибка загрузки');
      } finally {
        setLoading(false);
      }
    };
    if (id) fetchTest();
  }, [id]);

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="text-red-600 py-8">{error}</div>;
  if (!test) return <div>Тест не найден</div>;

  return (
    <div>
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-3xl font-bold">{test.title}</h1>
          <p className="text-gray-600 mt-2">{test.description}</p>
          <div className="mt-3 flex gap-3 text-sm">
            <span className={`px-2 py-1 rounded ${test.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
              {test.is_active ? 'Активен' : 'Неактивен'}
            </span>
            <span className="text-gray-500">Вопросов: {test.question_count}</span>
            <span className="text-gray-500">Проходной: {test.pass_score}%</span>
          </div>
        </div>
        <div className="flex gap-2">
          {isManager && (
            <>
              <Link
                to={`/tests/${test.id}/edit`}
                className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
              >
                Редактировать
              </Link>
              <Link
                to={`/tests/${test.id}/attempts`}
                className="px-4 py-2 bg-white border border-gray-300 rounded hover:bg-gray-50"
              >
                Результаты
              </Link>
            </>
          )}
          {hasRole(['seminarist', 'candidate']) && (
            <button
              onClick={() => navigate(`/tests/${test.id}/take`)}
              className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
            >
              Начать тест
            </button>
          )}
        </div>
      </div>

      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-4">Вопросы ({questions.length})</h2>
        <div className="space-y-4">
          {questions.map((q, index) => (
            <div key={q.id} className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-start gap-3">
                <span className="text-gray-400 font-mono text-sm mt-0.5">{index + 1}.</span>
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{q.text}</p>
                  <p className="text-sm text-gray-500 mt-1">
                    {q.qtype === 'single' ? 'Одиночный выбор' : 'Множественный выбор'} | {q.options.length} вариантов
                  </p>
                  <div className="mt-3 space-y-2">
                    {q.options.map((opt) => (
                      <div
                        key={opt.id}
                        className={`flex items-center gap-2 px-3 py-2 rounded text-sm ${
                          isManager && opt.is_correct
                            ? 'bg-green-50 text-green-800 border border-green-200'
                            : 'bg-gray-50 text-gray-700'
                        }`}
                      >
                        <span className="font-mono text-gray-400">{opt.id})</span>
                        <span>{opt.text}</span>
                        {isManager && opt.is_correct && (
                          <span className="text-xs bg-green-200 text-green-800 px-1.5 py-0.5 rounded ml-auto">
                            Правильный
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
          {questions.length === 0 && (
            <div className="text-center py-8 text-gray-500">Нет вопросов</div>
          )}
        </div>
      </div>
    </div>
  );
}
