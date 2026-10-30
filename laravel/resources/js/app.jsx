import './bootstrap';
import 'leaflet/dist/leaflet.css';

import React from 'react';
import { createRoot } from 'react-dom/client';

import App from './hmap/App.jsx';
import { applyTheme } from './hmap/theme.js';

applyTheme();  // before the first render, so the page never flashes light in dark mode
const root = createRoot(document.getElementById('hmap-root'));
root.render(<App />);
