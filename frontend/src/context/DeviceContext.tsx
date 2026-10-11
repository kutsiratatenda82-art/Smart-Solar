import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { Device } from '../types';
import { deviceService } from '../api/services';
import { useAuth } from './AuthContext';

interface DeviceContextType {
  currentDevice: Device | null;
  devices: Device[];
  systemPower: boolean;
  setSystemPower: (power: boolean) => void;
  setCurrentDevice: (device: Device | null) => void;
  refreshDevices: () => Promise<void>;
  loading: boolean;
}

const DeviceContext = createContext<DeviceContextType | undefined>(undefined);

export const DeviceProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [currentDevice, setCurrentDevice] = useState<Device | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [systemPower, setSystemPower] = useState(true);

  const refreshDevices = async () => {
    try {
      setLoading(true);
      const fetchedDevices = await deviceService.getDevices();
      setDevices(fetchedDevices);
      
      // If we don't have a current device but we have devices, select the first one
      if (fetchedDevices.length > 0) {
        // Try to restore from localStorage first
        const savedId = localStorage.getItem('currentDeviceId');
        if (savedId) {
          const savedDevice = fetchedDevices.find(d => d.id === parseInt(savedId));
          if (savedDevice) {
            setCurrentDevice(savedDevice);
            return;
          }
        }
        setCurrentDevice(fetchedDevices[0]);
      } else {
        setCurrentDevice(null);
      }
    } catch (error) {
      console.error("Failed to fetch devices:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      refreshDevices();
    } else {
      setDevices([]);
      setCurrentDevice(null);
      setLoading(false);
    }
  }, [isAuthenticated]);

  const handleSetCurrentDevice = (device: Device | null) => {
    setCurrentDevice(device);
    if (device) {
      localStorage.setItem('currentDeviceId', device.id.toString());
    } else {
      localStorage.removeItem('currentDeviceId');
    }
  };

  return (
    <DeviceContext.Provider value={{ currentDevice, devices, systemPower, setSystemPower, setCurrentDevice: handleSetCurrentDevice, refreshDevices, loading }}>
      {children}
    </DeviceContext.Provider>
  );
};

export const useDevice = () => {
  const context = useContext(DeviceContext);
  if (context === undefined) {
    throw new Error('useDevice must be used within a DeviceProvider');
  }
  return context;
};
