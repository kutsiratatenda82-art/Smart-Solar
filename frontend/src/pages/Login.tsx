import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authService } from '../api/services';
import { useAuth } from '../context/AuthContext';
import { Sun, AlertCircle } from 'lucide-react';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await authService.login(email, password);
      await login(data.access_token);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to login. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-[url('/solar_bg.png')] bg-cover bg-center bg-no-repeat relative">
      <div className="absolute inset-0 bg-black/40" />
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center relative z-10">
        <Sun className="mx-auto h-16 w-16 text-yellow-400 drop-shadow-md" />
        <h2 className="mt-4 text-center text-4xl font-extrabold text-white drop-shadow-md tracking-tight">
          Smart Solar Alert
        </h2>
        <p className="mt-2 text-center text-md text-gray-200 drop-shadow">
          Sign in to access your solar monitoring dashboard
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="bg-white/10 backdrop-blur-xl py-8 px-4 shadow-2xl sm:rounded-2xl sm:px-10 border border-white/20">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="bg-red-500/20 backdrop-blur-md border border-red-500/50 rounded-lg p-4 flex items-start gap-3 text-red-50 text-sm">
                <AlertCircle size={20} className="mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}
            
            <div>
              <label className="block text-sm font-medium text-gray-100">Email address</label>
              <div className="mt-1">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="appearance-none block w-full px-4 py-3 bg-white/20 border border-white/10 rounded-xl text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:border-transparent sm:text-sm transition-all shadow-inner"
                  placeholder="admin@example.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-100">Password</label>
              <div className="mt-1">
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="appearance-none block w-full px-4 py-3 bg-white/20 border border-white/10 rounded-xl text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:border-transparent sm:text-sm transition-all shadow-inner"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-lg text-sm font-bold text-gray-900 bg-yellow-400 hover:bg-yellow-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-400 disabled:opacity-50 transition-all transform hover:scale-[1.02]"
              >
                {loading ? 'Signing in...' : 'Sign in'}
              </button>
            </div>
          </form>

          <div className="mt-8">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-white/20" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-transparent text-gray-200">New to Smart Solar?</span>
              </div>
            </div>

            <div className="mt-6 text-center">
              <Link to="/register" className="font-semibold text-yellow-400 hover:text-yellow-300 transition-colors">
                Create an account
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
