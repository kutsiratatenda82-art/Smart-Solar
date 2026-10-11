import React, { useState } from 'react';
import { useDevice } from '../context/DeviceContext';
import { deviceService } from '../api/services';
import type { DiagnosticResult } from '../types';
import { Activity, AlertTriangle, PlaySquare, CheckCircle, Info, VolumeX, ShieldAlert } from 'lucide-react';
import { siren } from '../utils/audio';

const DemoMode: React.FC = () => {
  const { currentDevice, systemPower, setSystemPower } = useDevice();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DiagnosticResult[] | null>(null);

  React.useEffect(() => {
    if (result && result.some(r => r.severity === 'CRITICAL')) {
      try {
        siren.start();
      } catch (e) {
        console.warn("Audio play failed", e);
      }
    } else {
      siren.stop();
    }
    
    return () => siren.stop();
  }, [result]);

  const scenarios = [
    { name: 'Normal Operation', voltage: 13.2, current: 2.5, color: 'bg-emerald-600 hover:bg-emerald-700' },
    { name: 'Low Voltage', voltage: 11.0, current: 2.5, color: 'bg-yellow-600 hover:bg-yellow-700' },
    { name: 'Critical Low Voltage', voltage: 10.0, current: 2.5, color: 'bg-red-600 hover:bg-red-700' },
    { name: 'High Voltage', voltage: 14.8, current: 2.5, color: 'bg-yellow-600 hover:bg-yellow-700' },
    { name: 'Critical High Voltage', voltage: 15.5, current: 2.5, color: 'bg-red-600 hover:bg-red-700' },
    { name: 'Low Current', voltage: 13.2, current: 0.5, color: 'bg-yellow-600 hover:bg-yellow-700' },
    { name: 'Critical Current', voltage: 13.2, current: 0.2, color: 'bg-red-600 hover:bg-red-700' },
    { name: 'Multiple Faults', voltage: 9.5, current: 0.2, color: 'bg-purple-600 hover:bg-purple-700' },
  ];

  const handleSimulate = async (voltage: number, current: number) => {
    if (!currentDevice) return;
    
    // Initialize audio context immediately during user interaction to unlock it
    siren.init();
    
    setLoading(true);
    try {
      const res = await deviceService.simulate(currentDevice.id, { voltage, current });
      setResult(res.diagnostics);
    } catch (error) {
      console.error("Simulation failed", error);
    } finally {
      setLoading(false);
    }
  };

  if (!currentDevice) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500">
        <Activity size={48} className="mb-4 text-gray-300" />
        <h2 className="text-xl font-medium">No Device Selected</h2>
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
          <p className="text-gray-500 mb-8 text-lg">Demo Mode is currently disabled. Turn the system on to run simulations.</p>
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

  const hasCritical = result?.some(r => r.severity === 'CRITICAL');

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {hasCritical && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
          {/* Dark backdrop and flashing red border, but NO red background tint */}
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm pointer-events-none"></div>
          <div className="absolute inset-0 border-[12px] border-red-600 animate-pulse pointer-events-none"></div>
          
          <div className="relative bg-white border-4 border-red-600 rounded-xl shadow-2xl p-6 md:p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto pointer-events-auto transform animate-bounce-slow">
            <div className="flex items-center gap-4 border-b border-red-100 pb-6 mb-6">
              <div className="p-4 bg-red-100 text-red-600 rounded-full animate-pulse">
                <ShieldAlert size={48} />
              </div>
              <div>
                <h2 className="text-3xl font-black text-red-700 tracking-tight uppercase">Critical Alert Simulated</h2>
                <p className="text-red-900 font-medium text-lg mt-1">{result?.find(r => r.severity === 'CRITICAL')?.title}</p>
              </div>
            </div>

            <div className="space-y-6">
              <div className="bg-red-50 p-4 rounded-lg border border-red-100">
                <h3 className="font-bold text-red-900 flex items-center gap-2 mb-2">
                  <AlertTriangle size={20} />
                  Condition Detected
                </h3>
                <p className="text-red-800 text-lg leading-relaxed">{result?.find(r => r.severity === 'CRITICAL')?.message}</p>
              </div>

              <div className="bg-slate-50 p-6 rounded-lg border border-slate-200 shadow-inner">
                <h3 className="font-bold text-slate-900 uppercase tracking-wider text-sm mb-3">AI Recommended Solution</h3>
                <p className="text-slate-700 text-xl font-medium leading-relaxed">
                  {result?.find(r => r.severity === 'CRITICAL')?.recommended_solution}
                </p>
              </div>
            </div>

            <div className="mt-8 flex flex-col sm:flex-row justify-end gap-4 border-t border-gray-100 pt-6">
              <button 
                onClick={() => {
                  siren.stop();
                  setResult(null);
                  setSystemPower(false);
                }}
                className="px-6 py-3 bg-gray-900 hover:bg-black text-white font-bold rounded-lg shadow-md transition-colors flex items-center justify-center gap-2 w-full sm:w-auto"
              >
                <Activity size={20} />
                SHUT DOWN SYSTEM
              </button>
              <button 
                onClick={() => {
                  siren.stop();
                  setResult(result?.filter(r => r.severity !== 'CRITICAL') || null);
                }}
                className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-bold rounded-lg shadow-md transition-colors w-full sm:w-auto"
              >
                Silence Siren & Close
              </button>
            </div>
          </div>
        </div>
      )}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <PlaySquare className="text-purple-600" />
          Demo Mode
        </h1>
      </div>

      <div className="bg-purple-50 border border-purple-200 rounded-lg p-6 shadow-sm">
        <div className="flex items-start gap-4 text-purple-800">
          <Info size={24} className="mt-1 shrink-0" />
          <div>
            <h3 className="font-bold text-lg">⚠️ This is simulated data.</h3>
            <p className="mt-1">
              Selecting a scenario below will run the diagnostic engine against simulated sensor readings. 
              The results will be displayed here, but <strong>no real alerts will be created</strong> and 
              <strong> no historical readings will be saved</strong> to the database.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {scenarios.map((scenario) => (
          <button
            key={scenario.name}
            disabled={loading}
            onClick={() => handleSimulate(scenario.voltage, scenario.current)}
            className={`p-4 rounded-lg text-white font-medium shadow-sm transition-all transform active:scale-95 disabled:opacity-50 flex flex-col items-start ${scenario.color}`}
          >
            <span className="text-lg">{scenario.name}</span>
            <span className="text-sm opacity-80 font-mono mt-1">
              V: {scenario.voltage}V | I: {scenario.current}A
            </span>
          </button>
        ))}
      </div>

      {result && (
        <div className="mt-8">
          <div className="flex justify-between items-center mb-4 border-b pb-2">
            <h2 className="text-xl font-bold text-gray-900">Simulation Results</h2>
            {hasCritical && (
              <button 
                onClick={() => siren.stop()}
                className="flex items-center gap-2 px-3 py-1 bg-red-100 text-red-700 hover:bg-red-200 rounded text-sm font-bold transition-colors"
              >
                <VolumeX size={16} /> Silence Siren
              </button>
            )}
          </div>
          <div className="grid grid-cols-1 gap-4">
            {result.length === 0 || result[0].condition === 'NORMAL_OPERATION' ? (
              <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm flex items-start gap-4">
                <CheckCircle className="text-emerald-500 mt-1" size={24} />
                <div>
                  <h3 className="font-semibold text-gray-900">Normal Operation</h3>
                  <p className="text-sm text-gray-600 mt-1">Simulated readings are within normal parameters.</p>
                </div>
              </div>
            ) : (
              result.map((diag, idx) => (
                <div key={idx} className={`p-6 rounded-lg border shadow-sm flex items-start gap-4 ${
                  diag.severity === 'CRITICAL' ? 'bg-red-50 border-red-200' :
                  diag.severity === 'WARNING' ? 'bg-yellow-50 border-yellow-200' :
                  'bg-emerald-50 border-emerald-200'
                }`}>
                  {diag.severity === 'CRITICAL' ? <AlertTriangle className="text-red-600 mt-1" size={24} /> :
                   diag.severity === 'WARNING' ? <AlertTriangle className="text-yellow-600 mt-1" size={24} /> :
                   <CheckCircle className="text-emerald-600 mt-1" size={24} />}
                   
                  <div className="flex-1">
                    <h3 className={`font-bold text-lg ${
                      diag.severity === 'CRITICAL' ? 'text-red-900' :
                      diag.severity === 'WARNING' ? 'text-yellow-900' :
                      'text-emerald-900'
                    }`}>
                      {diag.title}
                    </h3>
                    <p className={`text-sm mt-1 font-medium ${
                      diag.severity === 'CRITICAL' ? 'text-red-800' :
                      diag.severity === 'WARNING' ? 'text-yellow-800' :
                      'text-emerald-800'
                    }`}>
                      {diag.message}
                    </p>
                    
                    <div className="mt-3 grid grid-cols-2 gap-4 text-sm max-w-md">
                      <div className="bg-white bg-opacity-50 p-2 rounded">
                        <span className="font-medium block text-gray-700">Simulated Value</span>
                        <span className="font-mono mt-0.5 block text-gray-900">{diag.measured_value}</span>
                      </div>
                      {diag.threshold_value !== null && (
                        <div className="bg-white bg-opacity-50 p-2 rounded">
                          <span className="font-medium block text-gray-700">Threshold</span>
                          <span className="font-mono mt-0.5 block text-gray-900">{diag.threshold_value}</span>
                        </div>
                      )}
                    </div>
                    
                    {diag.severity !== 'NORMAL' && (
                      <div className="mt-4 p-3 bg-white bg-opacity-60 rounded border border-white border-opacity-40">
                        <p className="text-sm font-medium text-gray-900">Recommended Action:</p>
                        <p className="text-sm text-gray-700 mt-1">{diag.recommended_solution}</p>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DemoMode;
