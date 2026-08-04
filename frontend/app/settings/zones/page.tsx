'use client';

import { useEffect, useState } from 'react';
import ZoneCanvas from '../../components/ZoneCanvas';

interface Zone {
  id: string;
  name: string;
  type: string;
  points: string;
  is_active: boolean;
  created_at: string;
}

export default function ZoneCalibrationPage() {
  const [zones, setZones] = useState<Zone[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [cameras, setCameras] = useState<{ index: number; name: string; label: string }[]>([]);
  const [selectedCamera, setSelectedCamera] = useState<number>(0);

  const fetchZones = () => {
    fetch('/api/v1/zones')
      .then((r) => r.json())
      .then((data) => {
        setZones(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    fetchZones();
    fetch('/api/v1/cameras')
      .then((r) => r.json())
      .then((data) => {
        setCameras(data);
        if (data.length > 0) {
          setSelectedCamera(data[0].index);
        }
      })
      .catch(() => {});
  }, []);

  const deleteZone = async (id: string) => {
    setDeleting(id);
    try {
      await fetch(`/api/v1/zones/${id}`, { method: 'DELETE' });
      setZones((prev) => prev.filter((z) => z.id !== id));
    } catch {
      // Handle error
    } finally {
      setDeleting(null);
    }
  };

  const formatPoints = (pointsJson: string) => {
    try {
      const pts = JSON.parse(pointsJson);
      return `${pts.length} vertices`;
    } catch {
      return '—';
    }
  };

  const formatDate = (ts: string) => {
    try {
      return new Date(ts).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return ts;
    }
  };

  return (
    <div className="p-4 lg:p-6 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <a href="/" className="text-xs text-slate-500 hover:text-slate-300 transition">
              Console
            </a>
            <svg className="h-3 w-3 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
            <span className="text-xs text-neon-yellow">Zone Calibration</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
            Zone Calibration Workspace
          </h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Define spatial security boundaries by drawing polygonal zones over the camera feed.
          </p>
        </div>
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Zone drawing canvas */}
        <div className="lg:col-span-2">
          <div className="glass-card p-4">
            {/* Card header with camera selector */}
            <div className="flex items-center justify-between gap-2 mb-4">
              <div className="flex items-center gap-2">
                <svg className="h-4 w-4 text-neon-yellow" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                </svg>
                <h2 className="text-sm font-semibold text-slate-200">Draw Zone</h2>
              </div>
              
              {cameras.length > 0 && (
                <div className="flex items-center gap-2 bg-slate-900/50 rounded-lg px-2 py-1 border border-slate-700/50">
                  <span className="text-xs text-slate-400">Camera:</span>
                  <select
                    value={selectedCamera}
                    onChange={(e) => setSelectedCamera(Number(e.target.value))}
                    className="bg-transparent text-sm text-slate-200 focus:outline-none focus:ring-0 border-none cursor-pointer p-0"
                    id="camera-selector"
                  >
                    {cameras.map((c) => (
                      <option key={c.index} value={c.index} className="bg-slate-800">
                        {c.label} - {c.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

            </div>

            <div className="rounded-lg bg-slate-950/50 p-1">
              <ZoneCanvas
                onZoneSaved={fetchZones}
                cameraIndex={selectedCamera}
              />
            </div>

            <div className="mt-4 rounded-lg border border-slate-700/30 bg-slate-800/20 px-4 py-3">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Instructions</h3>
              <ol className="text-xs text-slate-400 space-y-1.5 list-decimal list-inside">
                <li>Select the camera source above if multiple cameras are available.</li>
                <li>Click <strong className="text-slate-300">&quot;Capture Frame&quot;</strong> to freeze the video feed.</li>
                <li>Click on the canvas to place polygon vertices (minimum 3 points).</li>
                <li>Click <strong className="text-slate-300">&quot;Save Zone&quot;</strong> and enter a descriptive name.</li>
                <li>The zone becomes active immediately for intrusion detection.</li>
              </ol>
            </div>
          </div>
        </div>

        {/* Zone list */}
        <div className="glass-card flex flex-col">
          <div className="border-b border-slate-700/50 px-4 py-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <svg className="h-4 w-4 text-neon-cyan" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
              Active Zones
            </h2>
            <span className="text-[10px] font-mono text-slate-500">{zones.length} total</span>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-2 max-h-[600px]">
            {loading ? (
              <div className="flex items-center justify-center py-10">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-600 border-t-neon-yellow"></div>
              </div>
            ) : zones.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-slate-800/80">
                  <svg className="h-7 w-7 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                  </svg>
                </div>
                <p className="text-sm font-medium text-slate-400">No zones yet</p>
                <p className="mt-1 text-xs text-slate-600">Draw your first zone on the canvas</p>
              </div>
            ) : (
              zones.map((zone) => (
                <div
                  key={zone.id}
                  className="group rounded-lg border border-slate-700/30 bg-slate-800/30 p-3 transition hover:bg-slate-800/50"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className={`h-2.5 w-2.5 rounded-full flex-shrink-0 ${zone.is_active ? 'bg-neon-green' : 'bg-slate-600'}`}></div>
                      <div className="min-w-0">
                        <p className="text-xs font-medium text-slate-200 truncate">{zone.name}</p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-[10px] text-slate-500 uppercase font-mono">{zone.type}</span>
                          <span className="text-[10px] text-slate-600">•</span>
                          <span className="text-[10px] text-slate-500 font-mono">{formatPoints(zone.points)}</span>
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => deleteZone(zone.id)}
                      disabled={deleting === zone.id}
                      className="flex-shrink-0 opacity-0 group-hover:opacity-100 flex h-7 w-7 items-center justify-center rounded-md text-slate-500 transition hover:bg-neon-red/10 hover:text-neon-red disabled:opacity-40"
                      id={`delete-zone-${zone.id}`}
                    >
                      {deleting === zone.id ? (
                        <div className="h-3 w-3 animate-spin rounded-full border border-slate-500 border-t-transparent"></div>
                      ) : (
                        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      )}
                    </button>
                  </div>
                  <p className="mt-1.5 text-[10px] text-slate-600 pl-5">{formatDate(zone.created_at)}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
