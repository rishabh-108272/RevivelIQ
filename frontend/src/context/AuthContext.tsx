import React, { createContext, useState, useEffect, useContext } from 'react';

interface AuthUser {
  email: string;
  role: string;
  fullName: string;
  token: string;
}

interface AuthContextType {
  user: AuthUser | null;
  login: (email: string, role: string, fullName: string, token: string) => void;
  logout: () => void;
  isLoading: boolean;
  getAuthHeaders: () => { Authorization: string } | {};
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check localStorage
    const savedToken = localStorage.getItem('reviveiq_token');
    const savedRole = localStorage.getItem('reviveiq_role');
    const savedName = localStorage.getItem('reviveiq_name');
    const savedEmail = localStorage.getItem('reviveiq_email');

    if (savedToken && savedRole && savedName && savedEmail) {
      setUser({
        email: savedEmail,
        role: savedRole,
        fullName: savedName,
        token: savedToken
      });
    }
    setIsLoading(false);
  }, []);

  const login = (email: string, role: string, fullName: string, token: string) => {
    localStorage.setItem('reviveiq_token', token);
    localStorage.setItem('reviveiq_role', role);
    localStorage.setItem('reviveiq_name', fullName);
    localStorage.setItem('reviveiq_email', email);
    setUser({ email, role, fullName, token });
  };

  const logout = () => {
    localStorage.removeItem('reviveiq_token');
    localStorage.removeItem('reviveiq_role');
    localStorage.removeItem('reviveiq_name');
    localStorage.removeItem('reviveiq_email');
    setUser(null);
  };

  const getAuthHeaders = () => {
    if (user?.token) {
      return { Authorization: `Bearer ${user.token}` };
    }
    return {};
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoading, getAuthHeaders }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
