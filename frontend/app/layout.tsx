import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Virtual Fence — Security Operations Console',
  description:
    'Enterprise Autonomous Perimeter Intrusion & Spatial Boundary System. Real-time surveillance, zone-based intrusion detection, and incident management.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-950 text-slate-200 antialiased">
        <div className="flex min-h-screen">
          {/* ── Sidebar ── */}
          <aside className="hidden lg:flex w-64 flex-col border-r border-slate-800/80 bg-slate-900/50 backdrop-blur-md">
            {/* Brand */}
            <div className="flex items-center gap-3 px-5 py-6 border-b border-slate-800/60">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-neon-yellow to-neon-amber shadow-lg">
                <svg className="h-5 w-5 text-slate-900" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div>
                <h1 className="text-sm font-bold tracking-wide text-slate-100">Virtual Fence</h1>
                <p className="text-[10px] font-medium uppercase tracking-[0.2em] text-neon-yellow/80">Sentinel</p>
              </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-3 py-4 space-y-1">
              <a href="/" className="nav-link active" id="nav-dashboard">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
                Security Console
              </a>
              <a href="/settings/zones" className="nav-link" id="nav-zones">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Zone Calibration
              </a>
            </nav>

            {/* Footer */}
            <div className="border-t border-slate-800/60 px-5 py-4">
              <div className="flex items-center gap-2">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-neon-green opacity-75"></span>
                  <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-neon-green"></span>
                </span>
                <span className="text-xs text-slate-400">System Online</span>
              </div>
              <p className="mt-1 text-[10px] text-slate-600">v1.0.0 • Enterprise</p>
            </div>
          </aside>

          {/* ── Main content ── */}
          <main className="flex-1 overflow-y-auto">
            {/* Mobile header */}
            <header className="lg:hidden flex items-center justify-between border-b border-slate-800/80 bg-slate-900/80 backdrop-blur-md px-4 py-3">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-neon-yellow to-neon-amber">
                  <svg className="h-4 w-4 text-slate-900" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <span className="text-sm font-bold text-slate-100">Virtual Fence</span>
              </div>
              <nav className="flex gap-2">
                <a href="/" className="btn-ghost text-xs">Console</a>
                <a href="/settings/zones" className="btn-ghost text-xs">Zones</a>
              </nav>
            </header>

            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
