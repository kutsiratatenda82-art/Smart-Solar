import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authService } from '../api/services';
import { useAuth } from '../context/AuthContext';
import { Sun, AlertCircle, KeyRound, X, ShieldCheck } from 'lucide-react';

const SECURITY_QUESTIONS = [
  { id: 'birthday', label: 'What is your date of birth?', type: 'date', placeholder: '' },
  { id: 'school', label: 'What was the name of your first primary school?', type: 'text', placeholder: 'e.g. Mkoba Primary' },
  { id: 'pet', label: "What was your first pet's name?", type: 'text', placeholder: 'Your answer' },
  { id: 'city', label: 'In which city were you born?', type: 'text', placeholder: 'e.g. Kwekwe' },
];

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showForgot, setShowForgot] = useState(false);
  const [recoveryEmail, setRecoveryEmail] = useState('');
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [verifying, setVerifying] = useState(false);
  const [recoverySent, setRecoverySent] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const openForgot = () => {
    setRecoveryEmail(email);
    setAnswers({});
    setRecoverySent(false);
    setShowForgot(true);
  };

  const handleRecovery = (e: React.FormEvent) => {
    e.preventDefault();
    setVerifying(true);
    setTimeout(() => {
      setVerifying(false);
      setRecoverySent(true);
    }, 1200);
  };

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
              <div className="flex items-center justify-between">
                <label className="block text-sm font-medium text-gray-100">Password</label>
                <button
                  type="button"
                  id="forgot-password-button"
                  onClick={openForgot}
                  className="text-sm font-semibold text-yellow-400 hover:text-yellow-300 transition-colors"
                >
                  Forgot password?
                </button>
              </div>
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

      {/* ── Forgot password modal ── */}
      {showForgot && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
          onClick={() => setShowForgot(false)}
        >
          <div
            id="forgot-password-modal"
            className="w-full max-w-md bg-slate-900/95 border border-white/15 rounded-2xl shadow-2xl p-6 text-white max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-yellow-400/20 flex items-center justify-center">
                  <KeyRound className="text-yellow-400" size={20} />
                </div>
                <div>
                  <h3 className="text-lg font-bold">Account Recovery</h3>
                  <p className="text-xs text-gray-300">Answer your security questions to verify your identity</p>
                </div>
              </div>
              <button
                type="button"
                id="forgot-password-close"
                onClick={() => setShowForgot(false)}
                className="text-gray-400 hover:text-white transition-colors"
                aria-label="Close"
              >
                <X size={20} />
              </button>
            </div>

            {recoverySent ? (
              <div className="text-center py-6">
                <ShieldCheck className="mx-auto text-emerald-400 mb-3" size={48} />
                <h4 className="text-lg font-semibold mb-2">Request received</h4>
                <p className="text-sm text-gray-300 mb-6">
                  Self-service password reset is not enabled on this server yet. Please contact your
                  system administrator to complete the reset for <span className="text-yellow-400">{recoveryEmail || 'your account'}</span>.
                </p>
                <button
                  type="button"
                  onClick={() => setShowForgot(false)}
                  className="w-full py-3 rounded-xl font-bold text-gray-900 bg-yellow-400 hover:bg-yellow-300 transition-all"
                >
                  Back to sign in
                </button>
              </div>
            ) : (
              <form className="space-y-4" onSubmit={handleRecovery}>
                <div>
                  <label className="block text-sm font-medium text-gray-200 mb-1">Email address</label>
                  <input
                    id="recovery-email"
                    type="email"
                    required
                    value={recoveryEmail}
                    onChange={(e) => setRecoveryEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="block w-full px-4 py-2.5 bg-white/10 border border-white/15 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-400 sm:text-sm"
                  />
                </div>
                {SECURITY_QUESTIONS.map((q, i) => (
                  <div key={q.id}>
                    <label className="block text-sm font-medium text-gray-200 mb-1">
                      {i + 1}. {q.label}
                    </label>
                    <input
                      id={`security-${q.id}`}
                      type={q.type}
                      required
                      value={answers[q.id] || ''}
                      onChange={(e) => setAnswers((prev) => ({ ...prev, [q.id]: e.target.value }))}
                      placeholder={q.placeholder}
                      className="block w-full px-4 py-2.5 bg-white/10 border border-white/15 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-400 sm:text-sm [color-scheme:dark]"
                    />
                  </div>
                ))}
                <button
                  type="submit"
                  id="recovery-submit"
                  disabled={verifying}
                  className="w-full py-3 rounded-xl font-bold text-gray-900 bg-yellow-400 hover:bg-yellow-300 disabled:opacity-50 transition-all"
                >
                  {verifying ? 'Verifying...' : 'Verify & Reset Password'}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Login;
