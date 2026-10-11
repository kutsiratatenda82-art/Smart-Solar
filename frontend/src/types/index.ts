export interface User {
  id: number;
  email: string;
  is_active: boolean;
}

export interface Device {
  id: number;
  device_identifier: string;
  name: string;
  owner_id: number;
  created_at: string;
}

export interface DeviceCreate {
  device_identifier: string;
  name: string;
}

export interface DiagnosticResult {
  condition: string;
  severity: string;
  title: string;
  message: string;
  recommended_solution: string;
  measured_value: number;
  threshold_value: number | null;
}

export interface Reading {
  id: number;
  device_id: number;
  voltage: number;
  current: number;
  timestamp: string;
  diagnostics?: DiagnosticResult[];
}

export interface SimulationResult {
  mode: string;
  simulated: boolean;
  diagnostics: DiagnosticResult[];
}

export interface Alert {
  id: number;
  device_id: number;
  condition: string;
  severity: string;
  title: string;
  message: string;
  recommended_solution: string;
  measured_value: number;
  threshold_value: number | null;
  status: string;
  created_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
}
