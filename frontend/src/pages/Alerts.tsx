import React, { useEffect, useState } from 'react';
import { useDevice } from '../context/DeviceContext';
import { alertService } from '../api/services';
import type { Alert } from '../types';
import { AlertTriangle, CheckCircle, Activity, CheckSquare } from 'lucide-react';

const Alerts: React.FC = () => {
  const { currentDevice } = useDevice();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  const fetchAlerts = async () => {
    if (!currentDevice) return;
    setLoading(true);
    try {
      const activeAlerts = await alertService.getActive();
      setAlerts(activeAlerts.filter(a => a.device_id === currentDevice.id));
    } catch (error) {
      console.error("Failed to fetch alerts", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [currentDevice]);

  const handleAcknowledge = async (id: number) => {
    if (!window.confirm("Are you sure you want to acknowledge this alert?")) return;
    setActionLoading(id);
    try {
      await alertService.acknowledge(id);
      await fetchAlerts();
    } catch (error) {
      console.error("Failed to acknowledge alert", error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleResolve = async (id: number) => {
    if (!window.confirm("Are you sure you want to manually resolve this alert?")) return;
    setActionLoading(id);
    try {
      await alertService.resolve(id);
      await fetchAlerts();
    } catch (error) {
      console.error("Failed to resolve alert", error);
    } finally {
      setActionLoading(null);
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

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Active Alerts</h1>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : alerts.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-lg border border-gray-200 border-dashed">
          <CheckCircle className="mx-auto h-12 w-12 text-emerald-500 mb-3" />
          <h3 className="text-lg font-medium text-gray-900">All clear</h3>
          <p className="mt-1 text-gray-500">There are no active alerts for this device.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {alerts.map((alert) => (
            <div 
              key={alert.id} 
              className={`p-6 rounded-lg border shadow-sm ${
                alert.severity === 'CRITICAL' ? 'bg-red-50 border-red-200' : 'bg-yellow-50 border-yellow-200'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex gap-4">
                  <AlertTriangle 
                    className={`mt-1 ${alert.severity === 'CRITICAL' ? 'text-red-600' : 'text-yellow-600'}`} 
                    size={24} 
                  />
                  <div>
                    <div className="flex items-center gap-3">
                      <h3 className={`font-bold text-lg ${
                        alert.severity === 'CRITICAL' ? 'text-red-900' : 'text-yellow-900'
                      }`}>
                        {alert.title}
                      </h3>
                      {alert.status === 'ACKNOWLEDGED' && (
                        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-gray-200 text-gray-700">
                          ACKNOWLEDGED
                        </span>
                      )}
                    </div>
                    
                    <p className={`mt-1 ${alert.severity === 'CRITICAL' ? 'text-red-800' : 'text-yellow-800'}`}>
                      {alert.message}
                    </p>
                    
                    <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                      <div className="bg-white bg-opacity-50 p-3 rounded">
                        <span className="font-medium text-gray-900 block">Measured Value</span>
                        <span className="font-mono mt-1 block">{alert.measured_value}</span>
                      </div>
                      {alert.threshold_value !== null && (
                        <div className="bg-white bg-opacity-50 p-3 rounded">
                          <span className="font-medium text-gray-900 block">Threshold</span>
                          <span className="font-mono mt-1 block">{alert.threshold_value}</span>
                        </div>
                      )}
                    </div>
                    
                    <div className="mt-4 p-3 bg-white rounded border border-white border-opacity-40">
                      <span className="font-medium text-gray-900 block text-sm mb-1">Recommended Action</span>
                      <span className="text-gray-700 text-sm">{alert.recommended_solution}</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex flex-col gap-2 shrink-0 ml-6">
                  {alert.status === 'ACTIVE' && (
                    <button
                      onClick={() => handleAcknowledge(alert.id)}
                      disabled={actionLoading === alert.id}
                      className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-white border border-gray-300 rounded text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                    >
                      <CheckSquare size={16} />
                      Acknowledge
                    </button>
                  )}
                  <button
                    onClick={() => handleResolve(alert.id)}
                    disabled={actionLoading === alert.id}
                    className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-white border border-gray-300 rounded text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                  >
                    <CheckCircle size={16} className="text-emerald-600" />
                    Resolve
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Alerts;
