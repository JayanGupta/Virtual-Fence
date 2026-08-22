import { useEffect, useRef, useState } from 'react';
import { TelemetryData } from '../types';

export function useTelemetry() {
  const [telemetry, setTelemetry] = useState<TelemetryData>({
    active_targets: 0,
    state: 'SECURE',
    cameras: [],
  });
  const [alerts, setAlerts] = useState<any[]>([]);
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const [incidentCount, setIncidentCount] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const ws = new WebSocket(`${protocol}//${window.location.host}/ws/telemetry`);

      ws.onopen = () => {
        setWsStatus('connected');
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send('ping');
        }, 5000);
        ws.addEventListener('close', () => clearInterval(pingInterval));
      };

      ws.onmessage = (event) => {
        try {
          const data: TelemetryData = JSON.parse(event.data);
          setTelemetry(data);
          if (data.alerts && data.alerts.length > 0) {
            setAlerts((prev) => [...data.alerts!, ...prev]);
            setIncidentCount((prev) => prev + data.alerts!.length);
          }
        } catch {
          // ignore invalid json
        }
      };

      ws.onclose = () => {
        setWsStatus('disconnected');
        reconnectRef.current = setTimeout(connect, 3000);
      };
      ws.onerror = () => ws.close();
      wsRef.current = ws;
    };

    connect();
    return () => {
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      wsRef.current?.close();
    };
  }, []);

  return { telemetry, alerts, wsStatus, incidentCount, setIncidentCount };
}
