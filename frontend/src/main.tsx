import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App';
import { reportWebVitals } from './utils/reportWebVitals';

const container = document.getElementById('root');
if (!container) {
  throw new Error("Failed to find the root element to mount React application.");
}

const root = createRoot(container);
root.render(
  <StrictMode>
    <App />
  </StrictMode>
);

// Send vitals to GA4
reportWebVitals((metric) => {
  const { name, delta, value, id } = metric;
  if (typeof window !== 'undefined' && (window as any).gtag) {
    (window as any).gtag('event', name, {
      event_category: 'Web Vitals',
      event_action: name,
      event_value: Math.round(name === 'CLS' ? delta * 1000 : delta),
      event_label: id,
      non_interaction: true,
    });
  }
});
