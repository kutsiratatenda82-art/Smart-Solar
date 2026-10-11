
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { DeviceProvider } from './context/DeviceContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import Devices from './pages/Devices';
import Dashboard from './pages/Dashboard';
import Alerts from './pages/Alerts';
import History from './pages/History';
import DemoMode from './pages/DemoMode';

function App() {
  return (
    <AuthProvider>
      <DeviceProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            
            <Route element={<ProtectedRoute />}>
              <Route element={<Layout />}>
                <Route path="/" element={<Dashboard />} />
                <Route path="/alerts" element={<Alerts />} />
                <Route path="/history" element={<History />} />
                <Route path="/devices" element={<Devices />} />
                <Route path="/demo" element={<DemoMode />} />
              </Route>
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </DeviceProvider>
    </AuthProvider>
  );
}

export default App;
