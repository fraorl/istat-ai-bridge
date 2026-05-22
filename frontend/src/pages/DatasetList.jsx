import { useEffect, useState } from 'react'
import './DatasetList.css'

export default function DatasetList() {
  const [datasets, setDatasets] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')

  useEffect(() => {
    fetch('/api/datasets')
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(data => { setDatasets(data); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [])

  const filtered = datasets.filter(d =>
    d.name_it.toLowerCase().includes(search.toLowerCase()) ||
    d.id.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="dataset-page">
      <div className="page-header">
        <h1>Elenco Dataset ISTAT</h1>
        <p className="subtitle">{datasets.length > 0 ? `${datasets.length} dataset disponibili` : ''}</p>
      </div>

      <input
        className="search-input"
        type="text"
        placeholder="Cerca per nome o ID..."
        value={search}
        onChange={e => setSearch(e.target.value)}
      />

      {loading && <div className="state-msg">Caricamento in corso...</div>}
      {error && <div className="state-msg error">Errore: {error}</div>}

      {!loading && !error && (
        <div className="dataset-list">
          {filtered.length === 0
            ? <div className="state-msg">Nessun risultato trovato.</div>
            : filtered.map(d => (
              <div key={d.id} className="dataset-card">
                <div className="dataset-name">{d.name_it}</div>
                {d.name_en && d.name_en !== d.name_it && (
                  <div className="dataset-name-en">{d.name_en}</div>
                )}
                {d.description_it && (
                  <div className="dataset-desc">{d.description_it}</div>
                )}
                <div className="dataset-meta">
                  <span className="badge">{d.id}</span>
                  <span className="badge secondary">v{d.version}</span>
                </div>
              </div>
            ))
          }
        </div>
      )}
    </div>
  )
}
