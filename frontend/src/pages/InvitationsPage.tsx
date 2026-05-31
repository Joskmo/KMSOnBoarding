import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import type { Invitation, User } from '../types';

function CopyIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12"></polyline>
    </svg>
  );
}

export function InvitationsPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');
  const [createError, setCreateError] = useState('');
  const [lastCreatedToken, setLastCreatedToken] = useState('');
  const [copiedToken, setCopiedToken] = useState<string | null>(null);

  // Form state
  const [roleName, setRoleName] = useState('candidate');
  const [email, setEmail] = useState('');
  const [managerId, setManagerId] = useState(user?.id || '');

  useEffect(() => {
    fetchInvitations();
    fetchUsers();
  }, []);

  const fetchInvitations = async () => {
    setLoading(true);
    try {
      const res = await authApi.get('/invitations');
      setInvitations(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка загрузки приглашений');
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

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setCreateError('');
    setLastCreatedToken('');
    try {
      const payload: any = { role_name: roleName };
      if (email.trim()) payload.email = email.trim();
      if (managerId) payload.manager_id = managerId;
      const res = await authApi.post('/invitations', payload);
      setLastCreatedToken(res.data.token);
      setEmail('');
      fetchInvitations();
    } catch (err: any) {
      setCreateError(err.response?.data?.detail || 'Ошибка создания приглашения');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (invId: string) => {
    if (!window.confirm('Удалить приглашение?')) return;
    try {
      await authApi.delete(`/invitations/${invId}`);
      fetchInvitations();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка удаления');
    }
  };

  const copyInvitationLink = (token: string) => {
    const link = `${window.location.origin}/register?token=${token}`;
    navigator.clipboard.writeText(link).then(() => {
      setCopiedToken(token);
      setTimeout(() => setCopiedToken(null), 2000);
    });
  };

  const roleLabel = (role: string) => {
    const map: Record<string, string> = {
      admin: 'Админ',
      methodist: 'Методист',
      seminarist: 'Семинарист',
      candidate: 'Кандидат',
    };
    return map[role] || role;
  };

  const managers = users.filter((u) => u.role === 'admin' || u.role === 'methodist');
  const isAdmin = user?.role === 'admin';

  const inviteLink = lastCreatedToken
    ? `${window.location.origin}/register?token=${lastCreatedToken}`
    : '';

  return (
    <div>
      <button
        type="button"
        onClick={() => navigate('/modules')}
        className="text-sm text-gray-500 hover:text-gray-700 mb-2"
      >
        ← Назад
      </button>
      <h1 className="text-2xl font-bold mb-6">Приглашения и регистрация</h1>

      {/* Create invitation form */}
      <div className="bg-white p-6 rounded-lg shadow mb-8">
        <h2 className="text-lg font-semibold mb-4">Создать приглашение</h2>
        
        {createError && (
          <div className="bg-red-50 text-red-700 p-3 rounded mb-4">{createError}</div>
        )}
        {lastCreatedToken && (
          <div className="bg-green-50 border border-green-200 text-green-800 p-4 rounded mb-4">
            <p className="text-sm font-medium mb-2">Приглашение создано!</p>
            <div className="flex items-center gap-2 flex-wrap">
              <a
                href={inviteLink}
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-600 hover:underline break-all text-sm"
              >
                {inviteLink}
              </a>
              <button
                onClick={() => copyInvitationLink(lastCreatedToken)}
                className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50 transition"
                title="Скопировать ссылку"
              >
                {copiedToken === lastCreatedToken ? (
                  <>
                    <CheckIcon />
                    <span className="text-green-600">Скопировано!</span>
                  </>
                ) : (
                  <>
                    <CopyIcon />
                    <span>Скопировать</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        <form onSubmit={handleCreate} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Роль</label>
              <select
                value={roleName}
                onChange={(e) => setRoleName(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="candidate">Кандидат</option>
                <option value="seminarist">Семинарист</option>
                {isAdmin && <option value="methodist">Методист</option>}
                {isAdmin && <option value="admin">Админ</option>}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Email (опционально)</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@example.com"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Менеджер</label>
              <select
                value={managerId || user?.id || ''}
                onChange={(e) => setManagerId(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value={user?.id || ''}>
                  {user?.full_name || user?.email} (Вы)
                </option>
                {managers
                  .filter((m) => m.id !== user?.id)
                  .map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.full_name || m.email}
                    </option>
                  ))}
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={creating}
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
          >
            {creating ? 'Создание...' : 'Создать приглашение'}
          </button>
        </form>
      </div>

      {/* Invitations list */}
      <h2 className="text-lg font-semibold mb-4">Список приглашений</h2>

      {error && (
        <div className="bg-red-50 text-red-700 p-3 rounded mb-4">{error}</div>
      )}

      {loading ? (
        <div className="text-center py-8">Загрузка...</div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Токен</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Роль</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Статус</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Истекает</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Действия</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {invitations.map((inv) => (
                <tr key={inv.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                    {inv.token.slice(0, 16)}...
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {roleLabel(inv.role_name)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {inv.email || '—'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {inv.used ? (
                      <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">Использован</span>
                    ) : new Date(inv.expires_at) < new Date() ? (
                      <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs">Истёк</span>
                    ) : (
                      <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">Активен</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(inv.expires_at).toLocaleDateString('ru-RU')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    {!inv.used && new Date(inv.expires_at) >= new Date() && (
                      <div className="flex flex-col gap-1 items-end">
                        <button
                          onClick={() => copyInvitationLink(inv.token)}
                          className="text-indigo-600 hover:text-indigo-900"
                        >
                          {copiedToken === inv.token ? 'Скопировано!' : 'Скопировать ссылку на приглашение'}
                        </button>
                        <button
                          onClick={() => handleDelete(inv.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Удалить
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {invitations.length === 0 && (
            <div className="text-center py-8 text-gray-500">Нет приглашений</div>
          )}
        </div>
      )}
    </div>
  );
}
