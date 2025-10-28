import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // For cookie-based auth
});

// Request interceptor to add auth token if available
api.interceptors.request.use(
  (config) => {
    // If using JWT from localStorage
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized - redirect to login or refresh token
      console.error('Unauthorized access');
      // You can dispatch an event or use a global state to handle this
    }
    return Promise.reject(error);
  }
);
