import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../api/client';
import { useAuth } from '../context/AuthContext';

function EyeIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
      <circle cx="12" cy="12" r="3"></circle>
    </svg>
  );
}

function EyeOffIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
      <line x1="1" y1="1" x2="23" y2="23"></line>
    </svg>
  );
}

function CheckCircleIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
      <polyline points="22 4 12 14.01 9 11.01"></polyline>
    </svg>
  );
}

function PencilIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path>
    </svg>
  );
}

function validateEmail(email: string): boolean {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

function roleLabel(role: string): string {
  const map: Record<string, string> = {
    admin: 'Администратор',
    methodist: 'Методист',
    seminarist: 'Семинарист',
    candidate: 'Кандидат',
  };
  return map[role] || role;
}

export function ProfilePage() {
  const navigate = useNavigate();
  const { user, updateUser } = useAuth();

  // Personal data state
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [editName, setEditName] = useState(false);
  const [editEmail, setEditEmail] = useState(false);
  const [nameSaving, setNameSaving] = useState(false);
  const [emailSaving, setEmailSaving] = useState(false);
  const [nameSuccess, setNameSuccess] = useState('');
  const [emailSuccess, setEmailSuccess] = useState('');
  const [nameError, setNameError] = useState('');
  const [emailError, setEmailError] = useState('');

  // Password state
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordSuccess, setPasswordSuccess] = useState('');
  const [passwordError, setPasswordError] = useState('');

  const passwordsMatch = !!(password && confirmPassword && password === confirmPassword);
  const passwordValid = password.length >= 8;
  const passwordsValid = passwordsMatch && passwordValid;
  const passwordsMismatch = !!(password && confirmPassword && password !== confirmPassword);

  const handleNameSave = async () => {
    if (!fullName.trim()) return;
    setNameSaving(true);
    setNameError('');
    setNameSuccess('');
    try {
      await authApi.put('/users/me', { full_name: fullName });
      updateUser({ full_name: fullName });
      setNameSuccess('Имя обновлено');
      setEditName(false);
    } catch (err: any) {
      setNameError(err.response?.data?.detail || 'Ошибка обновления');
    } finally {
      setNameSaving(false);
    }
  };

  const handleEmailSave = async () => {
    if (email && !validateEmail(email)) {
      setEmailError('Некорректный email');
      return;
    }
    setEmailSaving(true);
    setEmailError('');
    setEmailSuccess('');
    try {
      await authApi.put('/users/me', { email: email || null });
      updateUser({ email: email || null });
      setEmailSuccess('Email обновлён');
      setEditEmail(false);
    } catch (err: any) {
      setEmailError(err.response?.data?.detail || 'Ошибка обновления');
    } finally {
      setEmailSaving(false);
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!passwordsValid) return;
    setPasswordSaving(true);
    setPasswordError('');
    setPasswordSuccess('');
    try {
      await authApi.put('/users/me', { password });
      setPasswordSuccess('Пароль успешно изменён');
      setPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setPasswordError(err.response?.data?.detail || 'Ошибка изменения пароля');
    } finally {
      setPasswordSaving(false);
    }
  };

  const getPasswordFieldClass = (value: string, isMismatch: boolean, isValid: boolean, tooShort: boolean) => {
    const base = 'mt-1 block w-full px-3 py-2 pr-10 border rounded-md focus:outline-none focus:ring-2 transition';
    if (isMismatch) {
      return `${base} border-red-500 focus:ring-red-200 focus:border-red-500 bg-red-50`;
    }
    if (tooShort) {
      return `${base} border-red-500 focus:ring-red-200 focus:border-red-500 bg-red-50`;
    }
    if (isValid && value.length >= 8) {
      return `${base} border-green-500 focus:ring-green-200 focus:border-green-500 bg-green-50`;
    }
    return `${base} border-gray-300 focus:ring-indigo-200 focus:border-indigo-500`;
  };

  return (
    <div className="max-w-2xl space-y-8">
      <div className="flex items-center gap-2">
        <button
          onClick={() => navigate('/modules')}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          ← Назад
        </button>
      </div>
      <h1 className="text-2xl font-bold">Профиль</h1>

      {/* Personal Data Card */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Личные данные</h2>
        {nameSuccess && (
          <div className="bg-green-50 text-green-700 p-3 rounded mb-4">{nameSuccess}</div>
        )}
        {emailSuccess && (
          <div className="bg-green-50 text-green-700 p-3 rounded mb-4">{emailSuccess}</div>
        )}
        {(nameError || emailError) && (
          <div className="bg-red-50 text-red-700 p-3 rounded mb-4">{nameError || emailError}</div>
        )}

        <div className="space-y-4">
          {/* Role (read-only) */}
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">Роль</label>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-1 bg-indigo-100 text-indigo-800 rounded text-sm font-medium">
                {roleLabel(user?.role || '')}
              </span>
            </div>
          </div>

          {/* Full Name */}
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">Полное имя</label>
            {!editName ? (
              <div className="flex items-center gap-3">
                <span className="text-base text-gray-900">{fullName || '—'}</span>
                <button
                  onClick={() => { setEditName(true); setNameError(''); setNameSuccess(''); }}
                  className="p-1.5 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded transition"
                  title="Изменить"
                >
                  <PencilIcon />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleNameSave()}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-500"
                  autoFocus
                />
                <button
                  onClick={handleNameSave}
                  disabled={nameSaving || !fullName.trim()}
                  className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50 text-sm"
                >
                  {nameSaving ? '...' : 'Сохранить'}
                </button>
                <button
                  onClick={() => { setEditName(false); setFullName(user?.full_name || ''); setNameError(''); }}
                  className="px-3 py-2 text-gray-500 hover:text-gray-700 text-sm"
                >
                  Отмена
                </button>
              </div>
            )}
          </div>

          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">Email</label>
            {!editEmail ? (
              <div className="flex items-center gap-3">
                <span className="text-base text-gray-900">{email || <span className="text-gray-400 italic">не указано</span>}</span>
                <button
                  onClick={() => { setEditEmail(true); setEmailError(''); setEmailSuccess(''); }}
                  className="p-1.5 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded transition"
                  title="Изменить"
                >
                  <PencilIcon />
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => { setEmail(e.target.value); setEmailError(''); }}
                    onKeyDown={(e) => e.key === 'Enter' && handleEmailSave()}
                    className={`flex-1 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 transition ${
                      email && !validateEmail(email)
                        ? 'border-red-500 focus:ring-red-200 focus:border-red-500 bg-red-50'
                        : 'border-gray-300 focus:ring-indigo-200 focus:border-indigo-500'
                    }`}
                    placeholder="user@example.com"
                    autoFocus
                  />
                  <button
                    onClick={handleEmailSave}
                    disabled={emailSaving || (!!email && !validateEmail(email))}
                    className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50 text-sm"
                  >
                    {emailSaving ? '...' : 'Сохранить'}
                  </button>
                  <button
                    onClick={() => { setEditEmail(false); setEmail(user?.email || ''); setEmailError(''); }}
                    className="px-3 py-2 text-gray-500 hover:text-gray-700 text-sm"
                  >
                    Отмена
                  </button>
                </div>
                {email && !validateEmail(email) && (
                  <p className="text-sm text-red-600">Введите корректный email</p>
                )}
                <p className="text-xs text-gray-500">
                  Оставьте поле пустым, чтобы удалить email
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Password Card */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Смена пароля</h2>
        {passwordSuccess && (
          <div className="bg-green-50 text-green-700 p-3 rounded mb-4">{passwordSuccess}</div>
        )}
        {passwordError && (
          <div className="bg-red-50 text-red-700 p-3 rounded mb-4">{passwordError}</div>
        )}
        <form onSubmit={handlePasswordSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Новый пароль</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={getPasswordFieldClass(password, false, passwordValid && passwordsMatch, password.length > 0 && password.length < 8)}
                placeholder="Минимум 8 символов"
              />
              <button
                type="button"
                onMouseDown={() => setShowPassword(true)}
                onMouseUp={() => setShowPassword(false)}
                onMouseLeave={() => setShowPassword(false)}
                onTouchStart={() => setShowPassword(true)}
                onTouchEnd={() => setShowPassword(false)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 focus:outline-none"
                tabIndex={-1}
              >
                {showPassword ? <EyeOffIcon /> : <EyeIcon />}
              </button>
            </div>
            {password.length > 0 && password.length < 8 && (
              <p className="mt-1.5 text-sm text-red-600 flex items-center gap-1">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-red-500"></span>
                Пароль слишком короткий (минимум 8 символов)
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Подтвердите пароль</label>
            <div className="relative">
              <input
                type={showConfirm ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className={getPasswordFieldClass(confirmPassword, passwordsMismatch, passwordsValid, false)}
                placeholder="Повторите пароль"
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
                {passwordsValid && (
                  <CheckCircleIcon />
                )}
                <button
                  type="button"
                  onMouseDown={() => setShowConfirm(true)}
                  onMouseUp={() => setShowConfirm(false)}
                  onMouseLeave={() => setShowConfirm(false)}
                  onTouchStart={() => setShowConfirm(true)}
                  onTouchEnd={() => setShowConfirm(false)}
                  className="text-gray-400 hover:text-gray-600 focus:outline-none"
                  tabIndex={-1}
                >
                  {showConfirm ? <EyeOffIcon /> : <EyeIcon />}
                </button>
              </div>
            </div>
            {passwordsMismatch && (
              <p className="mt-1.5 text-sm text-red-600 flex items-center gap-1">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-red-500"></span>
                Пароли не совпадают
              </p>
            )}
            {passwordsValid && (
              <p className="mt-1.5 text-sm text-green-600 flex items-center gap-1">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-green-500"></span>
                Пароли совпадают
              </p>
            )}
            {!passwordsValid && !passwordsMismatch && confirmPassword && password.length >= 8 && (
              <p className="mt-1.5 text-sm text-gray-500">
                Продолжайте ввод пароля...
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={passwordSaving || !passwordsValid}
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
          >
            {passwordSaving ? 'Сохранение...' : 'Сменить пароль'}
          </button>
        </form>
      </div>
    </div>
  );
}
