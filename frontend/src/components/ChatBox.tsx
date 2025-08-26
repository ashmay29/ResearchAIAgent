import { useState } from 'react'

export default function ChatBox() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<{role:'user'|'assistant', content:string}[]>([])

  function send() {
    if (!input.trim()) return
    // Placeholder – hook to backend follow-up QA endpoint when available
    setMessages(m => [...m, { role: 'user', content: input }, { role: 'assistant', content: 'Answer TBD (connect to backend QA).' }])
    setInput('')
  }

  return (
    <section className="border rounded-lg p-4">
      <h3 className="text-lg font-semibold mb-2">Ask follow-up questions</h3>
      <div className="h-48 overflow-auto border rounded p-2 mb-3 bg-white dark:bg-gray-800">
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'text-right' : 'text-left'}>
            <span className={`inline-block px-3 py-2 rounded my-1 ${m.role==='user'?'bg-blue-600 text-white':'bg-gray-200 dark:bg-gray-700'}`}>{m.content}</span>
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input className="flex-1 border rounded px-2 py-2 bg-white dark:bg-gray-800" value={input} onChange={e=>setInput(e.target.value)} placeholder="Ask about the paper..." />
        <button className="px-4 py-2 bg-blue-600 text-white rounded" onClick={send}>Send</button>
      </div>
    </section>
  )
}
