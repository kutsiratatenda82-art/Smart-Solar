import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Bell, Activity, Cpu, PlaySquare } from 'lucide-react';

const Sidebar: React.FC = () => {
  const navItems = [
    { name: 'Dashboard', path: '/', icon: <LayoutDashboard size={20} /> },
    { name: 'Alerts', path: '/alerts', icon: <Bell size={20} /> },
    { name: 'History', path: '/history', icon: <Activity size={20} /> },
    { name: 'Devices', path: '/devices', icon: <Cpu size={20} /> },
    { name: 'Demo Mode', path: '/demo', icon: <PlaySquare size={20} /> },
  ];

  return (
    <aside className="w-64 bg-slate-900/40 backdrop-blur-md text-white flex flex-col h-full shadow-lg border-r border-white/10">
      <div className="p-6 border-b border-white/10">
        <h1 className="text-xl font-bold tracking-wider text-yellow-400 drop-shadow-md">Smart Solar</h1>
      </div>
      <nav className="flex-1 py-4">
        <ul className="space-y-1 px-3">
          {navItems.map((item) => (
            <li key={item.name}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                    isActive
                      ? 'bg-yellow-400/20 text-yellow-400 border border-yellow-400/30'
                      : 'text-slate-300 hover:bg-white/10 hover:text-white border border-transparent'
                  }`
                }
              >
                {item.icon}
                <span className="font-medium tracking-wide">{item.name}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <div className="p-4 text-xs text-slate-400 text-center border-t border-white/10">
        Smart Solar Alert v1.0
      </div>
    </aside>
  );
};

export default Sidebar;
