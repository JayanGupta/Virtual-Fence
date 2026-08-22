// Virtual Fence — Shared TypeScript Interfaces

export type SystemState = 'SECURE' | 'BREACH';

export interface TargetTelemetry {
  id: number;
  cx: number;
  cy: number;
  bbox: number[];
  label?: string;
  camera_name?: string; // Appended by frontend
}

export interface CameraTelemetry {
  camera_index: number;
  camera_name: string;
  active_targets: number;
  state: SystemState;
  targets: TargetTelemetry[];
}

export interface TelemetryData {
  active_targets: number;
  state: SystemState;
  cameras?: CameraTelemetry[];
  alerts?: IncidentAlert[];
}

export interface IncidentAlert {
  incident_id: string;
  zone_id: string;
  zone_name: string;
  object_id: number;
  timestamp: string;
  snapshot_url: string;
  video_url: string | null;
}

export interface ZoneData {
  id: string;
  name: string;
  type: string;
  points: string;
  is_active: boolean;
  created_at: string;
}

export interface CameraConfig {
  index: number;
  name: string;
  label: string;
}

export interface Incident {
  id: string;
  zone_id: string;
  object_id: number;
  timestamp: string;
  snapshot_path: string | null;
  video_path: string | null;
  status: string;
  severity: string;
}
