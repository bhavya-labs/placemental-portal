import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/api';

interface AuthContextType {
  user: any | null;
  token: string | null;
  loading: boolean;
  login: (credentials: any) => Promise<any>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<any | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [loading, setLoading] = useState<boolean>(true);

  // Initialize auth state from local storage token
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('token');
      if (storedToken) {
        try {
          setToken(storedToken);
          const profile = await authService.getProfile();
          setUser(profile);
          localStorage.setItem('user', JSON.stringify(profile));
        } catch (error: any) {
          console.error('Failed to load profile from stored token', error);
          const isAuthError = error.response && (error.response.status === 401 || error.response.status === 403);
          if (isAuthError) {
            logout();
          } else {
            const cachedUser = localStorage.getItem('user');
            if (cachedUser) {
              try {
                setUser(JSON.parse(cachedUser));
              } catch {
                // Ignore
              }
            }
          }
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (credentials: any) => {
    setLoading(true);
    try {
      const data = await authService.login(credentials);
      localStorage.setItem('token', data.access_token);
      setToken(data.access_token);
      
      // Fetch details profile after successful token retrieval
      const profile = await authService.getProfile();
      localStorage.setItem('user', JSON.stringify(profile));
      setUser(profile);
      setLoading(false);
      return profile;
    } catch (error) {
      setLoading(false);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setToken(null);
    setLoading(false);
  };

  const refreshProfile = async () => {
    if (token) {
      try {
        const profile = await authService.getProfile();
        setUser(profile);
      } catch (error) {
        console.error('Failed to refresh profile', error);
      }
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, refreshProfile }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
