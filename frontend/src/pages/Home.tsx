import FileUpload from '@/components/FileUpload'
import OptionsPanel from '@/components/OptionsPanel'
import { useNavigate, Link } from 'react-router-dom'
import { useState } from 'react'
import { motion } from 'framer-motion'
import { api } from '@/lib/api'
import { FlaskConical, Settings2, History as HistoryIcon, Sparkles, Zap, Shield } from 'lucide-react'
import GlassCard from '@/components/ui/GlassCard'
import AnimatedBadge from '@/components/ui/AnimatedBadge'

type AnalysisOptions = {
  output_format: 'paragraphs' | 'bullet_points' | 'mind_map'
  focus_area: 'methodology' | 'literature_review' | 'results' | 'technological_stack' | 'overall_context'
  analysis_type: 'simple_summary' | 'critical_analysis' | 'research_notes'
}

export default function Home() {
  const nav = useNavigate()
  const [opts, setOpts] = useState<AnalysisOptions>({
    output_format: 'paragraphs',
    focus_area: 'overall_context',
    analysis_type: 'simple_summary',
  })
  const [starting, setStarting] = useState(false)

  async function onStart(paperIds: string[]) {
    if (!paperIds || paperIds.length === 0) return
    setStarting(true)
    try {
      const jobIds: string[] = []
      for (const id of paperIds) {
        const { data } = await api.post('/analysis/run', { paper_id: id, options: opts })
        jobIds.push(data.job_id)
      }
      // Navigate to the first job's analysis page
      nav(`/analysis/${jobIds[0]}`)
    } finally {
      setStarting(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="space-y-10"
    >
      {/* Hero */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
        className="relative overflow-hidden rounded-3xl border border-blue-100/60 dark:border-blue-900/40 bg-gradient-to-br from-blue-50 via-indigo-50 to-sky-100 dark:from-navy-deep dark:via-navy-dark dark:to-navy-medium p-10 md:p-16 text-center shadow-2xl"
      >
        <div className="absolute inset-0 pointer-events-none" aria-hidden>
          <div className="absolute -top-24 -left-24 h-80 w-80 rounded-full bg-gradient-to-br from-blue-400/40 to-indigo-400/30 blur-3xl animate-float" />
          <div className="absolute -bottom-24 -right-24 h-80 w-80 rounded-full bg-gradient-to-tr from-sky-400/40 to-blue-400/30 blur-3xl animate-float" style={{ animationDelay: '3s' }} />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-96 w-96 rounded-full bg-gradient-to-r from-indigo-400/20 to-purple-400/20 blur-3xl animate-glow" />
        </div>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="relative flex items-center justify-center gap-3 mb-4"
        >
          <FlaskConical className="h-10 w-10 text-blue-600 dark:text-blue-400 animate-float" />
          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-700 via-indigo-700 to-sky-600 dark:from-blue-400 dark:via-indigo-400 dark:to-sky-400 animate-gradient-x">
            Cognito Research
          </h1>
        </motion.div>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="relative max-w-2xl mx-auto text-lg text-blue-900/80 dark:text-gray-300 leading-relaxed mb-6"
        >
          Upload PDF(s) and get tailored summaries, critiques, and key findings powered by retrieval-augmented Gemini.
        </motion.p>
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.7 }}
          className="relative flex flex-wrap items-center justify-center gap-3"
        >
          <AnimatedBadge icon={<Sparkles className="h-4 w-4" />} variant="sky">
            RAG-powered
          </AnimatedBadge>
          <AnimatedBadge icon={<Settings2 className="h-4 w-4" />} variant="indigo">
            Configurable
          </AnimatedBadge>
          <AnimatedBadge icon={<HistoryIcon className="h-4 w-4" />} variant="blue">
            Sessions saved
          </AnimatedBadge>
          <AnimatedBadge icon={<Zap className="h-4 w-4" />} variant="sky">
            Lightning fast
          </AnimatedBadge>
          <AnimatedBadge icon={<Shield className="h-4 w-4" />} variant="indigo">
            Secure
          </AnimatedBadge>
        </motion.div>
      </motion.section>

      {/* Content grid */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.8 }}
        className="grid gap-6 md:gap-8 md:grid-cols-2 items-stretch"
      >
        {/* Upload Card */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.9 }}
        >
          <GlassCard className="flex flex-col h-full min-h-[400px]" glow>
            <div className="p-6 md:p-7 border-b border-blue-100/50 dark:border-gray-800/50">
              <h3 className="text-xl font-bold flex items-center gap-3">
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm shadow-lg shadow-blue-500/30">1</span>
                <span className="bg-gradient-to-r from-blue-700 to-indigo-700 bg-clip-text text-transparent">Upload your paper(s)</span>
              </h3>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 leading-relaxed">Drag & drop or choose multiple PDFs. Click Start analysis when ready.</p>
            </div>
            <div className="p-6 md:p-7 flex-1 flex items-center justify-center">
              <FileUpload onStart={onStart} starting={starting} />
            </div>
          </GlassCard>
        </motion.div>

        {/* Options Card */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 1 }}
        >
          <GlassCard className="flex flex-col h-full min-h-[400px]" glow>
            <div className="p-6 md:p-7 border-b border-blue-100/50 dark:border-gray-800/50">
              <h3 className="text-xl font-bold flex items-center gap-3">
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm shadow-lg shadow-blue-500/30">2</span>
                <span className="bg-gradient-to-r from-blue-700 to-indigo-700 bg-clip-text text-transparent">Tune the analysis</span>
              </h3>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 leading-relaxed">Choose format, focus area, and analysis type.</p>
            </div>
            <div className="p-6 md:p-7 flex-1">
              <OptionsPanel options={opts} onChange={setOpts} />
              <div className="mt-5 p-3 rounded-lg bg-blue-50/50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-900/30">
                <p className="text-xs text-blue-700 dark:text-blue-400 flex items-center gap-2">
                  <Sparkles className="h-3 w-3" />
                  <span>Tip: Switch to bullet points for quick skimming.</span>
                </p>
              </div>
            </div>
          </GlassCard>
        </motion.div>
      </motion.section>

      {/* Footer actions */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 1 }}
        className="flex items-center justify-between"
      >
        <div className="text-sm text-gray-600 dark:text-gray-400">Need to revisit something? Your runs are saved.</div>
        <Link className="px-4 py-2 rounded-lg border border-blue-200 text-blue-700 hover:bg-blue-50 dark:text-blue-300 dark:border-blue-900/40 dark:hover:bg-blue-900/20 inline-flex items-center gap-2 transition-all duration-300 hover:scale-105 hover:shadow-md" to="/history">
          <HistoryIcon className="h-4 w-4"/> View History
        </Link>
      </motion.div>
    </motion.div>
  )
}
