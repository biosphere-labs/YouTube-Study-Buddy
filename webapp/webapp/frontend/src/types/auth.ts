export interface User {
  id: string;
  email: string;
  name?: string;
  avatar?: string;
  githubId?: string;
  googleId?: string;
  discordId?: string;
  createdAt: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface LoginCredentials {
  provider: 'google' | 'github' | 'discord';
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
