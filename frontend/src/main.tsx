import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// Apply persisted theme before first paint to avoid flash
const savedTheme = localStorage.getItem("lh_theme") ?? "dark";
document.documentElement.setAttribute("data-theme", savedTheme);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
