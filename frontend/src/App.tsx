import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { Layout } from './components/Layout';
import { PrivateRoute } from './components/PrivateRoute';
import { RoleGuard } from './components/RoleGuard';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { ModulesPage } from './pages/ModulesPage';
import { ModuleDetailPage } from './pages/ModuleDetailPage';
import { ModuleCreatePage } from './pages/ModuleCreatePage';
import { ModuleEditPage } from './pages/ModuleEditPage';
import { UsersPage } from './pages/UsersPage';
import { UserEditPage } from './pages/UserEditPage';
import { InvitationsPage } from './pages/InvitationsPage';
import { ProfilePage } from './pages/ProfilePage';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/modules" replace />} />
            <Route path="modules" element={<PrivateRoute><ModulesPage /></PrivateRoute>} />
            <Route path="modules/:id" element={<PrivateRoute><ModuleDetailPage /></PrivateRoute>} />
            <Route path="modules/new" element={<PrivateRoute><ModuleCreatePage /></PrivateRoute>} />
            <Route path="modules/:id/edit" element={<PrivateRoute><ModuleEditPage /></PrivateRoute>} />
            <Route path="users" element={<PrivateRoute><RoleGuard allowedRoles={['admin', 'methodist']}><UsersPage /></RoleGuard></PrivateRoute>} />
            <Route path="users/:id/edit" element={<PrivateRoute><RoleGuard allowedRoles={['admin', 'methodist']}><UserEditPage /></RoleGuard></PrivateRoute>} />
            <Route path="invitations" element={<PrivateRoute><RoleGuard allowedRoles={['admin', 'methodist']}><InvitationsPage /></RoleGuard></PrivateRoute>} />
            <Route path="profile" element={<PrivateRoute><ProfilePage /></PrivateRoute>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
