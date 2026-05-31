import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { contentApi } from '../api/client';

export function ModuleCreatePage() {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const res = await contentApi.post('/modules', { title, description });
      navigate(`/modules/${res.data.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка создания модуля');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <button
        type="button"
        onClick={() => navigate('/modules')}
        className="text-sm text-gray-500 hover:text-gray-700 mb-2"
      >
        ← Назад
      </button>
      <h1 className="text-2xl font-bold mb-6">Создание модуля</h1>
      
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
            {saving ? 'Создание...' : 'Создать'}
          </button>
          
          <button
            type="button"
            onClick={() => navigate('/modules')}
            className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
          >
            Отмена
          </button>
        </div>
      </form>
    </div>
  );
}
