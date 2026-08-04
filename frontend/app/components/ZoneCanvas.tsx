'use client';

import { useRef, useState, useEffect, useCallback } from 'react';

interface Point {
  x: number;
  y: number;
}

interface ZoneCanvasProps {
  onZoneSaved?: () => void;
  onCameraSwitch?: () => void;
  cameraIndex?: number;
}

export default function ZoneCanvas({ onZoneSaved, onCameraSwitch, cameraIndex = 0 }: ZoneCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [points, setPoints] = useState<Point[]>([]);
  const [useSnapshot, setUseSnapshot] = useState(false);
  const [snapshotImage, setSnapshotImage] = useState<HTMLImageElement | null>(null);
  const [capturing, setCapturing] = useState(false);
  const [captureError, setCaptureError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [zoneName, setZoneName] = useState('');
  const [saving, setSaving] = useState(false);
  const [canvasSize, setCanvasSize] = useState({ w: 640, h: 480 });

  // Capture a snapshot from the backend (avoids all cross-origin canvas issues with MJPEG)
  const captureSnapshot = useCallback(async () => {
    setCapturing(true);
    setCaptureError('');
    try {
      const res = await fetch(`/api/v1/snapshot/${cameraIndex}?t=${Date.now()}`);
      if (!res.ok) throw new Error('No frame available');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const img = new Image();
      img.onload = () => {
        setSnapshotImage(img);
        setUseSnapshot(true);
        setCapturing(false);
      };
      img.onerror = () => {
        setCaptureError('Failed to load snapshot image.');
        setCapturing(false);
      };
      img.src = url;
    } catch {
      setCaptureError('Could not capture frame — camera may still be initialising.');
      setCapturing(false);
    }
  }, [cameraIndex]);

  const resetToLiveFeed = useCallback(() => {
    setUseSnapshot(false);
    setSnapshotImage(null);
    setPoints([]);
    setCaptureError('');
  }, []);

  // Notify parent and reset canvas when camera switches
  const handleCameraSwitch = useCallback(() => {
    resetToLiveFeed();
    onCameraSwitch?.();
  }, [resetToLiveFeed, onCameraSwitch]);

  // Draw canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = canvasSize.w;
    canvas.height = canvasSize.h;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Background
    if (snapshotImage && useSnapshot) {
      ctx.drawImage(snapshotImage, 0, 0, canvas.width, canvas.height);
    } else {
      ctx.fillStyle = '#0f172a';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      // Grid
      ctx.strokeStyle = '#1e293b';
      ctx.lineWidth = 1;
      for (let gx = 0; gx < canvas.width; gx += 32) {
        ctx.beginPath(); ctx.moveTo(gx, 0); ctx.lineTo(gx, canvas.height); ctx.stroke();
      }
      for (let gy = 0; gy < canvas.height; gy += 32) {
        ctx.beginPath(); ctx.moveTo(0, gy); ctx.lineTo(canvas.width, gy); ctx.stroke();
      }
      ctx.fillStyle = '#64748b';
      ctx.font = '14px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Click "Capture Frame" to freeze the video feed', canvas.width / 2, canvas.height / 2);
    }

    // Polygon fill
    if (points.length >= 3) {
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      for (let i = 1; i < points.length; i++) ctx.lineTo(points[i].x, points[i].y);
      ctx.closePath();
      ctx.fillStyle = 'rgba(250, 204, 21, 0.1)';
      ctx.fill();
    }

    // Polygon edges
    if (points.length >= 2) {
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      for (let i = 1; i < points.length; i++) ctx.lineTo(points[i].x, points[i].y);
      if (points.length >= 3) ctx.closePath();
      ctx.strokeStyle = '#facc15';
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 3]);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Vertices
    points.forEach((p, i) => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 8, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(250, 204, 21, 0.2)';
      ctx.fill();
      ctx.strokeStyle = '#facc15';
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
      ctx.fillStyle = '#facc15';
      ctx.fill();

      ctx.fillStyle = '#facc15';
      ctx.font = 'bold 10px JetBrains Mono, monospace';
      ctx.textAlign = 'center';
      ctx.fillText(`${i + 1}`, p.x, p.y - 14);
    });

    // Coordinate readout
    if (points.length > 0) {
      const last = points[points.length - 1];
      const nx = (last.x / canvas.width).toFixed(3);
      const ny = (last.y / canvas.height).toFixed(3);
      ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
      ctx.fillRect(canvas.width - 145, 8, 137, 24);
      ctx.fillStyle = '#94a3b8';
      ctx.font = '11px JetBrains Mono, monospace';
      ctx.textAlign = 'right';
      ctx.fillText(`Last: (${nx}, ${ny})`, canvas.width - 14, 24);
    }
  }, [points, snapshotImage, useSnapshot, canvasSize]);

  // Handle resize
  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        const w = containerRef.current.clientWidth;
        const h = Math.round(w * (480 / 640));
        setCanvasSize({ w, h: Math.min(h, 540) });
      }
    };
    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  // Canvas click handler
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!useSnapshot) return; // only draw on captured frame
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;
    setPoints((prev) => [...prev, { x, y }]);
  };

  // Save zone
  const saveZone = async () => {
    if (!zoneName.trim() || points.length < 3) return;
    setSaving(true);
    const canvas = canvasRef.current;
    const w = canvas?.width || 640;
    const h = canvas?.height || 480;

    const normalised = points.map((p) => [
      parseFloat((p.x / w).toFixed(5)),
      parseFloat((p.y / h).toFixed(5)),
    ]);

    try {
      const res = await fetch('/api/v1/zones', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: zoneName.trim(), type: 'POLYGON', points: normalised }),
      });
      if (res.ok) {
        setPoints([]);
        setZoneName('');
        setShowModal(false);
        onZoneSaved?.();
      }
    } catch {
      // Handle error
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-3">
      {/* Live feed (hidden once snapshot captured) */}
      {!useSnapshot && (
        <div className="feed-container rounded-xl overflow-hidden border border-slate-700/50">
          <img
            id="zone-feed-img"
            src={`/api/v1/video_feed/${cameraIndex}`}
            alt="Live feed"
            className="w-full h-auto block"
            crossOrigin="anonymous"
          />
        </div>
      )}

      {/* Canvas (always rendered; shown when snapshot active or points exist) */}
      <div ref={containerRef} className="relative">
        <canvas
          ref={canvasRef}
          onClick={handleCanvasClick}
          className={`w-full rounded-xl border border-slate-700/50 transition-shadow duration-300 ${
            useSnapshot ? 'cursor-crosshair' : 'cursor-default'
          } ${points.length >= 3 ? 'shadow-[0_0_20px_rgba(250,204,21,0.12)]' : ''}`}
          style={{ display: useSnapshot || points.length > 0 ? 'block' : 'none' }}
          id="zone-canvas"
        />
      </div>

      {/* Capture error */}
      {captureError && (
        <p className="text-xs text-neon-red font-mono px-1">{captureError}</p>
      )}

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        {!useSnapshot ? (
          <button
            onClick={captureSnapshot}
            disabled={capturing}
            className="btn-primary"
            id="capture-frame-btn"
          >
            {capturing ? (
              <>
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-900 border-t-transparent" />
                Capturing…
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Capture Frame
              </>
            )}
          </button>
        ) : (
          <button onClick={resetToLiveFeed} className="btn-ghost" id="recapture-btn">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Recapture
          </button>
        )}

        <button
          onClick={() => setPoints([])}
          className="btn-ghost"
          disabled={points.length === 0}
          id="clear-points-btn"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          Clear Points
        </button>

        <button
          onClick={() => setShowModal(true)}
          className="btn-primary"
          disabled={points.length < 3}
          id="save-zone-btn"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          Save Zone ({points.length} pts)
        </button>

        <span className="text-xs text-slate-500 font-mono ml-auto">
          {useSnapshot
            ? points.length >= 3
              ? '✓ Valid polygon'
              : `Need ${Math.max(0, 3 - points.length)} more point${3 - points.length !== 1 ? 's' : ''}`
            : 'Capture a frame first'}
        </span>
      </div>

      {/* Save modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="glass-card w-full max-w-sm p-6 animate-fade-in">
            <h3 className="text-lg font-semibold text-slate-100 mb-1">Name This Zone</h3>
            <p className="text-xs text-slate-400 mb-4">
              Assign a name to the {points.length}-point security zone.
            </p>
            <input
              type="text"
              value={zoneName}
              onChange={(e) => setZoneName(e.target.value)}
              placeholder="e.g. North Gate Perimeter"
              className="w-full rounded-lg border border-slate-600/50 bg-slate-800/60 px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-500 focus:border-neon-yellow/50 focus:outline-none focus:ring-1 focus:ring-neon-yellow/30 transition"
              autoFocus
              id="zone-name-input"
              onKeyDown={(e) => e.key === 'Enter' && saveZone()}
            />
            <div className="mt-4 flex gap-3 justify-end">
              <button onClick={() => setShowModal(false)} className="btn-ghost" id="zone-modal-cancel">
                Cancel
              </button>
              <button
                onClick={saveZone}
                disabled={!zoneName.trim() || saving}
                className="btn-primary"
                id="zone-modal-save"
              >
                {saving ? 'Saving…' : 'Create Zone'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
