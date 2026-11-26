import { useEffect, useState } from 'react';
import './App.css';
import logo from './assets/logo.png';

// Vite injects this value at build time. Keep a production fallback so a
// missing static-host environment variable cannot crash the React app.
const CONFIGURED_API_URL = import.meta.env.VITE_API_BASE_URL?.trim()
  || 'https://lakshmi-broliers.onrender.com';
const MAIN_APP_URL = new URL(CONFIGURED_API_URL).origin;
const HEALTH_CHECK_URL = new URL('/healthz/', MAIN_APP_URL).toString();

export default function App() {
  const [progress, setProgress] = useState(15);
  const [isReady, setIsReady] = useState(false);
  const [serverOnline, setServerOnline] = useState(false);
  const [connectionFailed, setConnectionFailed] = useState(false);
  const [retryNonce, setRetryNonce] = useState(0);

  // Smooth progress increments
  useEffect(() => {
    if (isReady) return;
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 94) return 94;
        const increment = Math.max(1, Math.floor((95 - prev) / 6));
        return Math.min(94, prev + increment);
      });
    }, 600);
    return () => clearInterval(interval);
  }, [isReady]);

  // Health check polling against live backend server
  useEffect(() => {
    let cancelled = false;
    let retryCount = 0;
    const MAX_RETRIES = 10;
    let initialTimer;
    let retryTimer;
    let redirectTimer;
    let activeController;

    const checkServerHealth = async () => {
      if (retryCount >= MAX_RETRIES) {
        setServerOnline(false);
        setConnectionFailed(true);
        setProgress(100);
        return;
      }
      activeController = new AbortController();
      const requestTimeout = setTimeout(() => activeController.abort(), 5000);

      try {
        const response = await fetch(HEALTH_CHECK_URL, {
          method: 'GET',
          headers: { Accept: 'application/json' },
          cache: 'no-store',
          signal: activeController.signal,
        });
        if (!response.ok) throw new Error(`Health check returned ${response.status}.`);
        const health = await response.json();
        if (health.status !== 'ok') throw new Error('Main app is not healthy yet.');

        if (!cancelled) {
          setServerOnline(true);
          setConnectionFailed(false);
          setIsReady(true);
          setProgress(100);

          redirectTimer = setTimeout(() => {
            window.location.href = MAIN_APP_URL;
          }, 900);
        }
      } catch (err) {
        retryCount++;
        if (!cancelled) {
          setProgress(Math.max(20, 94 - retryCount * 5));
          retryTimer = setTimeout(checkServerHealth, 2000);
        }
      } finally {
        clearTimeout(requestTimeout);
      }
    };

    initialTimer = setTimeout(checkServerHealth, 600);

    return () => {
      cancelled = true;
      activeController?.abort();
      clearTimeout(initialTimer);
      clearTimeout(retryTimer);
      clearTimeout(redirectTimer);
    };
  }, [retryNonce]);


  return (
    <div className="relative min-h-screen w-full bg-[#faf8f6] text-on-surface flex flex-col justify-between items-center px-6 py-10 overflow-hidden select-none font-sans antialiased">

      {/* TOP: Clean status & location */}
      <header className="relative z-10 w-full max-w-md flex items-center justify-between text-xs text-stone-600">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${isReady ? 'bg-emerald-600' : 'bg-primary'}`} />
          <span className="font-semibold uppercase tracking-wider text-[11px]">
            {connectionFailed ? 'Connection unavailable' : serverOnline ? 'Delivery Hub Active' : 'Connecting to Hub'}
          </span>
        </div>

        <div className="flex items-center gap-1.5 text-stone-500 text-[11px] font-medium">
          <span className="material-symbols-outlined text-[15px] text-stone-600">location_on</span>
          <span>Lakshmi Broliers, Railway station road, Uchipuli, Ramanathapuram 623534</span>
        </div>
      </header>

      {/* CENTER: Authentic Brand Identity & Clean Progress Indicator */}
      <div className="relative z-10 flex flex-col items-center justify-center my-auto w-full max-w-sm text-center">
        {/* Brand Logo in clean, grounded frame */}
        <div className="w-28 h-28 sm:w-32 sm:h-32 rounded-2xl bg-white border border-stone-200/80 shadow-sm p-4 flex items-center justify-center mb-6">
          <img
            src={logo}
            alt="Lakshmi Broliers"
            className="w-full h-full object-contain"
          />
        </div>

        {/* Brand App Name */}
        <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-stone-900 uppercase">
          Lakshmi <span className="text-primary font-bold">Broliers</span>
        </h1>
        <p className="text-xs font-semibold uppercase tracking-widest text-stone-500 mt-1">
          Daily Fresh Farm Butchery
        </p>

        {/* Dynamic Loading Message & Linear Minimal Progress Bar */}
        <div className="w-full mt-8">
          <div className="flex items-center justify-between text-xs text-stone-600 mb-2 font-medium">
            <span className="truncate">{connectionFailed ? "We could not reach the store. Check your connection and try again." : isReady ? "Ready! Launching Store..." : "Preparing today's fresh cuts..."}</span>
            <span className="text-primary font-bold ml-2 shrink-0">{isReady ? '100%' : `${progress}%`}</span>
          </div>

          <div className="w-full h-1.5 bg-stone-200/70 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary rounded-full transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
          {connectionFailed && (
            <button
              type="button"
              onClick={() => {
                setConnectionFailed(false);
                setProgress(15);
                setRetryNonce((value) => value + 1);
              }}
              className="mt-5 rounded-full bg-primary px-5 py-2.5 text-sm font-semibold text-white transition hover:opacity-90"
            >
              Try again
            </button>
          )}
        </div>
      </div>

      {/* FOOTER: Grounded quality reassurance */}
      <footer className="relative z-10 w-full max-w-sm flex items-center justify-center gap-6 text-[11px] font-medium text-stone-500 border-t border-stone-200/60 pt-4">
        <span>Cut to Order</span>
        <span>•</span>
        <span>100% Halal</span>
        <span>•</span>
        <span>Direct Farm Supply</span>
      </footer>

    </div>
  );
}
