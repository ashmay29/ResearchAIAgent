import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { api } from '@/lib/api'
import LoadingStatus from '@/components/LoadingStatus'
import SummarySection from '@/components/SummarySection'
import FeedbackSection from '@/components/FeedbackSection'
import FindingsList from '@/components/FindingsList'
import CitationViewer from '@/components/CitationViewer'
import ChatBox from '@/components/ChatBox'
import GradientButton from '@/components/ui/GradientButton'
import { Download, Printer, Sparkles } from 'lucide-react'

export default function AnalysisResult() {
  const { jobId } = useParams()
  const [status, setStatus] = useState('Loading analysis...')
  const [resultsByPaper, setResultsByPaper] = useState<Record<string, any> | null>(null)
  const [singleResult, setSingleResult] = useState<any>(null)
  const [paperIds, setPaperIds] = useState<string[]>([])
  const [selectedPaperId, setSelectedPaperId] = useState<string>('')

  useEffect(() => {
    let timer: any
    async function poll() {
      try {
        const { data } = await api.get(`/analysis/status/${jobId}`)
        // New batch shape
        if (data.status === 'done' && data.results) {
          const results = data.results as Record<string, any>
          const ids: string[] = (data.paper_ids && data.paper_ids.length > 0) ? data.paper_ids : Object.keys(results || {})
          setResultsByPaper(results)
          setPaperIds(ids)
          if (!selectedPaperId && ids.length > 0) setSelectedPaperId(ids[0])
          setStatus('Completed')
          clearInterval(timer)
          return
        }
        // Backward compat: old single result
        if (data.status === 'done' && data.result) {
          setSingleResult(data.result)
          setStatus('Completed')
          clearInterval(timer)
          return
        }
        // Done but nothing to show: surface a friendly message instead of blank
        if (data.status === 'done' && !data.results && !data.result) {
          setStatus('Completed, but no results available for this job. Please check server logs.')
          clearInterval(timer)
          return
        }
        setStatus(`Status: ${data.status} (${data.progress || 0}%)`)
      } catch (err) {
        console.error('Status polling failed', err)
        setStatus('Failed to load status. Please refresh or check server logs.')
        clearInterval(timer)
      }
    }
    poll()
    timer = setInterval(poll, 1500)
    return () => clearInterval(timer)
  }, [jobId])

  // Resolve the result to display
  const currentResult = useMemo(() => {
    if (resultsByPaper && selectedPaperId) return resultsByPaper[selectedPaperId]
    return singleResult
  }, [resultsByPaper, selectedPaperId, singleResult])

  if (!currentResult) return <LoadingStatus status={status} />

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-700 via-indigo-700 to-sky-600 bg-clip-text text-transparent flex items-center gap-3">
          <Sparkles className="h-8 w-8 text-blue-600 dark:text-blue-400" />
          Analysis Results
        </h2>
        <div className="flex gap-3 items-center">
          {resultsByPaper && paperIds.length > 1 && (
            <select
              className="px-3 py-2 border rounded-lg bg-white dark:bg-gray-900 dark:border-gray-800"
              value={selectedPaperId}
              onChange={(e) => setSelectedPaperId(e.target.value)}
              title="Select paper"
            >
              {paperIds.map(id => (
                <option key={id} value={id}>{id}</option>
              ))}
            </select>
          )}
          <GradientButton
            variant="secondary"
            icon={<Download className="h-4 w-4" />}
            onClick={() => exportMarkdown(currentResult)}
          >
            Export Markdown
          </GradientButton>
          <GradientButton
            variant="secondary"
            icon={<Printer className="h-4 w-4" />}
            onClick={() => window.print()}
          >
            Print PDF
          </GradientButton>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2, staggerChildren: 0.1 }}
        className="space-y-6"
      >
        {currentResult.summary_sections?.map((s: any, idx: number) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.1 }}
          >
            <SummarySection title={s.title} content={s.content} />
          </motion.div>
        ))}
        
        {!!(currentResult.feedback && currentResult.feedback.trim()) && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
          >
            <FeedbackSection feedback={currentResult.feedback} />
          </motion.div>
        )}

        {!!(currentResult.key_findings && currentResult.key_findings.length) && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
          >
            <FindingsList items={currentResult.key_findings || []} />
          </motion.div>
        )}

        {!!(currentResult.citations && currentResult.citations.length) && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
          >
            <CitationViewer items={currentResult.citations || []} />
          </motion.div>
        )}

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <ChatBox />
        </motion.div>
      </motion.div>
    </motion.div>
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
