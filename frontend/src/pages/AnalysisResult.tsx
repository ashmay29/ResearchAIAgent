import { useEffect, useState } from 'react'
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
        <div className="flex gap-3">
          <GradientButton
            variant="secondary"
            icon={<Download className="h-4 w-4" />}
            onClick={() => exportMarkdown(result)}
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
        {result.summary_sections?.map((s: any, idx: number) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.1 }}
          >
            <SummarySection title={s.title} content={s.content} />
          </motion.div>
        ))}
        
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
        >
          <FeedbackSection feedback={result.feedback} />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
        >
          <FindingsList items={result.key_findings || []} />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
        >
          <CitationViewer items={result.citations || []} />
        </motion.div>

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
