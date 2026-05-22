import { useEffect, useState } from 'react'
import Chat from '../components/Chat'
import './DatasetList.css'

const REGIONS = [
  "valle d'aosta", 'piemonte', 'liguria', 'lombardia', 'trentino', 'alto adige',
  'veneto', 'friuli', 'emilia', 'romagna', 'toscana', 'umbria', 'marche',
  'lazio', 'abruzzo', 'molise', 'campania', 'puglia', 'basilicata',
  'calabria', 'sicilia', 'sardegna',
]

function hasRegion(name) {
  const lower = name.toLowerCase()
  return REGIONS.some(r => new RegExp(`\\b${r}\\b`).test(lower))
}

export default function DatasetList() {
  const [datasets, setDatasets]     = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState(null)
  const [search, setSearch]         = useState('')
  const [filteredIds, setFilteredIds]   = useState(null)
  const [regionFilter, setRegionFilter] = useState('all')
  const [categoryFilter, setCategoryFilter] = useState('all')

  useEffect(() => {
    Promise.all([
      fetch('/api/datasets').then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() }),
      fetch('/api/categories').then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() }),
    ])
      .then(([ds, cats]) => {
        setDatasets(ds)
        setCategories(cats)
        setLoading(false)
      })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [])

  const visible = datasets.filter(d => {
    const matchSearch =
      d.name_it.toLowerCase().includes(search.toLowerCase()) ||
      d.id.toLowerCase().includes(search.toLowerCase())
    const matchFilter   = filteredIds === null || filteredIds.includes(d.id)
    const matchRegion   =
      regionFilter === 'all' ||
      (regionFilter === 'with'    && hasRegion(d.name_it)) ||
      (regionFilter === 'without' && !hasRegion(d.name_it))
    const matchCategory =
      categoryFilter === 'all' || d.category_id === categoryFilter

    return matchSearch && matchFilter && matchRegion && matchCategory
  })

  return (
    <div className="dataset-page">
      <div className="page-header">
        <h1>Elenco Dataset ISTAT</h1>
        <p className="subtitle">
          {datasets.length > 0 ? `${visible.length} di ${datasets.length} dataset` : ''}
        </p>
      </div>

      <div className="page-body">
        <div className="list-col">
          <input
            className="search-input"
            type="text"
            placeholder="Cerca per nome o ID..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />

          <div className="filter-bar">
            <span className="filter-label">Categoria:</span>
            <select
              className="category-select"
              value={categoryFilter}
              onChange={e => setCategoryFilter(e.target.value)}
            >
              <option value="all">Tutte le categorie</option>
              {categories.map(c => (
                <option key={c.id} value={c.id}>{c.name_it}</option>
              ))}
            </select>
          </div>

          <div className="filter-bar">
            <span className="filter-label">Regioni:</span>
            {[
              { value: 'all',     label: 'Tutti' },
              { value: 'with',    label: 'Con regione' },
              { value: 'without', label: 'Senza regione' },
            ].map(opt => (
              <button
                key={opt.value}
                className={`filter-btn${regionFilter === opt.value ? ' active' : ''}`}
                onClick={() => setRegionFilter(opt.value)}
              >
                {opt.label}
              </button>
            ))}
          </div>

          {loading && <div className="state-msg">Caricamento in corso...</div>}
          {error && <div className="state-msg error">Errore: {error}</div>}

          {!loading && !error && (
            <div className="dataset-list">
              {visible.length === 0
                ? <div className="state-msg">Nessun risultato trovato.</div>
                : visible.map(d => (
                  <div
                    key={d.id}
                    className={`dataset-card${filteredIds && filteredIds.includes(d.id) ? ' highlighted' : ''}`}
                  >
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
                      {d.category_id && (
                        <span className="badge category">{d.category_id}</span>
                      )}
                    </div>
                  </div>
                ))
              }
            </div>
          )}
        </div>

        <div className="chat-col">
          <Chat
            onFilter={ids => setFilteredIds(ids)}
            onReset={() => setFilteredIds(null)}
          />
        </div>
      </div>
    </div>
  )
}
