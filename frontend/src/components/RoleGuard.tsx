import { useAuth } from '../context/AuthContext';

interface RoleGuardProps {
  allowedRoles: string[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function RoleGuard({ allowedRoles, children, fallback }: RoleGuardProps) {
  const { hasRole } = useAuth();

  if (!hasRole(allowedRoles)) {
    return fallback ? <>{fallback}</> : null;
  }

  return <>{children}</>;
}
