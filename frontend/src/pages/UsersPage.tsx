import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { authApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import type { User } from '../types';

export function UsersPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [activeTab, setActiveTab] = useState<'all' | 'subordinates'>('all');

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await authApi.get('/users');
      setUsers(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка загрузки пользователей');
    } finally {
      setLoading(false);
    }
  };

  const allUsers = users.filter((u) => {
    if (!roleFilter) return true;
    return u.role === roleFilter;
  });

  const subordinates = users.filter((u) => u.manager_id === currentUser?.id);

  const displayedUsers = activeTab === 'all' ? allUsers : subordinates;

  const roleLabel = (role: string) => {
    const map: Record<string, string> = {
      admin: 'Админ',
      methodist: 'Методист',
      seminarist: 'Семинарист',
      candidate: 'Кандидат',
    };
    return map[role] || role;
  };

  const roleColor = (role: string) => {
    const map: Record<string, string> = {
      admin: 'bg-red-100 text-red-800',
      methodist: 'bg-blue-100 text-blue-800',
      seminarist: 'bg-green-100 text-green-800',
      candidate: 'bg-gray-100 text-gray-800',
    };
    return map[role] || 'bg-gray-100 text-gray-800';
  };

  const canEditUser = (user: User) => {
    if (!currentUser) return false;
    if (currentUser.id === user.id) return false; // edit yourself in Profile
    if (currentUser.role === 'admin') return true;
    if (currentUser.role === 'methodist' && user.manager_id === currentUser.id) return true;
    return false;
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Пользователи</h1>
      </div>

      {/* Tabs */}
      <div className="mb-4 border-b border-gray-200">
        <nav className="flex gap-6">
          <button
            onClick={() => setActiveTab('all')}
            className={`pb-2 text-sm font-medium border-b-2 transition ${
              activeTab === 'all'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Все пользователи
          </button>
          <button
            onClick={() => setActiveTab('subordinates')}
            className={`pb-2 text-sm font-medium border-b-2 transition ${
              activeTab === 'subordinates'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Мои подчиненные {subordinates.length > 0 && `(${subordinates.length})`}
          </button>
        </nav>
      </div>

      {activeTab === 'all' && (
        <div className="mb-4 flex gap-4">
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded"
          >
            <option value="">Все роли</option>
            <option value="admin">Админ</option>
            <option value="methodist">Методист</option>
            <option value="seminarist">Семинарист</option>
            <option value="candidate">Кандидат</option>
          </select>
        </div>
      )}

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
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Имя</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Роль</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Менеджер</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Действия</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {displayedUsers.map((user) => (
                <tr key={user.id} className={`hover:bg-gray-50 ${user.id === currentUser?.id ? 'bg-indigo-50' : ''}`}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {user.full_name || '—'}
                    {user.id === currentUser?.id && (
                      <span className="ml-2 text-xs text-indigo-600 font-semibold">(Вы)</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{user.email}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 rounded text-xs ${roleColor(user.role)}`}>
                      {roleLabel(user.role)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {(() => {
                      const manager = users.find((u) => u.id === user.manager_id);
                      return manager ? (manager.full_name || manager.email) : '—';
                    })()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    {canEditUser(user) && (
                      <Link
                        to={`/users/${user.id}/edit`}
                        className="text-indigo-600 hover:text-indigo-900"
                      >
                        Редактировать
                      </Link>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {displayedUsers.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              {activeTab === 'subordinates' ? 'Нет подчиненных' : 'Нет пользователей'}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
