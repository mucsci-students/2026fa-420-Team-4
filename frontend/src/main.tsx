import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import MainMenu from './MainMenu.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <MainMenu />
  </StrictMode>,
)
