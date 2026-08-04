'use client';

import { useEffect, useRef, useState, useCallback } from 'react';

interface Incident {
  incident_id: string;
  zone_id: string;
  zone_name: string;
  object_id: number;
  timestamp: string;
  snapshot_url: string;
  video_url?: string | null;
  status?: string;
}

interface IncidentDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  alerts: Incident[];
}

export default function IncidentDrawer({ isOpen, onClose, alerts }: IncidentDrawerProps) {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [acknowledging, setAcknowledging] = useState<string | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const prevCountRef = useRef(0);

  // Merge incoming alerts
  useEffect(() => {
    if (alerts.length > 0) {
      setIncidents((prev) => {
        const existingIds = new Set(prev.map((i) => i.incident_id));
        const newAlerts = alerts.filter((a) => !existingIds.has(a.incident_id));
        return [...newAlerts, ...prev].slice(0, 200);
      });
    }
  }, [alerts]);

  // Audio chime on new alert
  const playChime = useCallback(() => {
    try {
      if (!audioCtxRef.current) {
        audioCtxRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      const ctx = audioCtxRef.current;
      const now = ctx.currentTime;

      // Two-tone alert chime
      const frequencies = [880, 1100];
      frequencies.forEach((freq, i) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, now + i * 0.12);
        gain.gain.setValueAtTime(0.15, now + i * 0.12);
        gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.12 + 0.3);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now + i * 0.12);
        osc.stop(now + i * 0.12 + 0.35);
      });
    } catch {
      // Audio not available
    }
  }, []);

  useEffect(() => {
    if (incidents.length > prevCountRef.current && prevCountRef.current >= 0) {
      playChime();
    }
    prevCountRef.current = incidents.length;
  }, [incidents.length, playChime]);

  // Load existing incidents on mount
  useEffect(() => {
    fetch('/api/v1/incidents')
      .then((r) => r.json())
      .then((data: any[]) => {
        const mapped: Incident[] = data.map((d) => ({
          incident_id: d.id,
          zone_id: d.zone_id,
          zone_name: d.zone_name || 'Zone',
          object_id: d.object_id,
          timestamp: d.timestamp,
          snapshot_url: d.snapshot_path || '',
          video_url: d.video_path || null,
          status: d.status,
        }));
        setIncidents((prev) => {
          const existingIds = new Set(prev.map((i) => i.incident_id));
          const fresh = mapped.filter((m) => !existingIds.has(m.incident_id));
          return [...prev, ...fresh].slice(0, 200);
        });
      })
      .catch(() => {});
  }, []);

  const acknowledge = async (id: string) => {
    setAcknowledging(id);
    try {
      await fetch(`/api/v1/incidents/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'ACKNOWLEDGED' }),
      });
      setIncidents((prev) =>
        prev.map((inc) =>
          inc.incident_id === id ? { ...inc, status: 'ACKNOWLEDGED' } : inc
        )
      );
    } catch {
      // Ignore
    } finally {
      setAcknowledging(null);
    }
  };

  const formatTime = (ts: string) => {
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString('en-US', { hour12: false }) + ' ' + d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
      return ts;
    }
  };

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm transition-opacity"
          onClick={onClose}
        />
      )}

      {/* Drawer */}
      <div
        className={`fixed right-0 top-0 z-50 h-full w-full max-w-md transform border-l border-slate-700/50 bg-slate-900/95 backdrop-blur-xl shadow-2xl transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-700/50 px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-neon-red/15">
              <svg className="h-4 w-4 text-neon-red" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div>
              <h2 className="text-sm font-semibold text-slate-100">Incident Feed</h2>
              <p className="text-[10px] text-slate-500">
                {incidents.filter((i) => !i.status || i.status === 'UNREAD').length} unread
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-800 hover:text-slate-200"
            id="incident-drawer-close"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Incident list */}
        <div className="overflow-y-auto h-[calc(100%-65px)] px-4 py-3 space-y-3">
          {incidents.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-slate-800/80">
                <svg className="h-8 w-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <p className="text-sm font-medium text-slate-400">No incidents recorded</p>
              <p className="mt-1 text-xs text-slate-600">Perimeter is secure</p>
            </div>
          )}

          {incidents.map((inc) => (
            <div
              key={inc.incident_id}
              className={`animate-fade-in glass-card overflow-hidden transition-all duration-200 ${
                !inc.status || inc.status === 'UNREAD'
                  ? 'border-neon-red/30 shadow-[0_0_15px_rgba(239,68,68,0.08)]'
                  : 'opacity-60'
              }`}
            >
              {/* Snapshot thumbnail or Video */}
              {inc.video_url ? (
                <div className="relative h-36 w-full overflow-hidden bg-slate-950">
                  <video
                    src={inc.video_url}
                    controls
                    className="h-full w-full object-contain"
                  />
                  <div className="absolute top-2 left-2 pointer-events-none">
                    <span className="inline-flex items-center gap-1 rounded bg-neon-red/90 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white">
                      <span className="h-1.5 w-1.5 rounded-full bg-white animate-pulse"></span>
                      Video Clip
                    </span>
                  </div>
                </div>
              ) : inc.snapshot_url && (
                <div className="relative h-36 w-full overflow-hidden bg-slate-950">
                  <img
                    src={inc.snapshot_url}
                    alt={`Incident ${inc.incident_id.slice(0, 8)}`}
                    className="h-full w-full object-cover"
                    loading="lazy"
                  />
                  <div className="absolute top-2 left-2">
                    <span className="inline-flex items-center gap-1 rounded bg-neon-red/90 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white">
                      <span className="h-1.5 w-1.5 rounded-full bg-white animate-pulse"></span>
                      Breach
                    </span>
                  </div>
                </div>
              )}

              {/* Details */}
              <div className="p-3 space-y-2">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs font-semibold text-slate-200">
                      {inc.zone_name}
                    </p>
                    <p className="text-[10px] text-slate-500 font-mono mt-0.5">
                      Target ID-{inc.object_id} • {formatTime(inc.timestamp)}
                    </p>
                  </div>
                  <span
                    className={`text-[9px] font-bold uppercase tracking-widest ${
                      !inc.status || inc.status === 'UNREAD'
                        ? 'text-neon-red'
                        : inc.status === 'ACKNOWLEDGED'
                        ? 'text-neon-amber'
                        : 'text-neon-green'
                    }`}
                  >
                    {inc.status || 'UNREAD'}
                  </span>
                </div>

                {(!inc.status || inc.status === 'UNREAD') && (
                  <button
                    onClick={() => acknowledge(inc.incident_id)}
                    disabled={acknowledging === inc.incident_id}
                    className="w-full rounded-lg bg-slate-700/50 px-3 py-1.5 text-[11px] font-medium text-slate-300 transition hover:bg-slate-700 hover:text-neon-amber disabled:opacity-40"
                    id={`ack-${inc.incident_id}`}
                  >
                    {acknowledging === inc.incident_id ? 'Acknowledging…' : '✓ Acknowledge'}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
