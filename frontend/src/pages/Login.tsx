import { useState } from 'react'
import { api, setAuth } from '@/lib/api'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [msg, setMsg] = useState('')

  async function submit() {
    try {
      const { data } = await api.post('/auth/login', { email, password })
      setAuth(data.token)
      setMsg('Logged in!')
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || 'Login failed')
    }
  }

  return (
    <div className="max-w-sm mx-auto grid gap-3">
      <h2 className="text-xl font-semibold">Login</h2>
      <input className="border rounded px-2 py-2 bg-white dark:bg-gray-800" placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} />
      <input type="password" className="border rounded px-2 py-2 bg-white dark:bg-gray-800" placeholder="Password" value={password} onChange={e=>setPassword(e.target.value)} />
      <button className="px-4 py-2 bg-blue-600 text-white rounded" onClick={submit}>Login</button>
      {msg && <div className="text-sm text-gray-600 dark:text-gray-300">{msg}</div>}
    </div>
  )
}
