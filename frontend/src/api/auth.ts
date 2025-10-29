import type { User } from '@/types';
import {
  cognitoSignInWithProvider,
  cognitoSignOut,
  getCognitoUser,
  isAuthenticated,
} from '@/lib/cognito';

export const authApi = {
  // Sign in with Google via Cognito
  loginWithGoogle: async (): Promise<void> => {
    await cognitoSignInWithProvider('Google');
  },

  // Sign in with GitHub via Cognito
  loginWithGitHub: async (): Promise<void> => {
    await cognitoSignInWithProvider('GitHub');
  },

  // Sign in with Discord via Cognito
  loginWithDiscord: async (): Promise<void> => {
    await cognitoSignInWithProvider('Discord');
  },

  // Get current user from Cognito
  getCurrentUser: async (): Promise<User | null> => {
    return await getCognitoUser();
  },

  // Check if user is authenticated
  isAuthenticated: async (): Promise<boolean> => {
    return await isAuthenticated();
  },

  // Sign out via Cognito
  logout: async (): Promise<void> => {
    await cognitoSignOut();
  },
};
