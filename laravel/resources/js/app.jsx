import './bootstrap';
import 'leaflet/dist/leaflet.css';

import React from 'react';
import { createRoot } from 'react-dom/client';

import App from './hmap/App.jsx';

const root = createRoot(document.getElementById('hmap-root'));
root.render(<App />);
