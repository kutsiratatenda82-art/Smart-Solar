import React, { useEffect, useState } from 'react';
import { useDevice } from '../context/DeviceContext';
import { readingService, deviceService, alertService } from '../api/services';
import type { Reading, DiagnosticResult, Alert } from '../types';
import { Zap, AlertTriangle, CheckCircle, Info, Activity } from 'lucide-react';

const Dashboard: React.FC = () => {
  const { currentDevice, systemPower, setSystemPower } = useDevice();
  const [latestReading, setLatestReading] = useState<Reading | null>(null);
  const [diagnostics, setDiagnostics] = useState<DiagnosticResult[]>([]);
  const [activeAlerts, setActiveAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!currentDevice || !systemPower) return;

    let mounted = true;
    let intervalId: number;

    const fetchData = async () => {
      try {
        const [reading, diags, alerts] = await Promise.all([
          readingService.getLatest(currentDevice.id).catch(() => null),
          deviceService.getDeviceDiagnostics(currentDevice.id).catch(() => []),
          alertService.getActive().catch(() => [])
        ]);

        if (mounted) {
          setLatestReading(reading);
          setDiagnostics(diags);
          setActiveAlerts(alerts.filter(a => a.device_id === currentDevice.id));
        }
      } catch (error) {
        console.error("Dashboard fetch error", error);
      } finally {
        if (mounted) setLoading(false);
      }
    };

    setLoading(true);
    fetchData();
    intervalId = window.setInterval(fetchData, 5000); // Poll every 5 seconds

    return () => {
      mounted = false;
      window.clearInterval(intervalId);
    };
  }, [currentDevice, systemPower]);

  if (!currentDevice) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500">
        <Activity size={48} className="mb-4 text-gray-300" />
        <h2 className="text-xl font-medium">No Device Selected</h2>
        <p className="mt-2 text-sm">Please select a device from the Devices page to view its dashboard.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!systemPower) {
    return (
      <div className="flex flex-col items-center justify-center h-[70vh] bg-gray-50 rounded-2xl border-2 border-dashed border-gray-300">
        <div className="bg-white p-12 rounded-3xl shadow-xl border border-gray-100 flex flex-col items-center text-center max-w-lg">
          <div className="w-24 h-24 bg-red-50 rounded-full flex items-center justify-center mb-6">
            <Activity size={48} className="text-red-500 opacity-50" />
          </div>
          <h2 className="text-3xl font-black text-gray-900 mb-2">SYSTEM SHUT DOWN</h2>
          <p className="text-gray-500 mb-8 text-lg">Monitoring is currently disabled. No alerts or readings will be processed.</p>
          <button 
            onClick={() => setSystemPower(true)}
            className="bg-emerald-500 hover:bg-emerald-600 text-white font-bold py-4 px-8 rounded-full shadow-[0_4px_14px_0_rgba(16,185,129,0.39)] transition-all transform hover:scale-105 active:scale-95"
          >
            TURN SYSTEM ON
          </button>
        </div>
      </div>
    );
  }

  // Determine if offline (no reading in the last 15 seconds)
  const isOffline = latestReading 
    ? (new Date().getTime() - new Date(latestReading.timestamp).getTime() > 15000) 
    : true;

  const hasCritical = activeAlerts.some(a => a.severity === 'CRITICAL');
  const hasWarning = activeAlerts.some(a => a.severity === 'WARNING');
  const systemStatus = isOffline ? 'OFFLINE' : hasCritical ? 'CRITICAL' : hasWarning ? 'WARNING' : 'NORMAL';
  

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white drop-shadow-md tracking-tight">Dashboard</h1>
        <div className={`px-4 py-1.5 rounded-full border font-bold text-sm tracking-wide shadow-md ${
          systemStatus === 'NORMAL' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 backdrop-blur-md' :
          systemStatus === 'WARNING' ? 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40 backdrop-blur-md' :
          systemStatus === 'CRITICAL' ? 'bg-red-500/20 text-red-300 border-red-500/40 backdrop-blur-md' :
          'bg-gray-500/20 text-gray-300 border-gray-500/40 backdrop-blur-md'
        }`}>
          STATUS: {systemStatus}
        </div>
      </div>

      {!latestReading ? (
        <div className="bg-white/10 backdrop-blur-xl p-8 rounded-2xl border border-white/20 text-center shadow-2xl">
          <Info className="mx-auto h-12 w-12 text-blue-300 mb-3 drop-shadow" />
          <h3 className="text-xl font-medium text-white">No Data Available</h3>
          <p className="text-blue-100/70 mt-1">This device hasn't sent any sensor readings yet.</p>
        </div>
      ) : (
        <>
          {/* Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className={`bg-white/10 backdrop-blur-xl p-6 rounded-2xl border border-white/20 shadow-xl flex items-start gap-4 transition-transform hover:scale-[1.02] ${isOffline ? 'opacity-60 grayscale' : ''}`}>
              <div className="p-4 bg-blue-500/20 text-blue-300 rounded-xl shadow-inner border border-blue-500/30">
                <Zap size={28} />
              </div>
              <div>
                <p className="text-sm font-medium text-blue-200">Current Voltage</p>
                <p className="text-3xl font-black text-white mt-1 drop-shadow">{latestReading.voltage.toFixed(2)} <span className="text-xl font-medium text-blue-200">V</span></p>
              </div>
            </div>

            <div className={`bg-white/10 backdrop-blur-xl p-6 rounded-2xl border border-white/20 shadow-xl flex items-start gap-4 transition-transform hover:scale-[1.02] ${isOffline ? 'opacity-60 grayscale' : ''}`}>
              <div className="p-4 bg-orange-500/20 text-orange-300 rounded-xl shadow-inner border border-orange-500/30">
                <Activity size={28} />
              </div>
              <div>
                <p className="text-sm font-medium text-orange-200">Current</p>
                <p className="text-3xl font-black text-white mt-1 drop-shadow">{latestReading.current.toFixed(2)} <span className="text-xl font-medium text-orange-200">A</span></p>
              </div>
            </div>

            <div className={`bg-white/10 backdrop-blur-xl p-6 rounded-2xl border border-white/20 shadow-xl flex items-start gap-4 transition-transform hover:scale-[1.02] ${isOffline ? 'opacity-60 grayscale' : ''}`}>
              <div className="p-4 bg-slate-500/20 text-slate-300 rounded-xl shadow-inner border border-slate-500/30">
                <AlertTriangle size={28} />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-200">Active Alerts</p>
                <p className="text-3xl font-black text-white mt-1 drop-shadow">{activeAlerts.length}</p>
              </div>
            </div>
          </div>

          <div className="flex justify-between items-center mt-8 px-2">
            {isOffline ? (
              <div className="flex items-center gap-2 text-sm font-bold text-red-400 bg-red-900/40 backdrop-blur-md px-4 py-2 rounded-lg border border-red-500/50 shadow-md">
                <Activity size={18} className="animate-pulse" />
                HARDWARE DISCONNECTED
              </div>
            ) : (
              <div></div>
            )}
            <p className={`text-sm ${isOffline ? 'text-red-300 font-medium' : 'text-gray-300'}`}>
              Last updated: {new Date(latestReading.timestamp).toLocaleString()}
            </p>
          </div>

          {/* Diagnostics Section */}
          <div className="mt-10">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-3 drop-shadow-md">
              <div className="p-2 bg-blue-500/20 rounded-lg border border-blue-500/30">
                <Activity size={22} className="text-blue-400" />
              </div>
              System Diagnosis
            </h2>
            
            <div className="grid grid-cols-1 gap-5">
              {diagnostics.length === 0 ? (
                <div className="bg-emerald-900/30 backdrop-blur-xl p-6 rounded-2xl border border-emerald-500/30 shadow-xl flex items-start gap-5 transition-all">
                  <div className="p-3 bg-emerald-500/20 rounded-full">
                    <CheckCircle className="text-emerald-400" size={28} />
                  </div>
                  <div>
                    <h3 className="font-bold text-lg text-emerald-100">Normal Operation</h3>
                    <p className="text-emerald-200/80 mt-1">All sensor readings are within normal operating parameters.</p>
                  </div>
                </div>
              ) : (
                diagnostics.map((diag, idx) => (
                  <div key={idx} className={`p-6 rounded-2xl border shadow-xl flex items-start gap-5 backdrop-blur-xl transition-all ${
                    diag.severity === 'CRITICAL' ? 'bg-red-900/30 border-red-500/40' :
                    diag.severity === 'WARNING' ? 'bg-yellow-900/30 border-yellow-500/40' :
                    'bg-emerald-900/30 border-emerald-500/40'
                  }`}>
                    <div className={`p-3 rounded-full ${
                      diag.severity === 'CRITICAL' ? 'bg-red-500/20' :
                      diag.severity === 'WARNING' ? 'bg-yellow-500/20' :
                      'bg-emerald-500/20'
                    }`}>
                      {diag.severity === 'CRITICAL' ? <AlertTriangle className="text-red-400" size={28} /> :
                       diag.severity === 'WARNING' ? <AlertTriangle className="text-yellow-400" size={28} /> :
                       <CheckCircle className="text-emerald-400" size={28} />}
                    </div>
                     
                    <div className="flex-1">
                      <h3 className={`font-bold text-lg ${
                        diag.severity === 'CRITICAL' ? 'text-red-200' :
                        diag.severity === 'WARNING' ? 'text-yellow-200' :
                        'text-emerald-200'
                      }`}>
                        {diag.title}
                      </h3>
                      <p className={`text-md mt-1 ${
                        diag.severity === 'CRITICAL' ? 'text-red-100/80' :
                        diag.severity === 'WARNING' ? 'text-yellow-100/80' :
                        'text-emerald-100/80'
                      }`}>
                        {diag.message}
                      </p>
                      
                      {diag.severity !== 'NORMAL' && (
                        <div className="mt-5 p-4 bg-black/20 rounded-xl border border-white/10 shadow-inner">
                          <p className="text-sm font-semibold text-white/90">Recommended Action:</p>
                          <p className="text-md text-white/70 mt-1.5">{diag.recommended_solution}</p>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default Dashboard;
