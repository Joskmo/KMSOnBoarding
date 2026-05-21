import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { authApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import type { User } from '../types';

function validateEmail(email: string): boolean {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

export function UserEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user: currentUser } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [managerId, setManagerId] = useState('');
  const [targetUser, setTargetUser] = useState<User | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [resetPasswordLoading, setResetPasswordLoading] = useState(false);
  const [resetPasswordResult, setResetPasswordResult] = useState('');

  useEffect(() => {
    if (id) {
      fetchUser();
      fetchUsers();
    }
  }, [id]);

  const fetchUser = async () => {
    try {
      const res = await authApi.get<User>(`/users/${id}`);
      setTargetUser(res.data);
      setFullName(res.data.full_name || '');
      setEmail(res.data.email || '');
      const currentManagerId = res.data.manager_id || '';
      setManagerId(currentManagerId === id ? '' : currentManagerId);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка загрузки пользователя');
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const res = await authApi.get('/users');
      setUsers(res.data);
    } catch {
      // ignore
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const payload: any = {};
      if (canEditFullName && fullName) {
        payload.full_name = fullName;
      }
      if (canEditEmail) {
        payload.email = email || null;
      }
      if (canEditManager) {
        if (managerId && managerId !== id) {
          payload.manager_id = managerId;
        } else {
          payload.manager_id = null;
        }
      }
      await authApi.put(`/users/${id}`, payload);
      navigate('/users');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  const handleResetPassword = async () => {
    if (!window.confirm('Сбросить пароль пользователя? Будет сгенерирован новый случайный пароль.')) {
      return;
    }
    setResetPasswordLoading(true);
    setResetPasswordResult('');
    setError('');
    try {
      const res = await authApi.post(`/users/${id}/reset-password`);
      setResetPasswordResult(res.data.new_password);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка сброса пароля');
    } finally {
      setResetPasswordLoading(false);
    }
  };

  const managers = users.filter((u) => (u.role === 'admin' || u.role === 'methodist') && u.id !== id);

  // Permission checks
  const isAdmin = currentUser?.role === 'admin';
  const isSelf = currentUser?.id === id;
  const isSubordinate = targetUser?.manager_id === currentUser?.id;
  const canEditFullName = isAdmin || isSelf;
  const canEditEmail = isAdmin;
  const canEditManager = isAdmin || (currentUser?.role === 'methodist' && isSubordinate);
  const canResetPassword = isAdmin;

  if (loading) return <div className="text-center py-8">Загрузка...</div>;

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">Редактирование пользователя</h1>
      
      {error && (
        <div className="bg-red-50 text-red-700 p-3 rounded mb-4">{error}</div>
      )}

      {resetPasswordResult && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 p-4 rounded mb-4">
          <p className="text-sm font-medium mb-2">Пароль успешно сброшен!</p>
          <div className="flex items-center gap-2">
            <code className="bg-white px-3 py-1.5 rounded border border-yellow-300 text-sm font-mono">
              {resetPasswordResult}
            </code>
            <button
              onClick={() => {
                navigator.clipboard.writeText(resetPasswordResult);
              }}
              className="text-xs text-indigo-600 hover:text-indigo-800"
            >
              Скопировать
            </button>
          </div>
          <p className="mt-2 text-xs text-yellow-700">
            Сохраните этот пароль — он больше не будет показан. Пользователь сможет сменить его в профиле.
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {canEditFullName && (
          <div>
            <label className="block text-sm font-medium text-gray-700">Полное имя</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
        )}

        {canEditEmail && (
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={`mt-1 block w-full px-3 py-2 border rounded-md ${
                email && !validateEmail(email)
                  ? 'border-red-500 bg-red-50'
                  : 'border-gray-300'
              }`}
              placeholder="user@example.com"
            />
            {email && !validateEmail(email) && (
              <p className="mt-1 text-xs text-red-600">Введите корректный email</p>
            )}
          </div>
        )}

        {canEditManager && (
          <div>
            <label className="block text-sm font-medium text-gray-700">Менеджер</label>
            <select
              value={managerId}
              onChange={(e) => setManagerId(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="">— Нет менеджера —</option>
              {managers.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.full_name || m.email} ({m.role})
                </option>
              ))}
            </select>
            <p className="mt-1 text-xs text-gray-500">
              Выберите админа или методиста в качестве менеджера.
            </p>
          </div>
        )}

        <div className="flex gap-4">
          <button
            type="submit"
            disabled={saving || (email !== '' && !validateEmail(email))}
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
          >
            {saving ? 'Сохранение...' : 'Сохранить'}
          </button>
          
          {canResetPassword && (
            <button
              type="button"
              onClick={handleResetPassword}
              disabled={resetPasswordLoading}
              className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:opacity-50"
            >
              {resetPasswordLoading ? 'Сброс...' : 'Сбросить пароль'}
            </button>
          )}
          
          <button
            type="button"
            onClick={() => navigate('/users')}
            className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
          >
            Отмена
          </button>
        </div>
      </form>
    </div>
  );
}
