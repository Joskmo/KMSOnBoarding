import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Layout } from './components/Layout';
import { PrivateRoute } from './components/PrivateRoute';
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
import { TestsListPage } from './pages/TestsListPage';
import { TestCreatePage } from './pages/TestCreatePage';
import { TestEditPage } from './pages/TestEditPage';
import { TestDetailPage } from './pages/TestDetailPage';
import { TestTakePage } from './pages/TestTakePage';
import { MyAttemptsPage } from './pages/MyAttemptsPage';
import { TestAttemptsPage } from './pages/TestAttemptsPage';

function RoleRoute({ allowedRoles, children }: { allowedRoles: string[]; children: React.ReactNode }) {
  const { hasRole } = useAuth();
  return hasRole(allowedRoles) ? <>{children}</> : <Navigate to="/tests" replace />;
}

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
            <Route path="users" element={<PrivateRoute><RoleRoute allowedRoles={['admin', 'methodist']}><UsersPage /></RoleRoute></PrivateRoute>} />
            <Route path="users/:id/edit" element={<PrivateRoute><RoleRoute allowedRoles={['admin', 'methodist']}><UserEditPage /></RoleRoute></PrivateRoute>} />
            <Route path="invitations" element={<PrivateRoute><RoleRoute allowedRoles={['admin', 'methodist']}><InvitationsPage /></RoleRoute></PrivateRoute>} />
            <Route path="profile" element={<PrivateRoute><ProfilePage /></PrivateRoute>} />
            
            {/* Assessment routes */}
            <Route path="tests" element={<PrivateRoute><TestsListPage /></PrivateRoute>} />
            <Route path="tests/create" element={<PrivateRoute><RoleRoute allowedRoles={['admin', 'methodist']}><TestCreatePage /></RoleRoute></PrivateRoute>} />
            <Route path="tests/:id" element={<PrivateRoute><TestDetailPage /></PrivateRoute>} />
            <Route path="tests/:id/edit" element={<PrivateRoute><RoleRoute allowedRoles={['admin', 'methodist']}><TestEditPage /></RoleRoute></PrivateRoute>} />
            <Route path="tests/:id/attempts" element={<PrivateRoute><RoleRoute allowedRoles={['admin', 'methodist']}><TestAttemptsPage /></RoleRoute></PrivateRoute>} />
            <Route path="tests/:id/take" element={<PrivateRoute><RoleRoute allowedRoles={['seminarist', 'candidate']}><TestTakePage /></RoleRoute></PrivateRoute>} />
            <Route path="attempts/my" element={<PrivateRoute><MyAttemptsPage /></PrivateRoute>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
