import { create } from 'zustand';

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

interface AuthState {
  token: string | null;
  user: User | null;
  setToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
  logout: () => void;
}

const getInitialToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  // Use sessionStorage so session clears automatically when browser tab is closed
  return sessionStorage.getItem('token');
};

const getInitialUser = (): User | null => {
  if (typeof window === 'undefined') return null;
  return JSON.parse(sessionStorage.getItem('user') || 'null');
};

export const useAuthStore = create<AuthState>((set) => ({
  token: getInitialToken(),
  user: getInitialUser(),
  setToken: (token) => {
    if (typeof window !== 'undefined') {
      if (token) {
        sessionStorage.setItem('token', token);
      } else {
        sessionStorage.removeItem('token');
        localStorage.removeItem('token');
      }
    }
    set({ token });
  },
  setUser: (user) => {
    if (typeof window !== 'undefined') {
      if (user) {
        sessionStorage.setItem('user', JSON.stringify(user));
      } else {
        sessionStorage.removeItem('user');
        localStorage.removeItem('user');
      }
    }
    set({ user });
  },
  logout: () => {
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem('token');
      sessionStorage.removeItem('user');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
    set({ token: null, user: null });
  },
}));
