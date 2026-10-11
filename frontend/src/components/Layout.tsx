import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import GlobalAlertOverlay from './GlobalAlertOverlay';
import SolarChatbot from './SolarChatbot';

const Layout: React.FC = () => {
  return (
    <div className="flex h-screen overflow-hidden bg-[url('/solar_bg.png')] bg-cover bg-center bg-no-repeat relative">
      <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-[2px]" />
      <div className="flex h-screen w-full relative z-10">
        <Sidebar />
        <div className="relative flex flex-col flex-1 overflow-y-auto overflow-x-hidden">
          <Topbar />
          <main className="w-full grow p-6 sm:p-10">
            <Outlet />
          </main>
        </div>
      </div>
      <GlobalAlertOverlay />
      <SolarChatbot />
    </div>
  );
};

export default Layout;
