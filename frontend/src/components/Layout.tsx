import { Outlet, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { HeaderDropdown } from './HeaderDropdown';

export function Layout() {
  const { user, isAuthenticated } = useAuth();

  const isAdmin = user?.role === 'admin';
  const isMethodist = user?.role === 'methodist';
  const canManageUsers = isAdmin || isMethodist;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-6">
            <Link to="/modules" className="text-xl font-bold text-indigo-600">
              KMS Content
            </Link>
            
            {isAuthenticated && (
              <nav className="hidden md:flex gap-4 text-sm">
                <Link to="/modules" className="text-gray-600 hover:text-indigo-600">
                  Модули
                </Link>
                <Link to="/tests" className="text-gray-600 hover:text-indigo-600">
                  Тесты
                </Link>
                {canManageUsers && (
                  <>
                    <Link to="/users" className="text-gray-600 hover:text-indigo-600">
                      Пользователи
                    </Link>
                    <Link to="/invitations" className="text-gray-600 hover:text-indigo-600">
                      Приглашения
                    </Link>
                  </>
                )}
              </nav>
            )}
          </div>
          
          {isAuthenticated && user && (
            <HeaderDropdown />
          )}
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
