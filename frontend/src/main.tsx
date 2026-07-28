import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css'; // Import our main CSS file with Tailwind directives
import App from './App';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);