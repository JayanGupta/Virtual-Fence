'use client';

import { useEffect, useState, useCallback } from 'react';
import IncidentDrawer from './components/IncidentDrawer';
import { ErrorBoundary } from './components/ErrorBoundary';
import { useTelemetry } from './hooks/useTelemetry';
import { api } from './lib/api';
import { ZoneData, CameraConfig } from './types';

export default function SecurityConsole() {
  const { telemetry, alerts, wsStatus, incidentCount, setIncidentCount } = useTelemetry();
  
  const [zones, setZones] = useState<ZoneData[]>([]);
  const [systemCameras, setSystemCameras] = useState<CameraConfig[]>([]);
  const [currentCameraIdx, setCurrentCameraIdx] = useState(0);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Load initial data
  useEffect(() => {
    const initData = async () => {
      try {
        const [zData, cData, iData] = await Promise.all([
          api.zones.list(),
          api.cameras.list(),
          api.incidents.list()
        ]);
        setZones(zData);
        setSystemCameras(cData);
        setIncidentCount(iData.length);
      } catch (err) {
        console.error("Failed to fetch initial data", err);
      }
    };
    initData();
  }, [setIncidentCount]);

  // Keyboard navigation for cycling cameras
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (systemCameras.length <= 1) return;
    if (e.key === 'ArrowRight') {
      setCurrentCameraIdx((prev) => (prev + 1) % systemCameras.length);
    } else if (e.key === 'ArrowLeft') {
      setCurrentCameraIdx((prev) => (prev - 1 + systemCameras.length) % systemCameras.length);
    }
  }, [systemCameras.length]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  const cycleNext = () => {
    if (systemCameras.length > 0) {
      setCurrentCameraIdx((prev) => (prev + 1) % systemCameras.length);
    }
  };

  const cyclePrev = () => {
    if (systemCameras.length > 0) {
      setCurrentCameraIdx((prev) => (prev - 1 + systemCameras.length) % systemCameras.length);
    }
  };

  const isBreached = telemetry.state === 'BREACH';

  // We gather all targets from all cameras for the tracker panel
  const allTargets = (telemetry.cameras || []).flatMap(c =>
    c.targets.map(t => ({ ...t, camera_name: c.camera_name }))
  );

  // Current active camera for display
  const activeCamera = systemCameras.length > 0 ? systemCameras[currentCameraIdx] : null;
  const activeCameraTelemetry = activeCamera
    ? (telemetry.cameras || []).find(c => c.camera_index === activeCamera.index)
    : null;
  const isActiveCamBreached = activeCameraTelemetry?.state === 'BREACH';

  return (
    <ErrorBoundary>
      <div className="p-4 lg:p-6 space-y-6 animate-fade-in">
        {/* ── Header ── */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
              Security Console
            </h1>
            <p className="text-sm text-slate-400 mt-0.5">
              Real-time perimeter surveillance &amp; intrusion detection
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-lg border border-slate-700/50 bg-slate-800/50 px-3 py-1.5" aria-label={`System status: ${wsStatus}`}>
              <span className={`h-2 w-2 rounded-full ${
                wsStatus === 'connected' ? 'bg-neon-green animate-pulse' :
                wsStatus === 'connecting' ? 'bg-neon-amber animate-pulse' :
                'bg-slate-600'
              }`}></span>
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                {wsStatus === 'connected' ? 'Live' : wsStatus === 'connecting' ? 'Connecting' : 'Offline'}
              </span>
            </div>
            <div className={isBreached ? 'badge-breach' : 'badge-secure'}>
              <span className={`h-2 w-2 rounded-full ${isBreached ? 'bg-neon-red animate-pulse' : 'bg-neon-green'}`}></span>
              {isBreached ? 'BREACH DETECTED' : 'SECURE'}
            </div>
            <button
              onClick={() => setDrawerOpen(true)}
              className="relative btn-ghost"
              id="open-incident-drawer"
              aria-label="Open Alerts"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              Alerts
              {incidentCount > 0 && (
                <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-neon-red text-[9px] font-bold text-white">
                  {incidentCount > 99 ? '99+' : incidentCount}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* ── Stats cards ── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="stat-card">
            <span className="label">Active Targets</span>
            <span className={`value ${telemetry.active_targets > 0 ? 'text-neon-cyan' : 'text-slate-500'}`}>
              {telemetry.active_targets}
            </span>
          </div>
          <div className="stat-card">
            <span className="label">Security State</span>
            <span className={`value text-lg ${isBreached ? 'text-neon-red text-glow-red' : 'text-neon-green text-glow-green'}`}>
              {isBreached ? 'BREACH' : 'SECURE'}
            </span>
          </div>
          <div className="stat-card">
            <span className="label">Active Zones</span>
            <span className="value text-neon-yellow">{zones.length}</span>
          </div>
          <div className="stat-card">
            <span className="label">Total Incidents</span>
            <span className="value text-neon-amber">{incidentCount}</span>
          </div>
        </div>

        {/* ── Single Camera + Target panel ── */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {/* Single Camera Display */}
          <div className="lg:col-span-3">
            {activeCamera ? (
              <div className={`glass-card overflow-hidden transition-all duration-300 flex flex-col ${isActiveCamBreached ? 'ring-2 ring-neon-red shadow-[0_0_15px_rgba(239,68,68,0.5)]' : 'ring-1 ring-slate-700/50'}`}>

                {/* Camera Header & Cycling Controls */}
                <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/30 bg-slate-900/50">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1">
                      <button
                        onClick={cyclePrev}
                        className="p-1.5 rounded-md hover:bg-slate-700/50 text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                        title="Previous Camera (← Arrow)"
                        disabled={systemCameras.length <= 1}
                        id="camera-prev"
                        aria-label="Previous Camera"
                      >
                        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                        </svg>
                      </button>
                      <button
                        onClick={cycleNext}
                        className="p-1.5 rounded-md hover:bg-slate-700/50 text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                        title="Next Camera (→ Arrow)"
                        disabled={systemCameras.length <= 1}
                        id="camera-next"
                        aria-label="Next Camera"
                      >
                        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                        </svg>
                      </button>
                    </div>
                    <div>
                      <div className="text-sm font-bold text-slate-200 tracking-wider">
                        {activeCamera.label}
                        <span className="text-slate-500 font-normal ml-2">{activeCamera.name}</span>
                        <span className="text-slate-600 font-normal ml-2 text-xs">
                          ({currentCameraIdx + 1}/{systemCameras.length})
                        </span>
                      </div>
                      {systemCameras.length > 1 && (
                        <div className="text-[10px] text-slate-500 mt-0.5">Use ◀ ▶ arrow keys to cycle cameras</div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="text-[11px] font-mono text-slate-500 hidden sm:inline">640×480 • MJPEG</span>
                    <span className={`flex items-center gap-1.5 text-xs font-bold ${isActiveCamBreached ? 'text-neon-red' : 'text-neon-green'}`}>
                      <span className={`h-2 w-2 rounded-full ${isActiveCamBreached ? 'bg-neon-red' : 'bg-neon-green'} animate-pulse`}></span>
                      {isActiveCamBreached ? 'BREACH' : 'LIVE'}
                    </span>
                  </div>
                </div>

                {/* Video Feed */}
                <div className="feed-container relative bg-black aspect-[4/3] sm:aspect-video w-full">
                  <img
                    src={`/api/v1/video_feed/${activeCamera.index}`}
                    alt={`Camera ${activeCamera.index} live feed`}
                    className="w-full h-full object-contain"
                    id={`video-feed-${activeCamera.index}`}
                    crossOrigin="anonymous"
                  />
                  {isActiveCamBreached && (
                    <div className="absolute inset-0 border-4 border-neon-red/60 pointer-events-none"></div>
                  )}
                </div>
              </div>
            ) : (
              <div className="glass-card flex flex-col items-center justify-center py-20 text-center ring-1 ring-slate-700/50">
                <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-slate-800/80">
                  <svg className="h-8 w-8 text-slate-600 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </div>
                <p className="text-sm font-medium text-slate-400">Loading cameras…</p>
              </div>
            )}
          </div>

          {/* Target tracker panel */}
          <div className="glass-card flex flex-col lg:col-span-1">
            <div className="border-b border-slate-700/50 px-4 py-3 bg-slate-900/50">
              <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <svg className="h-4 w-4 text-neon-cyan" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Active Targets
              </h2>
            </div>
            <div className="flex-1 overflow-y-auto p-3 space-y-2 max-h-[600px] lg:max-h-[800px]">
              {allTargets.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-10 text-center">
                  <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-slate-800/80">
                    <svg className="h-6 w-6 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  </div>
                  <p className="text-xs text-slate-500">No targets tracked across all cameras.</p>
                </div>
              ) : (
                allTargets.map((t, idx) => (
                  <div key={`${t.camera_name}-${t.id}-${idx}`} className="flex flex-col gap-1 rounded-lg border border-slate-700/30 bg-slate-800/40 px-3 py-2 transition hover:bg-slate-800/60">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-neon-cyan/10 text-neon-cyan shrink-0">
                          <span className="text-[10px] font-bold font-mono">{t.id}</span>
                        </div>
                        <span className="text-sm font-semibold text-slate-200 capitalize truncate">
                          {t.label || 'unknown'}
                        </span>
                      </div>
                      <span className="h-1.5 w-1.5 rounded-full bg-neon-cyan animate-pulse"></span>
                    </div>

                    <div className="flex items-center justify-between mt-1 pl-8">
                      <p className="text-[10px] text-slate-400 truncate">
                        Cam: <span className="text-slate-300 font-medium">{t.camera_name}</span>
                      </p>
                      <p className="text-[10px] font-mono text-slate-500">
                        pos({t.cx}, {t.cy})
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* ── Incident Drawer ── */}
        <IncidentDrawer isOpen={drawerOpen} onClose={() => setDrawerOpen(false)} alerts={alerts} />
      </div>
    </ErrorBoundary>
  );
}
