import { useEffect, useState } from 'react'
import { api } from '@/lib/api'

export default function Settings() {
  const [len, setLen] = useState('medium')

  useEffect(() => {
    api.get('/settings').then(({ data }) => setLen(data.default_summary_length || 'medium'))
  }, [])

  function save() {
    api.post('/settings', { default_summary_length: len })
  }

  return (
    <div className="grid gap-4">
      <h2 className="text-xl font-semibold">Settings</h2>
      <label className="block">
        <span className="block text-sm mb-1">Default summary length</span>
        <select value={len} onChange={e=>setLen(e.target.value)} className="border rounded px-2 py-1 bg-white dark:bg-gray-800">
          <option value="short">Short</option>
          <option value="medium">Medium</option>
          <option value="long">Long</option>
        </select>
      </label>
      <button className="px-4 py-2 bg-blue-600 text-white rounded w-fit" onClick={save}>Save</button>
    </div>
  )
}
