import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getTest } from '../api/assessment';
import { LoadingSpinner } from '../components/LoadingSpinner';
import type { Test } from '../types';

export function TestDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { hasRole } = useAuth();
  const [test, setTest] = useState<Test | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const isManager = hasRole(['admin', 'methodist']);

  useEffect(() => {
    const fetchTest = async () => {
      try {
        const res = await getTest(id!);
        setTest(res.data);
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
    </div>
  );
}
