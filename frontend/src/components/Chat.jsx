import { useEffect, useRef, useState } from 'react'
import './Chat.css'

export default function Chat({ onFilter, onReset }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Ciao! Posso aiutarti a trovare i dataset ISTAT. Dimmi cosa cerchi.' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function send() {
    const text = input.trim()
    if (!text || loading) return

    setInput('')
    setMessages(prev => [...prev, { role: 'user', text }])
    setLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      })
      if (res.status === 429) {
        const err = await res.json()
        setMessages(prev => [...prev, { role: 'assistant', text: err.detail, rateLimit: true }])
        return
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()

      setMessages(prev => [...prev, { role: 'assistant', text: data.reply }])

      if (data.filtered_ids && data.filtered_ids.length > 0) {
        onFilter(data.filtered_ids)
      } else {
        onReset()
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', text: `Errore: ${e.message}`, error: true }])
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <span>Assistente AI</span>
        <button className="reset-btn" onClick={onReset} title="Rimuovi filtro">✕</button>
      </div>

      <div className="chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}${m.error ? ' error' : ''}${m.rateLimit ? ' rate-limit' : ''}`}>
            {m.text}
          </div>
        ))}
        {loading && (
          <div className="bubble assistant loading">
            <span className="dot" /><span className="dot" /><span className="dot" />
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-row">
        <textarea
          className="chat-input"
          placeholder="Chiedi qualcosa sui dataset..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={2}
          disabled={loading}
        />
        <button className="send-btn" onClick={send} disabled={loading || !input.trim()}>
          Invia
        </button>
      </div>
    </div>
  )
}
