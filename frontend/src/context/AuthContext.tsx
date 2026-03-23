import {
  createContext, useCallback, useContext, useState, type ReactNode,
} from "react";

interface AuthUser {
  token: string;
  userId: number;
  email: string;
  name: string | null;
}

interface AuthCtx extends AuthUser {
  isAuthenticated: true;
  login: (u: AuthUser) => void;
  logout: () => void;
  authHeader: () => Record<string, string>;
}

interface AnonCtx {
  isAuthenticated: false;
  token: null;
  userId: null;
  email: null;
  name: null;
  login: (u: AuthUser) => void;
  logout: () => void;
  authHeader: () => Record<string, string>;
}

type ContextType = AuthCtx | AnonCtx;

const KEY = "lh_auth";
const AuthContext = createContext<ContextType | null>(null);

function readStorage(): AuthUser | null {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(readStorage);

  const login = useCallback((u: AuthUser) => {
    try { localStorage.setItem(KEY, JSON.stringify(u)); } catch { /* ignore */ }
    setUser(u);
  }, []);

  const logout = useCallback(() => {
    try { localStorage.removeItem(KEY); } catch { /* ignore */ }
    setUser(null);
  }, []);

  const authHeader = useCallback(
    (): Record<string, string> =>
      user ? { Authorization: `Bearer ${user.token}` } : {},
    [user],
  );

  const ctx: ContextType = user
    ? { ...user, isAuthenticated: true, login, logout, authHeader }
    : { isAuthenticated: false, token: null, userId: null, email: null, name: null, login, logout, authHeader };

  return <AuthContext.Provider value={ctx}>{children}</AuthContext.Provider>;
}

export function useAuth(): ContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
