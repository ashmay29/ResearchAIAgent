import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '@/lib/api'

export default function History() {
  const [items, setItems] = useState<{id:string, status:string}[]>([])

  useEffect(() => {
    api.get('/history/list').then(({ data }) => setItems(data.items || []))
  }, [])

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Saved Analyses</h2>
      <div className="space-y-2">
        {items.map(i => (
          <Link key={i.id} to={`/analysis/${i.id}`} className="block border rounded p-3 hover:bg-gray-50 dark:hover:bg-gray-800">
            <div className="font-medium">Job {i.id}</div>
            <div className="text-sm text-gray-600 dark:text-gray-300">Status: {i.status}</div>
          </Link>
        ))}
      </div>
    </div>
  )
}
