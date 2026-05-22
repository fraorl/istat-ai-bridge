import { Routes, Route, NavLink } from 'react-router-dom'
import DatasetList from './pages/DatasetList'
import './App.css'

function App() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span className="logo-text">ISTAT Bridge</span>
        </div>
        <nav className="sidebar-nav">
          <NavLink to="/" end className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
            Elenco Dataset ISTAT
          </NavLink>
        </nav>
      </aside>
      <main className="content">
        <Routes>
          <Route path="/" element={<DatasetList />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
