import { Amplify } from 'aws-amplify';
import {
  signOut,
  fetchAuthSession,
  getCurrentUser,
  fetchUserAttributes,
  signInWithRedirect,
} from 'aws-amplify/auth';
import type { User } from '@/types';

// Initialize Amplify with Cognito configuration
export function configureAmplify() {
  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID,
        userPoolClientId: import.meta.env.VITE_COGNITO_CLIENT_ID,
        loginWith: {
          oauth: {
            domain: `${import.meta.env.VITE_COGNITO_USER_POOL_ID}.auth.${import.meta.env.VITE_COGNITO_REGION}.amazoncognito.com`,
            scopes: ['openid', 'email', 'profile'],
            redirectSignIn: [window.location.origin + '/auth/callback'],
            redirectSignOut: [window.location.origin + '/login'],
            responseType: 'code',
          },
        },
      },
    },
  });
}

// Get current authenticated user
export async function getCognitoUser(): Promise<User | null> {
  try {
    const cognitoUser = await getCurrentUser();
    const attributes = await fetchUserAttributes();

    // Determine provider from identities
    const provider = (attributes.identities as string | undefined)?.includes('Google')
      ? 'google'
      : (attributes.identities as string | undefined)?.includes('GitHub')
      ? 'github'
      : 'discord';

    return {
      id: cognitoUser.userId,
      email: attributes.email || '',
      name: attributes.name || attributes.email || '',
      avatar: attributes.picture,
      provider: provider as 'google' | 'github' | 'discord',
      createdAt: new Date().toISOString(), // Cognito doesn't provide this directly
    };
  } catch (error) {
    console.error('Error getting Cognito user:', error);
    return null;
  }
}

// Get current access token
export async function getAccessToken(): Promise<string | null> {
  try {
    const session = await fetchAuthSession();
    const token = session.tokens?.accessToken?.toString();
    return token || null;
  } catch (error) {
    console.error('Error getting access token:', error);
    return null;
  }
}

// Get ID token (contains user claims)
export async function getIdToken(): Promise<string | null> {
  try {
    const session = await fetchAuthSession();
    const token = session.tokens?.idToken?.toString();
    return token || null;
  } catch (error) {
    console.error('Error getting ID token:', error);
    return null;
  }
}

// Sign in with OAuth provider
export async function cognitoSignInWithProvider(
  provider: 'Google' | 'GitHub' | 'Discord'
): Promise<void> {
  try {
    await signInWithRedirect({
      provider: {
        custom: provider,
      },
    });
  } catch (error) {
    console.error(`Error signing in with ${provider}:`, error);
    throw error;
  }
}

// Sign out
export async function cognitoSignOut(): Promise<void> {
  try {
    await signOut();
  } catch (error) {
    console.error('Error signing out:', error);
    throw error;
  }
}

// Check if user is authenticated
export async function isAuthenticated(): Promise<boolean> {
  try {
    const session = await fetchAuthSession();
    return !!session.tokens?.accessToken;
  } catch (error) {
    return false;
  }
}

// Refresh auth session
export async function refreshAuthSession(): Promise<void> {
  try {
    await fetchAuthSession({ forceRefresh: true });
  } catch (error) {
    console.error('Error refreshing session:', error);
    throw error;
  }
}
