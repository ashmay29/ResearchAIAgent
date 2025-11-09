import { FileText, Target, Microscope } from 'lucide-react'

type AnalysisOptions = {
  output_format: 'paragraphs' | 'bullet_points' | 'mind_map'
  focus_area: 'methodology' | 'literature_review' | 'results' | 'technological_stack' | 'overall_context'
  analysis_type: 'simple_summary' | 'critical_analysis' | 'research_notes'
}

type Props = {
  options: AnalysisOptions
  onChange: (opts: AnalysisOptions) => void
}

export default function OptionsPanel({ options, onChange }: Props) {
  return (
    <div className="space-y-4">
      <div className="group">
        <label className="flex items-center gap-2 text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
          <FileText className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          Output format
        </label>
        <select
          className="w-full border border-blue-200 dark:border-blue-800/50 rounded-lg px-3 py-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 transition-all duration-300 hover:border-blue-300 dark:hover:border-blue-700 focus:border-blue-500 dark:focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none cursor-pointer"
          value={options.output_format}
          onChange={e => onChange({ ...options, output_format: e.target.value as AnalysisOptions['output_format'] })}
        >
          <option value="paragraphs">📝 Paragraphs</option>
          <option value="bullet_points">• Bullet points</option>
          <option value="mind_map">🗺️ Mind map</option>
        </select>
      </div>
      <div className="group">
        <label className="flex items-center gap-2 text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
          <Target className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          Focus area
        </label>
        <select
          className="w-full border border-blue-200 dark:border-blue-800/50 rounded-lg px-3 py-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 transition-all duration-300 hover:border-blue-300 dark:hover:border-blue-700 focus:border-blue-500 dark:focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none cursor-pointer"
          value={options.focus_area}
          onChange={e => onChange({ ...options, focus_area: e.target.value as AnalysisOptions['focus_area'] })}
        >
          <option value="overall_context">🌐 Overall context</option>
          <option value="methodology">🔬 Methodology</option>
          <option value="literature_review">📚 Literature review</option>
          <option value="results">📊 Results</option>
          <option value="technological_stack">⚙️ Technological stack</option>
        </select>
      </div>
      <div className="group">
        <label className="flex items-center gap-2 text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
          <Microscope className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          Analysis type
        </label>
        <select
          className="w-full border border-blue-200 dark:border-blue-800/50 rounded-lg px-3 py-2.5 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 transition-all duration-300 hover:border-blue-300 dark:hover:border-blue-700 focus:border-blue-500 dark:focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none cursor-pointer"
          value={options.analysis_type}
          onChange={e => onChange({ ...options, analysis_type: e.target.value as AnalysisOptions['analysis_type'] })}
        >
          <option value="simple_summary">✨ Simple summary</option>
          <option value="critical_analysis">🔍 Critical analysis</option>
          <option value="research_notes">📋 Research notes</option>
        </select>
      </div>
    </div>
  )
}
