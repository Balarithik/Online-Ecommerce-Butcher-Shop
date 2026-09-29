import { useEffect, useState } from 'react';
import './App.css';
import logo from './assets/logo_aramcuts.png';

const MAIN_APP_URL = 'https://lakshmi-broliers.onrender.com';

function Splash() {
  const [loading, setLoading] = useState(true);

  // Poll the main app to see if it's reachable
  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      try {
        const response = await fetch(MAIN_APP_URL, { method: 'HEAD', mode: 'no-cors' });
        // If we get any response (or no-cors succeeds), consider it loaded
        if (!cancelled) {
          window.location.href = MAIN_APP_URL;
        }
      } catch (e) {
        // Not reachable yet, retry after a short delay
        if (!cancelled) {
          setTimeout(check, 1500);
        }
      }
    };
    // Initial delay before first check
    setTimeout(check, 500);
    // Fallback timeout: after 10 seconds force redirect
    const fallback = setTimeout(() => {
      if (!cancelled) {
        window.location.href = MAIN_APP_URL;
      }
    }, 10000);
    return () => {
      cancelled = true;
      clearTimeout(fallback);
    };
  }, []);

  return (
    <div className="splash-container">
      <img src={logo} alt="AramCuts" className="splash-logo" />
      <div className="spinner" />
      <p className="loading-text">App is loading, please wait…</p>
    </div>
  );
}

export default Splash;
