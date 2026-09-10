import React, { createContext, useState, useEffect, useContext } from 'react';
import { api, setAuthToken, removeAuthToken, getAuthToken } from '../api/client';
import { socketService } from '../api/socket';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const initAuth = async () => {
      const token = getAuthToken();
      if (token) {
        try {
          const userData = await api.getMe();
          setUser(userData);
          socketService.connect(token);
        } catch (err) {
          console.error('Failed to load user:', err);
          removeAuthToken();
        }
      }
      setLoading(false);
    };

    initAuth();

    // Listen for unauthorized events to clear auth state
    const handleUnauthorized = () => {
      setUser(null);
      socketService.disconnect();
    };
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    
    return () => {
      window.removeEventListener('auth:unauthorized', handleUnauthorized);
    };
  }, []);

  const login = async (email, password) => {
    try {
      setError(null);
      const data = await api.login({ email, password });
      setAuthToken(data.access_token);
      
      const userData = await api.getMe();
      setUser(userData);
      socketService.connect(data.access_token);
      return userData;
    } catch (err) {
      setError(err.message || 'Login failed');
      throw err;
    }
  };

  const register = async (userData) => {
    try {
      setError(null);
      await api.register(userData);
      // Auto login after register
      return await login(userData.email, userData.password);
    } catch (err) {
      setError(err.message || 'Registration failed');
      throw err;
    }
  };

  const logout = () => {
    removeAuthToken();
    setUser(null);
    socketService.disconnect();
  };

  const value = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
