import { createContext, type ReactNode, useCallback, useContext, useMemo, useState } from 'react';

import type { User } from '@/lib/types';

import { clearStoredUser, getStoredUser, setStoredUser } from './session';

interface AuthApi {
  user: User | null;
  login: (user: User) => void;
  logout: () => void;
  // The intro splash plays once after an actual login, as the transition into the app
  // (not on app open). login() arms it; the shell consumes it when the animation ends.
  splashPending: boolean;
  consumeSplash: () => void;
}

const AuthContext = createContext<AuthApi | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => getStoredUser());
  const [splashPending, setSplashPending] = useState(false);

  const login = useCallback((u: User) => {
    setStoredUser(u);
    setUser(u);
    setSplashPending(true);
  }, []);

  const logout = useCallback(() => {
    clearStoredUser();
    setUser(null);
    setSplashPending(false);
  }, []);

  const consumeSplash = useCallback(() => setSplashPending(false), []);

  const value = useMemo(
    () => ({ user, login, logout, splashPending, consumeSplash }),
    [user, login, logout, splashPending, consumeSplash],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthApi {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
