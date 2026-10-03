import { useEffect, useState, useRef } from 'react';
import './App.css';
import logo from './assets/logo.png';

const MAIN_APP_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const LOADING_MESSAGES = [
  "Connecting to Lakshmi Broliers Hub...",
  "Selecting today's farm-fresh cuts...",
  "Checking today's fresh-cut inventory...",
  "Calibrating custom cut preferences...",
  "Preparing vacuum packaging station...",
  "Almost ready! Launching store...",
];

export default function App() {
  const [progress, setProgress] = useState(15);
  const [messageIndex, setMessageIndex] = useState(0);
  const [isReady, setIsReady] = useState(false);
  const [fadingOut, setFadingOut] = useState(false);
  const [serverOnline, setServerOnline] = useState(false);
  const attemptRef = useRef(0);

  // Cycle loading messages
  useEffect(() => {
    if (isReady) return;
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % LOADING_MESSAGES.length);
    }, 2400);
    return () => clearInterval(interval);
  }, [isReady]);

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

    const checkServerHealth = async () => {
      attemptRef.current += 1;
      try {
        await fetch(MAIN_APP_URL, { method: 'HEAD', mode: 'no-cors' });
        if (!cancelled) {
          setServerOnline(true);
          setIsReady(true);
          setProgress(100);

          setTimeout(() => {
            setFadingOut(true);
            setTimeout(() => {
              window.location.href = MAIN_APP_URL;
            }, 700);
          }, 900);
        }
      } catch (err) {
        if (!cancelled) {
          setTimeout(checkServerHealth, 2000);
        }
      }
    };

    const initialTimer = setTimeout(checkServerHealth, 600);

    const fallbackTimer = setTimeout(() => {
      if (!cancelled && !isReady) {
        setServerOnline(true);
        setIsReady(true);
        setProgress(100);
        setTimeout(() => {
          setFadingOut(true);
          setTimeout(() => {
            window.location.href = MAIN_APP_URL;
          }, 700);
        }, 600);
      }
    }, 25000);

    return () => {
      cancelled = true;
      clearTimeout(initialTimer);
      clearTimeout(fallbackTimer);
    };
  }, [isReady]);

  // Circular progress math (radius: 76px)
  const radius = 76;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  return (
    <div className={`relative min-h-screen w-full bg-[#fdfbfb] text-on-surface flex flex-col justify-between items-center px-4 py-8 overflow-hidden select-none font-sans antialiased transition-all duration-700 ${fadingOut ? 'animate-fade-out-screen' : ''}`}>

      {/* 1. LARGE OVERLAPPING BACKGROUND WATERMARK LOGO */}
      <div className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[520px] h-[520px] sm:w-[680px] sm:h-[680px] opacity-[0.06] mix-blend-multiply select-none z-0 filter blur-[1px] animate-slow-spin">
        <img src={logo} alt="" className="w-full h-full object-contain" />
      </div>

      {/* 2. AMBIENT RADIAL BACKGROUND GLOWS OVERLAPPING WITH WATERMARK */}
      <div className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-tr from-red-600/20 via-primary/15 to-amber-500/15 rounded-full blur-3xl animate-pulse-glow z-0" />
      <div className="pointer-events-none absolute -top-32 -right-32 w-96 h-96 bg-primary/10 rounded-full blur-3xl z-0" />
      <div className="pointer-events-none absolute -bottom-32 -left-32 w-96 h-96 bg-amber-600/10 rounded-full blur-3xl z-0" />

      {/* Subtle Geometry Grid */}
      <div className="pointer-events-none absolute inset-0 opacity-[0.035] bg-[radial-gradient(#8f000d_1.2px,transparent_1.2px)] [background-size:24px_24px] z-0" />

      {/* TOP HEADER: Brand Pill & Live Status */}
      <header className="relative z-20 w-full max-w-md flex items-center justify-between pt-2">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/90 backdrop-blur-md border border-outline-variant/60 shadow-xs">
          <span className={`w-2 h-2 rounded-full ${isReady ? 'bg-emerald-500' : 'bg-primary animate-ping'}`} />
          <span className="text-[11px] font-bold text-on-surface tracking-wide uppercase">
            {serverOnline ? 'Hub Online' : 'Connecting Hub'}
          </span>
        </div>

        <div className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-white/90 backdrop-blur-md border border-outline-variant/60 shadow-xs">
          <span className="material-symbols-outlined text-[15px] text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>
            location_on
          </span>
          <span className="text-[11px] font-semibold text-on-surface-variant">Uchipuli Delivery</span>
        </div>
      </header>

      {/* CENTERPIECE: OVERLAPPING LOGO, ORBITAL PROGRESS & AURA */}
      <div className="relative z-20 flex flex-col items-center justify-center my-auto w-full max-w-md">

        {/* Emblem Layered Container */}
        <div className="relative flex items-center justify-center mb-6">

          {/* Layer A: Rotating Watermark Seal Ring */}
          <div className="absolute -inset-10 rounded-full border border-dashed border-primary/25 animate-slow-spin pointer-events-none" />
          <div className="absolute -inset-16 rounded-full border border-dotted border-amber-600/20 animate-reverse-spin pointer-events-none" />

          {/* Layer B: Glowing Halo Aura behind Logo */}
          <div className="absolute -inset-4 rounded-full bg-gradient-to-tr from-primary/35 via-red-500/25 to-amber-400/35 blur-xl" />

          {/* Layer C: Circular SVG Progress Ring hugging the Logo */}
          <svg className="relative w-48 h-48 sm:w-56 sm:h-56 transform -rotate-90 drop-shadow-lg" viewBox="0 0 176 176">
            {/* Background Track */}
            <circle
              cx="88"
              cy="88"
              r={radius}
              className="text-stone-200/90 stroke-current"
              strokeWidth="5"
              fill="transparent"
            />
            {/* Animated Progress Gradient */}
            <circle
              cx="88"
              cy="88"
              r={radius}
              stroke="url(#progressGradient)"
              strokeWidth="6.5"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              fill="transparent"
              className="transition-all duration-500 ease-out"
            />
            <defs>
              <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#8f000d" />
                <stop offset="50%" stopColor="#b22222" />
                <stop offset="100%" stopColor="#eab308" />
              </linearGradient>
            </defs>
          </svg>

          {/* Layer D: Central Overlapping Logo Seal with Glassmorphic Backdrop */}
          <div className="absolute inset-4 rounded-full bg-white/95 backdrop-blur-md p-2.5 shadow-[0_16px_40px_-8px_rgba(143,0,13,0.25)] border-2 border-primary/20 flex items-center justify-center overflow-hidden">
            <div className="w-full h-full rounded-full bg-gradient-to-br from-[#fffafa] via-white to-[#fbf1ee] flex items-center justify-center border border-primary/10 shadow-inner overflow-hidden p-2 group">
              <img
                src={logo}
                alt="Lakshmi Broliers"
                className="w-full h-full object-contain filter drop-shadow-md transform group-hover:scale-105 transition-transform duration-500"
              />
            </div>
          </div>

          {/* Layer E: Overlapping Floating Top Badge */}
          <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 z-30 animate-float-badge">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-gradient-to-r from-primary to-primary-container text-white text-[10px] font-extrabold uppercase tracking-wider shadow-md border border-white/30 whitespace-nowrap">
              <span className="material-symbols-outlined text-[13px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                bolt
              </span>
              <span>45m Express</span>
            </div>
          </div>

          {/* Layer F: Overlapping Floating Bottom Progress Badge */}
          <div className="absolute -bottom-3.5 left-1/2 -translate-x-1/2 z-30">
            <div className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-white text-on-surface text-xs font-black tracking-wide shadow-lg border border-outline-variant/60">
              <span className={`w-2 h-2 rounded-full ${isReady ? 'bg-emerald-500' : 'bg-primary animate-pulse'}`} />
              <span className="text-primary font-headline">{isReady ? '100' : progress}%</span>
            </div>
          </div>

        </div>

        {/* Brand App Name: "Lakshmi Broliers" */}
        <div className="text-center px-4 mt-2">
          <h1 className="font-headline text-3xl sm:text-4xl font-black tracking-tight text-primary uppercase leading-tight">
            LAKSHMI <span className="text-primary-container font-light">BROLIERS</span>
          </h1>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-on-surface-variant/90 mt-1">
            Farm-Fresh Poultry &amp; Daily Cuts
          </p>
          <p className="text-xs text-on-surface-variant max-w-[280px] mx-auto mt-2 leading-relaxed">
            Hygienically cut on order, vacuum-sealed, and delivered within 45-60 mins.
          </p>
        </div>

      </div>

      {/* BOTTOM SECTION: Progress Status & Trust Pillars */}
      <div className="relative z-20 w-full max-w-md flex flex-col items-center gap-5 pb-2">

        {/* Dynamic Loading Message & Linear Track Bar */}
        <div className="w-full bg-white/90 backdrop-blur-md rounded-2xl border border-outline-variant/60 p-4 shadow-sm">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="font-semibold text-on-surface flex items-center gap-2 truncate">
              {!isReady ? (
                <span className="w-2 h-2 rounded-full bg-primary animate-ping shrink-0" />
              ) : (
                <span className="material-symbols-outlined text-emerald-600 text-[18px] shrink-0" style={{ fontVariationSettings: "'FILL' 1" }}>
                  check_circle
                </span>
              )}
              <span className="truncate">{isReady ? "Ready! Launching Store..." : LOADING_MESSAGES[messageIndex]}</span>
            </span>
            <span className="text-[11px] font-bold text-primary shrink-0 ml-2">{isReady ? '100%' : `${progress}%`}</span>
          </div>

          <div className="w-full h-2 bg-stone-100 rounded-full overflow-hidden p-[1px] border border-stone-200 shadow-inner">
            <div
              className="h-full bg-gradient-to-r from-primary via-primary-container to-amber-500 rounded-full transition-all duration-300 ease-out shadow-xs"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Bento Trust Badges */}
        <div className="w-full grid grid-cols-3 gap-2 text-center">
          <div className="p-2.5 rounded-xl bg-white/85 backdrop-blur-sm border border-outline-variant/40 shadow-2xs">
            <span className="material-symbols-outlined text-[18px] text-primary mb-0.5">content_cut</span>
            <p className="text-[10px] font-bold text-on-surface">Cut on Order</p>
            <p className="text-[9px] text-on-surface-variant">Cut Fresh to Order</p>
          </div>
          <div className="p-2.5 rounded-xl bg-white/85 backdrop-blur-sm border border-outline-variant/40 shadow-2xs">
            <span className="material-symbols-outlined text-[18px] text-emerald-700 mb-0.5" style={{ fontVariationSettings: "'FILL' 1" }}>verified</span>
            <p className="text-[10px] font-bold text-on-surface">100% Halal</p>
            <p className="text-[9px] text-on-surface-variant">Lab Certified</p>
          </div>
          <div className="p-2.5 rounded-xl bg-white/85 backdrop-blur-sm border border-outline-variant/40 shadow-2xs">
            <span className="material-symbols-outlined text-[18px] text-amber-600 mb-0.5">ac_unit</span>
            <p className="text-[10px] font-bold text-on-surface">0-4°C Packed</p>
            <p className="text-[9px] text-on-surface-variant">Vacuum Sealed</p>
          </div>
        </div>

      </div>

    </div>
  );
}
