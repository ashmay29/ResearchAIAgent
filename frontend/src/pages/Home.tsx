import FileUpload from '@/components/FileUpload'
import OptionsPanel from '@/components/OptionsPanel'
import { useNavigate, Link } from 'react-router-dom'
import { useState } from 'react'
import { api } from '@/lib/api'
import { FlaskConical, Settings2, History as HistoryIcon, Sparkles } from 'lucide-react'

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
    <div className="space-y-10">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-2xl border border-blue-100/60 dark:border-blue-900/40 bg-gradient-to-br from-blue-50 via-indigo-50 to-sky-100 dark:from-[#0b1220] dark:via-[#0b1220] dark:to-[#0b1220] p-8 md:p-12 text-center">
        <div className="absolute inset-0 pointer-events-none" aria-hidden>
          <div className="absolute -top-24 -left-24 h-72 w-72 rounded-full bg-gradient-to-br from-blue-400/30 to-indigo-400/20 blur-3xl" />
          <div className="absolute -bottom-24 -right-24 h-72 w-72 rounded-full bg-gradient-to-tr from-sky-400/30 to-blue-400/20 blur-3xl" />
        </div>
        <div className="relative flex items-center justify-center gap-3 mb-3">
          <FlaskConical className="h-8 w-8 text-blue-600" />
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-700 via-indigo-700 to-sky-600">Cognito Research</h1>
        </div>
        <p className="relative max-w-2xl mx-auto text-blue-900/70 dark:text-gray-300">
          Upload PDF(s) and get tailored summaries, critiques, and key findings powered by retrieval-augmented Gemini.
        </p>
        <div className="relative mt-5 flex items-center justify-center gap-3 text-sm text-blue-900/60 dark:text-gray-400">
          <div className="inline-flex items-center gap-1"><Sparkles className="h-4 w-4 text-sky-600"/> RAG-powered</div>
          <div className="inline-flex items-center gap-1"><Settings2 className="h-4 w-4 text-indigo-600"/> Configurable</div>
          <div className="inline-flex items-center gap-1"><HistoryIcon className="h-4 w-4 text-blue-600"/> Sessions saved</div>
        </div>
      </section>

      {/* Content grid */}
      <section className="grid gap-6 md:gap-8 md:grid-cols-2 items-stretch">
        {/* Upload Card */}
        <div className="rounded-xl border border-blue-100 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm flex flex-col h-full min-h-[380px]">
          <div className="p-5 md:p-6 border-b border-gray-100 dark:border-gray-800">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm">1</span>
              Upload your paper(s)
            </h3>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">Drag & drop or choose multiple PDFs. Click Start analysis when ready.</p>
          </div>
          <div className="p-5 md:p-6 flex-1 flex items-center justify-center">
            <FileUpload onStart={onStart} starting={starting} />
          </div>
        </div>

        {/* Options Card */}
        <div className="rounded-xl border border-blue-100 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm flex flex-col h-full min-h-[380px]">
          <div className="p-5 md:p-6 border-b border-gray-100 dark:border-gray-800">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm">2</span>
              Tune the analysis
            </h3>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">Choose format, focus area, and analysis type.</p>
          </div>
          <div className="p-5 md:p-6 flex-1">
            <OptionsPanel options={opts} onChange={setOpts} />
            <div className="mt-4 text-xs text-gray-500">Tip: Switch to bullet points for quick skimming.</div>
          </div>
        </div>
      </section>

      {/* Footer actions */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600 dark:text-gray-400">Need to revisit something? Your runs are saved.</div>
        <Link className="px-4 py-2 rounded-lg border border-blue-200 text-blue-700 hover:bg-blue-50 dark:text-blue-300 dark:border-blue-900/40 dark:hover:bg-blue-900/20 inline-flex items-center gap-2" to="/history">
          <HistoryIcon className="h-4 w-4"/> View History
        </Link>
      </div>
    </div>
  )
}
