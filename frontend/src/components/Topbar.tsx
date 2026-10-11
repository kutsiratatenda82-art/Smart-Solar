import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useDevice } from '../context/DeviceContext';
import { LogOut, User as UserIcon, Power } from 'lucide-react';
import { useLocation } from 'react-router-dom';

const Topbar: React.FC = () => {
  const { user, logout } = useAuth();
  const { currentDevice, systemPower, setSystemPower } = useDevice();
  const location = useLocation();
  
  const isDemo = location.pathname.includes('demo');

  return (
    <header className="bg-white/10 backdrop-blur-md border-b border-white/20 shadow-sm sticky top-0 z-10 px-6 py-4 flex items-center justify-between">
      <div className="flex items-center gap-6">
        <div className="flex flex-col">
          <span className="text-sm text-gray-300 font-medium">Current Device</span>
          <span className="font-semibold text-white drop-shadow-sm">
            {currentDevice ? currentDevice.name : 'No device selected'}
          </span>
        </div>
        
        {isDemo ? (
          <div className="flex items-center gap-2 bg-purple-500/20 text-purple-200 border border-purple-500/30 px-3 py-1 rounded-full text-sm font-semibold backdrop-blur-sm">
            <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse"></span>
            DEMO MODE
          </div>
        ) : (
          <div className="flex items-center gap-2 bg-emerald-500/20 text-emerald-200 border border-emerald-500/30 px-3 py-1 rounded-full text-sm font-semibold backdrop-blur-sm">
            <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]"></span>
            LIVE DATA
          </div>
        )}
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm text-gray-200">
          <UserIcon size={18} />
          <span>{user?.email}</span>
        </div>
        <div className="h-6 w-px bg-white/20"></div>
        <button
          onClick={() => setSystemPower(!systemPower)}
          className={`flex items-center justify-center p-2 rounded-full transition-colors shadow-sm border backdrop-blur-sm ${
            systemPower 
              ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 hover:bg-emerald-500/30' 
              : 'bg-red-500/20 text-red-300 border-red-500/40 hover:bg-red-500/30 shadow-[0_0_15px_rgba(239,68,68,0.5)]'
          }`}
          title={systemPower ? "System is ON. Click to SHUT DOWN." : "System is OFF. Click to TURN ON."}
        >
          <Power size={20} />
        </button>
        <div className="h-6 w-px bg-white/20"></div>
        <button
          onClick={logout}
          className="flex items-center gap-2 text-sm text-gray-300 hover:text-white transition-colors"
        >
          <LogOut size={18} />
          <span>Logout</span>
        </button>
      </div>
    </header>
  );
};

export default Topbar;
