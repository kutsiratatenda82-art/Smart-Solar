import React, { useState } from 'react';
import { useDevice } from '../context/DeviceContext';
import { deviceService } from '../api/services';
import { Cpu, Plus, Check } from 'lucide-react';

const Devices: React.FC = () => {
  const { devices, currentDevice, setCurrentDevice, refreshDevices, loading } = useDevice();
  const [isCreating, setIsCreating] = useState(false);
  const [newDeviceId, setNewDeviceId] = useState('');
  const [newDeviceName, setNewDeviceName] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    
    try {
      await deviceService.createDevice({
        device_identifier: newDeviceId,
        name: newDeviceName
      });
      await refreshDevices();
      setIsCreating(false);
      setNewDeviceId('');
      setNewDeviceName('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create device');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">My Devices</h1>
        <button
          onClick={() => setIsCreating(!isCreating)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
        >
          <Plus size={18} />
          <span>Add Device</span>
        </button>
      </div>

      {isCreating && (
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Register New Device</h2>
          <form onSubmit={handleCreate} className="space-y-4">
            {error && <div className="text-sm text-red-600 bg-red-50 p-3 rounded-md">{error}</div>}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Device Identifier</label>
                <input
                  type="text"
                  required
                  value={newDeviceId}
                  onChange={(e) => setNewDeviceId(e.target.value)}
                  placeholder="e.g. ESP32-SOLAR-001"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Friendly Name</label>
                <input
                  type="text"
                  required
                  value={newDeviceName}
                  onChange={(e) => setNewDeviceName(e.target.value)}
                  placeholder="e.g. Roof Panel 1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setIsCreating(false)}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {submitting ? 'Saving...' : 'Save Device'}
              </button>
            </div>
          </form>
        </div>
      )}

      {devices.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200 border-dashed">
          <Cpu className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No devices</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by registering a new solar device.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {devices.map((device) => {
            const isSelected = currentDevice?.id === device.id;
            
            return (
              <div 
                key={device.id}
                onClick={() => setCurrentDevice(device)}
                className={`relative flex flex-col p-6 rounded-lg border cursor-pointer transition-all ${
                  isSelected 
                    ? 'border-blue-500 ring-1 ring-blue-500 bg-blue-50 shadow-md' 
                    : 'border-gray-200 bg-white hover:border-blue-300 hover:shadow-sm'
                }`}
              >
                {isSelected && (
                  <div className="absolute top-4 right-4 text-blue-600">
                    <Check size={20} />
                  </div>
                )}
                
                <div className="flex items-center gap-3 mb-4">
                  <div className={`p-2 rounded-md ${isSelected ? 'bg-blue-100' : 'bg-gray-100'}`}>
                    <Cpu size={24} className={isSelected ? 'text-blue-600' : 'text-gray-600'} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{device.name}</h3>
                    <p className="text-xs text-gray-500 font-mono">{device.device_identifier}</p>
                  </div>
                </div>
                
                <div className="mt-auto text-xs text-gray-400">
                  Registered: {new Date(device.created_at).toLocaleDateString()}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Devices;
