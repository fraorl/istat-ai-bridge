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

const YEAR_RE = /\b(19|20)\d{2}\b/g

function baseName(name) {
  return name
    .replace(YEAR_RE, '')
    .replace(/\s*[-–—]\s*$/, '')
    .replace(/\(\s*\)/g, '')
    .replace(/\s{2,}/g, ' ')
    .trim()
}

function groupDatasets(datasets) {
  const map = new Map()
  for (const d of datasets) {
    const years = [...d.name_it.matchAll(YEAR_RE)].map(m => m[0])
    const key   = years.length > 0 ? baseName(d.name_it) : d.name_it

    if (!map.has(key)) {
      map.set(key, { key, name_it: key, name_en: baseName(d.name_en || ''), items: [] })
    }
    map.get(key).items.push({ ...d, _years: years })
  }

  return Array.from(map.values()).map(g => ({
    ...g,
    years: [...new Set(g.items.flatMap(d => d._years))].sort(),
    description_it: g.items[0].description_it,
  }))
}

export default function DatasetList() {
  const [datasets, setDatasets]         = useState([])
  const [loading, setLoading]           = useState(true)
  const [error, setError]               = useState(null)
  const [search, setSearch]             = useState('')
  const [filteredIds, setFilteredIds]   = useState(null)
  const [regionFilter, setRegionFilter] = useState('all')

  useEffect(() => {
    fetch('/api/datasets')
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(data => { setDatasets(data); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [])

  // filtra i dataset singoli, poi raggruppa il risultato
  const filtered = datasets.filter(d => {
    const matchSearch =
      d.name_it.toLowerCase().includes(search.toLowerCase()) ||
      d.id.toLowerCase().includes(search.toLowerCase())
    const matchFilter = filteredIds === null || filteredIds.includes(d.id)
    const matchRegion =
      regionFilter === 'all' ||
      (regionFilter === 'with'    && hasRegion(d.name_it)) ||
      (regionFilter === 'without' && !hasRegion(d.name_it))
    return matchSearch && matchFilter && matchRegion
  })

  const groups = groupDatasets(filtered)

  const isHighlighted = g =>
    filteredIds && g.items.some(d => filteredIds.includes(d.id))

  return (
    <div className="dataset-page">
      <div className="page-header">
        <h1>Elenco Dataset ISTAT</h1>
        <p className="subtitle">
          {datasets.length > 0
            ? `${groups.length} gruppi · ${filtered.length} di ${datasets.length} dataset`
            : ''}
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
          {error   && <div className="state-msg error">Errore: {error}</div>}

          {!loading && !error && (
            <div className="dataset-list">
              {groups.length === 0
                ? <div className="state-msg">Nessun risultato trovato.</div>
                : groups.map(g => (
                  <div
                    key={g.key}
                    className={`dataset-card${isHighlighted(g) ? ' highlighted' : ''}`}
                  >
                    <div className="dataset-name">{g.name_it}</div>
                    {g.name_en && g.name_en !== g.name_it && (
                      <div className="dataset-name-en">{g.name_en}</div>
                    )}
                    {g.description_it && (
                      <div className="dataset-desc">{g.description_it}</div>
                    )}
                    <div className="dataset-meta">
                      {g.years.length > 0
                        ? g.years.map(y => (
                          <span key={y} className="badge year">{y}</span>
                        ))
                        : <span className="badge">{g.items[0].id}</span>
                      }
                      {g.items.length > 1 && (
                        <span className="badge secondary">{g.items.length} dataset</span>
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
