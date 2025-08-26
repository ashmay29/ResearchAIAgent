import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '@/lib/api'
import LoadingStatus from '@/components/LoadingStatus'
import SummarySection from '@/components/SummarySection'
import FeedbackSection from '@/components/FeedbackSection'
import FindingsList from '@/components/FindingsList'
import CitationViewer from '@/components/CitationViewer'
import ChatBox from '@/components/ChatBox'

export default function AnalysisResult() {
  const { jobId } = useParams()
  const [status, setStatus] = useState('Loading analysis...')
  const [result, setResult] = useState<any>(null)

  useEffect(() => {
    let timer: any
    async function poll() {
      const { data } = await api.get(`/analysis/status/${jobId}`)
      if (data.status === 'done' || data.result) {
        setResult(data.result)
        setStatus('Completed')
        clearInterval(timer)
      } else {
        setStatus(`Status: ${data.status} (${data.progress || 0}%)`)
      }
    }
    poll()
    timer = setInterval(poll, 1500)
    return () => clearInterval(timer)
  }, [jobId])

  if (!result) return <LoadingStatus status={status} />

  return (
    <div className="grid gap-6">
      <h2 className="text-xl font-semibold">Analysis Results</h2>
      {result.summary_sections?.map((s: any, idx: number) => (
        <SummarySection key={idx} title={s.title} content={s.content} />
      ))}
      <FeedbackSection feedback={result.feedback} />
      <FindingsList items={result.key_findings || []} />
      <CitationViewer items={result.citations || []} />
      <div>
        <button className="px-3 py-2 border rounded mr-2" onClick={() => exportMarkdown(result)}>Export Markdown</button>
        <button className="px-3 py-2 border rounded" onClick={() => window.print()}>Export PDF (Print)</button>
      </div>
      <ChatBox />
    </div>
  )
}

function exportMarkdown(result: any) {
  let md = `# Summary\n\n`
  for (const s of result.summary_sections || []) {
    md += `## ${s.title}\n\n${s.content}\n\n`
  }
  md += `\n## Feedback\n\n${result.feedback}\n\n`
  md += `\n## Key Findings\n\n` + (result.key_findings || []).map((f: string) => `- ${f}`).join('\n') + '\n'
  const blob = new Blob([md], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'analysis.md'
  a.click()
  URL.revokeObjectURL(url)
}
