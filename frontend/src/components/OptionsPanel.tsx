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
    <div className="border rounded-lg p-4 grid gap-3">
      <div>
        <label className="block text-sm mb-1">Output format</label>
        <select
          className="w-full border rounded px-2 py-1 bg-white dark:bg-gray-800"
          value={options.output_format}
          onChange={e => onChange({ ...options, output_format: e.target.value as AnalysisOptions['output_format'] })}
        >
          <option value="paragraphs">Paragraphs</option>
          <option value="bullet_points">Bullet points</option>
          <option value="mind_map">Mind map</option>
        </select>
      </div>
      <div>
        <label className="block text-sm mb-1">Focus area</label>
        <select
          className="w-full border rounded px-2 py-1 bg-white dark:bg-gray-800"
          value={options.focus_area}
          onChange={e => onChange({ ...options, focus_area: e.target.value as AnalysisOptions['focus_area'] })}
        >
          <option value="overall_context">Overall context</option>
          <option value="methodology">Methodology</option>
          <option value="literature_review">Literature review</option>
          <option value="results">Results</option>
          <option value="technological_stack">Technological stack</option>
        </select>
      </div>
      <div>
        <label className="block text-sm mb-1">Analysis type</label>
        <select
          className="w-full border rounded px-2 py-1 bg-white dark:bg-gray-800"
          value={options.analysis_type}
          onChange={e => onChange({ ...options, analysis_type: e.target.value as AnalysisOptions['analysis_type'] })}
        >
          <option value="simple_summary">Simple summary</option>
          <option value="critical_analysis">Critical analysis</option>
          <option value="research_notes">Research notes</option>
        </select>
      </div>
    </div>
  )
}
