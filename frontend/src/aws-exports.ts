// AWS Amplify configuration
// This file exports the Amplify configuration for use throughout the app

export const awsConfig = {
  Auth: {
    Cognito: {
      userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID || '',
      userPoolClientId: import.meta.env.VITE_COGNITO_CLIENT_ID || '',
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
};

export const apiConfig = {
  endpoint: import.meta.env.VITE_API_GATEWAY_URL || '',
  region: import.meta.env.VITE_COGNITO_REGION || 'us-east-1',
};

export const stripeConfig = {
  publicKey: import.meta.env.VITE_STRIPE_PUBLIC_KEY || '',
};
