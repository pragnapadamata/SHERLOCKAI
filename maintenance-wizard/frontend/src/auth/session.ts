// Persisted dummy-SSO session. The stored user's id is the X-User-Id sent on
// every request (read by the non-React api client), so it lives outside React.
import type { User } from '@/lib/types';

const KEY = 'mw.user';

export function getStoredUser(): User | null {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

export function setStoredUser(user: User): void {
  localStorage.setItem(KEY, JSON.stringify(user));
}

export function clearStoredUser(): void {
  localStorage.removeItem(KEY);
}

export function currentUserId(): string | null {
  return getStoredUser()?.user_id ?? null;
}
