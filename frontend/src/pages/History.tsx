import React, { useEffect, useState, useMemo } from 'react';
import { useDevice } from '../context/DeviceContext';
import { readingService, alertService } from '../api/services';
import type { Reading, Alert } from '../types';
import { Activity, Clock } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

const History: React.FC = () => {
  const { currentDevice } = useDevice();
  const [readings, setReadings] = useState<Reading[]>([]);
  const [alertHistory, setAlertHistory] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!currentDevice) return;

    let mounted = true;
    setLoading(true);

    const fetchHistory = async () => {
      try {
        const [historicalReadings, alerts] = await Promise.all([
          readingService.getHistory(currentDevice.id, 50).catch(() => []),
          alertService.getHistory(50).catch(() => [])
        ]);

        if (mounted) {
          // Recharts expects data chronologically, so we reverse it
          setReadings(historicalReadings.slice().reverse());
          setAlertHistory(alerts.filter(a => a.device_id === currentDevice.id));
        }
      } catch (error) {
        console.error("Failed to fetch history", error);
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchHistory();

    return () => {
      mounted = false;
    };
  }, [currentDevice]);

  const chartData = useMemo(() => {
    return readings.map(r => ({
      ...r,
      timeLabel: new Date(r.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      dateLabel: new Date(r.timestamp).toLocaleDateString()
    }));
  }, [readings]);

  if (!currentDevice) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500">
        <Activity size={48} className="mb-4 text-gray-300" />
        <h2 className="text-xl font-medium">No Device Selected</h2>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">System History</h1>
        <p className="text-gray-500 mt-1">Recent sensor readings and alert history</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Voltage History (V)</h2>
              {readings.length === 0 ? (
                <div className="h-64 flex items-center justify-center text-gray-400">
                  No reading data available
                </div>
              ) : (
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                      <XAxis dataKey="timeLabel" stroke="#9ca3af" fontSize={12} tickMargin={10} />
                      <YAxis stroke="#9ca3af" fontSize={12} tickFormatter={(val) => val.toFixed(1)} domain={['auto', 'auto']} />
                      <Tooltip 
                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                        labelStyle={{ fontWeight: 'bold', color: '#374151' }}
                      />
                      <Line type="monotone" dataKey="voltage" stroke="#3b82f6" strokeWidth={2} dot={false} activeDot={{ r: 6 }} name="Voltage" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Current History (A)</h2>
              {readings.length === 0 ? (
                <div className="h-64 flex items-center justify-center text-gray-400">
                  No reading data available
                </div>
              ) : (
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                      <XAxis dataKey="timeLabel" stroke="#9ca3af" fontSize={12} tickMargin={10} />
                      <YAxis stroke="#9ca3af" fontSize={12} tickFormatter={(val) => val.toFixed(1)} domain={['auto', 'auto']} />
                      <Tooltip 
                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                        labelStyle={{ fontWeight: 'bold', color: '#374151' }}
                      />
                      <Line type="monotone" dataKey="current" stroke="#ea580c" strokeWidth={2} dot={false} activeDot={{ r: 6 }} name="Current" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center gap-2">
              <Clock size={20} className="text-gray-500" />
              Alert Log
            </h2>
            
            {alertHistory.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No alerts recorded in history.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date/Time</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Severity</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Condition</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {alertHistory.map((alert) => (
                      <tr key={alert.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {new Date(alert.created_at).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            alert.severity === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                            alert.severity === 'WARNING' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {alert.severity}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {alert.title}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            alert.status === 'RESOLVED' ? 'bg-emerald-100 text-emerald-800' :
                            alert.status === 'ACKNOWLEDGED' ? 'bg-blue-100 text-blue-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {alert.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default History;
