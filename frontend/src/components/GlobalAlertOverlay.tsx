import React, { useEffect, useRef, useState } from 'react';
import { useDevice } from '../context/DeviceContext';
import { alertService, readingService } from '../api/services';
import { siren } from '../utils/audio';
import { AlertTriangle, ShieldAlert } from 'lucide-react';
import type { Alert } from '../types';

const GlobalAlertOverlay: React.FC = () => {
  const { currentDevice, systemPower, setSystemPower } = useDevice();
  const [criticalAlert, setCriticalAlert] = useState<Alert | null>(null);
  const alertIdRef = useRef<number | null>(null);

  // Keep alertIdRef in sync with state
  useEffect(() => {
    alertIdRef.current = criticalAlert?.id ?? null;
  }, [criticalAlert]);
  
  // Polling effect — NO criticalAlert in deps so it doesn't restart on every alert change
  useEffect(() => {
    if (!currentDevice || !systemPower) {
      setCriticalAlert(null);
      return;
    }

    const checkForAlerts = async () => {
      try {
        // First check if device is offline (no readings in last 15 seconds)
        const latestReading = await readingService.getLatest(currentDevice.id).catch(() => null);
        const isOffline = latestReading 
          ? (new Date().getTime() - new Date(latestReading.timestamp).getTime() > 15000) 
          : true;

        if (isOffline) {
          setCriticalAlert(prev => prev ? null : prev); // Only update if there was an alert
          return; // Do not show alerts for disconnected hardware
        }

        const activeAlerts = await alertService.getActive();
        
        // Find the first ACTIVE critical alert for the current device
        const targetAlert = activeAlerts.find(
          a => a.device_id === currentDevice.id && a.severity === 'CRITICAL' && a.status === 'ACTIVE'
        );

        if (targetAlert) {
          // Only update state if the alert ID actually changed — prevents unnecessary re-renders
          setCriticalAlert(prev => prev?.id === targetAlert.id ? prev : targetAlert);
        } else {
          setCriticalAlert(prev => prev ? null : prev);
        }
      } catch (err) {
        // Ignore fetch errors to prevent console spam
      }
    };

    // Poll every 5 seconds
    const interval = setInterval(checkForAlerts, 5000);
    checkForAlerts(); // Initial check

    return () => clearInterval(interval);
  }, [currentDevice, systemPower]);

  // Audio effect — only fires when alert presence actually changes (not on every poll)
  useEffect(() => {
    if (criticalAlert) {
      try {
        siren.start();
      } catch (e) {
        console.warn("Could not start audio due to browser policies");
      }
    } else {
      siren.stop();
    }

    // Only stop on unmount, NOT on every re-render
    return () => { siren.stop(); };
  }, [criticalAlert]);

  if (!criticalAlert) return null;

  return (
    <div className="fixed inset-0 z-[9999] pointer-events-none flex items-center justify-center p-4">
      {/* Dark backdrop and flashing red border */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm pointer-events-none"></div>
      <div className="absolute inset-0 border-[12px] border-red-600 animate-pulse pointer-events-none"></div>
      
      {/* Modal Content */}
      <div className="relative bg-white border-4 border-red-600 rounded-xl shadow-2xl p-6 md:p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto pointer-events-auto transform animate-bounce-slow">
        
        <div className="flex items-center gap-4 border-b border-red-100 pb-6 mb-6">
          <div className="p-4 bg-red-100 text-red-600 rounded-full animate-pulse">
            <ShieldAlert size={48} />
          </div>
          <div>
            <h2 className="text-3xl font-black text-red-700 tracking-tight uppercase">Critical Alert</h2>
            <p className="text-red-900 font-medium text-lg mt-1">{criticalAlert.title}</p>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-red-50 p-4 rounded-lg border border-red-100">
            <h3 className="font-bold text-red-900 flex items-center gap-2 mb-2">
              <AlertTriangle size={20} />
              Condition Detected
            </h3>
            <p className="text-red-800 text-lg leading-relaxed">{criticalAlert.message}</p>
          </div>

          <div className="bg-slate-50 p-6 rounded-lg border border-slate-200 shadow-inner">
            <h3 className="font-bold text-slate-900 uppercase tracking-wider text-sm mb-3">AI Recommended Solution</h3>
            <p className="text-slate-700 text-xl font-medium leading-relaxed">
              {criticalAlert.recommended_solution}
            </p>
          </div>
        </div>

        <div className="mt-8 flex flex-col sm:flex-row justify-end gap-4 border-t border-gray-100 pt-6">
          <button 
            onClick={() => {
              siren.stop(); 
              setCriticalAlert(null); 
              setSystemPower(false);
            }}
            className="px-6 py-3 bg-gray-900 hover:bg-black text-white font-bold rounded-lg shadow-md transition-colors w-full sm:w-auto flex items-center justify-center gap-2"
          >
            SHUT DOWN SYSTEM
          </button>
          <button 
            onClick={async () => {
              siren.stop(); 
              if (criticalAlert) {
                try {
                  await alertService.acknowledge(criticalAlert.id);
                } catch (e) {
                  console.error("Failed to acknowledge alert");
                }
              }
              setCriticalAlert(null); 
            }}
            className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-bold rounded-lg shadow-md transition-colors w-full sm:w-auto"
          >
            Silence Alarm & Hide
          </button>
        </div>
      </div>
    </div>
  );
};

export default GlobalAlertOverlay;
