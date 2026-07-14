import { create } from "zustand";

import type { User } from "../types";

interface AuthState {
  token: string | null;
  user: User | null;
  setToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem("realmeet_token"),
  user: null,
  setToken: (token) => {
    if (token) {
      localStorage.setItem("realmeet_token", token);
    } else {
      localStorage.removeItem("realmeet_token");
    }
    set({ token });
  },
  setUser: (user) => set({ user }),
  logout: () => {
    localStorage.removeItem("realmeet_token");
    set({ token: null, user: null });
  },
}));
