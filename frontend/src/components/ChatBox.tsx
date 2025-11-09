import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, MessageCircle } from 'lucide-react'
import GlassCard from './ui/GlassCard'

export default function ChatBox() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<{role:'user'|'assistant', content:string}[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  function send() {
    if (!input.trim()) return
    // Placeholder – hook to backend follow-up QA endpoint when available
    setMessages(m => [...m, { role: 'user', content: input }, { role: 'assistant', content: 'Answer TBD (connect to backend QA).' }])
    setInput('')
  }

  function handleKeyPress(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <GlassCard className="overflow-hidden">
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <MessageCircle className="h-5 w-5" />
          Ask follow-up questions
        </h3>
      </div>
      <div className="p-6">
        <div className="h-64 overflow-y-auto border border-blue-100 dark:border-blue-900/40 rounded-xl p-4 mb-4 bg-gradient-to-br from-gray-50 to-blue-50/30 dark:from-gray-900/50 dark:to-blue-900/10 backdrop-blur-sm">
          <AnimatePresence mode="popLayout">
            {messages.length === 0 ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="h-full flex items-center justify-center text-gray-400 dark:text-gray-600 text-sm"
              >
                No messages yet. Ask a question about the paper!
              </motion.div>
            ) : (
              messages.map((m, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ duration: 0.3 }}
                  className={`mb-3 ${m.role === 'user' ? 'text-right' : 'text-left'}`}
                >
                  <span className={`
                    inline-block px-4 py-2.5 rounded-2xl text-sm
                    ${m.role === 'user'
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/30'
                      : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 shadow-md'
                    }
                  `}>
                    {m.content}
                  </span>
                </motion.div>
              ))
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>
        <div className="flex gap-3">
          <input
            className="flex-1 border border-blue-200 dark:border-blue-800/50 rounded-xl px-4 py-3 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 transition-all duration-300 hover:border-blue-300 dark:hover:border-blue-700 focus:border-blue-500 dark:focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about the paper..."
          />
          <button
            className="px-5 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-medium shadow-lg shadow-blue-500/20 hover:shadow-xl hover:shadow-blue-500/30 hover:scale-105 active:scale-95 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            onClick={send}
            disabled={!input.trim()}
          >
            <Send className="h-4 w-4" />
            Send
          </button>
        </div>
      </div>
    </GlassCard>
  )
}
