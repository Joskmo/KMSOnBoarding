import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { contentApi } from '../api/client';
import { createTest } from '../api/assessment';
import type { Module } from '../types';

export function TestCreatePage() {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [moduleId, setModuleId] = useState('');
  const [passScore, setPassScore] = useState(70);
  const [modules, setModules] = useState<Module[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    fetchModules();
  }, []);

  const fetchModules = async () => {
    try {
      const res = await contentApi.get('/modules?page=1&size=100');
      setModules(res.data.items || []);
    } catch (err: any) {
      setError('Не удалось загрузить список модулей');
    }
  };

  const validate = () => {
    const errors: Record<string, string> = {};
    if (!title.trim()) errors.title = 'Название обязательно';
    if (!moduleId) errors.module_id = 'Выберите модуль';
    if (passScore < 0 || passScore > 100) errors.pass_score = 'От 0 до 100';
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setSaving(true);
    setError('');
    try {
      const res = await createTest({
        module_id: moduleId,
        title,
        description: description || undefined,
        pass_score: passScore,
      });
      navigate(`/tests/${res.data.id}/edit`);
    } catch (err: any) {
      if (err.response?.status === 422) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          const msgs = detail.map((d: any) => `${d.loc?.join('.')}: ${d.msg}`).join('; ');
          setError(`Ошибка валидации: ${msgs}`);
        } else {
          setError(detail || 'Ошибка валидации');
        }
      } else {
        setError(err.response?.data?.detail || 'Ошибка создания теста');
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">Создание теста</h1>
      {error && <div className="bg-red-50 text-red-700 p-3 rounded mb-4">{error}</div>}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700">Название *</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
          />
          {fieldErrors.title && <p className="text-red-600 text-sm mt-1">{fieldErrors.title}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Модуль *</label>
          <select
            value={moduleId}
            onChange={(e) => setModuleId(e.target.value)}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="">Выберите модуль</option>
            {modules.map((m) => (
              <option key={m.id} value={m.id}>{m.title}</option>
            ))}
          </select>
          {fieldErrors.module_id && <p className="text-red-600 text-sm mt-1">{fieldErrors.module_id}</p>}
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
          <label className="block text-sm font-medium text-gray-700">
            Проходной балл: {passScore}%
          </label>
          <input
            type="range"
            min={0}
            max={100}
            value={passScore}
            onChange={(e) => setPassScore(Number(e.target.value))}
            className="mt-1 block w-full"
          />
          {fieldErrors.pass_score && <p className="text-red-600 text-sm mt-1">{fieldErrors.pass_score}</p>}
        </div>

        <div className="flex gap-4">
          <button
            type="submit"
            disabled={saving}
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
          >
            {saving ? 'Создание...' : 'Создать тест'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/tests')}
            className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
          >
            Отмена
          </button>
        </div>
      </form>
    </div>
  );
}
