import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { contentApi } from '../api/client';
import type { Module } from '../types';

export function ModuleEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const fetchModule = useCallback(async () => {
    try {
      const res = await contentApi.get<Module>(`/modules/${id}`);
      setTitle(res.data.title);
      setDescription(res.data.description || '');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка загрузки');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (id) fetchModule();
  }, [id, fetchModule]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await contentApi.patch(`/modules/${id}`, { title, description });
      navigate(`/modules/${id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="text-center py-8">Загрузка...</div>;

  return (
    <div className="max-w-2xl">
      <button
        type="button"
        onClick={() => navigate(`/modules/${id}`)}
        className="text-sm text-gray-500 hover:text-gray-700 mb-2"
      >
        ← Назад
      </button>
      <h1 className="text-2xl font-bold mb-6">Редактирование модуля</h1>
      
      {error && (
        <div className="bg-red-50 text-red-700 p-3 rounded mb-4">{error}</div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
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
            rows={4}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
          />
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
            onClick={() => navigate(`/modules/${id}`)}
            className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
          >
            Отмена
          </button>
        </div>
      </form>
    </div>
  );
}
