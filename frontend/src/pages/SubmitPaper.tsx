import { useState } from 'react'
import FileUpload from '@/components/FileUpload'
import OptionsPanel from '@/components/OptionsPanel'
import { api } from '@/lib/api'
import { useNavigate } from 'react-router-dom'

export default function SubmitPaper() {
  const [paperId, setPaperId] = useState<string | null>(null)
  const [opts, setOpts] = useState({ summary_length: 'medium' as const, focus: '', feedback_type: 'critique' as const })
  const [loading, setLoading] = useState(false)
  const nav = useNavigate()

  async function startAnalysis() {
    if (!paperId) {
      alert('Please upload a PDF first.')
      return
    }
    setLoading(true)
    try {
      const { data } = await api.post('/analysis/run', { paper_id: paperId, options: opts })
      nav(`/analysis/${data.job_id}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid gap-6">
      <h2 className="text-xl font-semibold">Submit a paper</h2>
      <FileUpload onUploaded={setPaperId} />

      <details className="border rounded-lg p-4" open>
        <summary className="cursor-pointer font-medium">Advanced options</summary>
        <div className="mt-4">
          <OptionsPanel options={opts} onChange={setOpts} />
        </div>
      </details>

      <button className="px-4 py-2 bg-green-600 text-white rounded disabled:opacity-50" onClick={startAnalysis} disabled={!paperId || loading}>
        {loading ? 'Starting...' : 'Submit'}
      </button>
    </div>
  )
}
