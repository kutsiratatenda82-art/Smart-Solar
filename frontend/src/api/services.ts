import client from './client';
import type { User, Device, DeviceCreate, Reading, Alert, SimulationResult, DiagnosticResult } from '../types';

export const authService = {
  login: async (email: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    const response = await client.post('/api/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },
  register: async (email: string, password: string) => {
    const response = await client.post('/api/auth/register', { email, password });
    return response.data;
  },
  getMe: async (): Promise<User> => {
    const response = await client.get('/api/auth/me');
    return response.data;
  },
};

export const deviceService = {
  getDevices: async (): Promise<Device[]> => {
    const response = await client.get('/api/devices');
    return response.data;
  },
  createDevice: async (data: DeviceCreate): Promise<Device> => {
    const response = await client.post('/api/devices', data);
    return response.data;
  },
  getDeviceDiagnostics: async (deviceId: number): Promise<DiagnosticResult[]> => {
    const response = await client.get(`/api/devices/${deviceId}/diagnostics`);
    return response.data;
  },
  simulate: async (deviceId: number, data: { voltage: number, current: number }): Promise<SimulationResult> => {
    const response = await client.post(`/api/devices/${deviceId}/simulate`, data);
    return response.data;
  }
};

export const readingService = {
  getLatest: async (deviceId: number): Promise<Reading> => {
    const response = await client.get(`/api/devices/${deviceId}/readings/latest`);
    return response.data;
  },
  getHistory: async (deviceId: number, limit: number = 100): Promise<Reading[]> => {
    const response = await client.get(`/api/devices/${deviceId}/readings/history?limit=${limit}`);
    return response.data;
  }
};

export const alertService = {
  getActive: async (): Promise<Alert[]> => {
    const response = await client.get('/api/alerts');
    return response.data;
  },
  getHistory: async (limit: number = 100): Promise<Alert[]> => {
    const response = await client.get(`/api/alerts/history?limit=${limit}`);
    return response.data;
  },
  acknowledge: async (alertId: number): Promise<Alert> => {
    const response = await client.patch(`/api/alerts/${alertId}/acknowledge`);
    return response.data;
  },
  resolve: async (alertId: number): Promise<Alert> => {
    const response = await client.patch(`/api/alerts/${alertId}/resolve`);
    return response.data;
  }
};

export const chatService = {
  /**
   * Send a message to the AI solar assistant.
   * @param deviceId  The currently selected device ID (or null if no device selected).
   * @param message   The user's message text.
   * @returns         { reply: string } from the backend.
   */
  sendMessage: async (deviceId: number | null, message: string): Promise<{ reply: string }> => {
    if (deviceId === null) {
      // No device selected — return a client-side prompt without hitting the server
      return {
        reply:
          "Please select a device from the Devices page first so I can access your live solar data and give you accurate answers.",
      };
    }
    const response = await client.post(`/api/devices/${deviceId}/chat`, { message });
    return response.data;
  },
};
