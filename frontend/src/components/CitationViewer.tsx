type Citation = { title?: string; authors?: string[]; year?: number | string; link?: string }
export default function CitationViewer({ items }: { items: Array<Citation | string> }) {
  const safeItems = Array.isArray(items) ? items : []
  return (
    <section className="mb-6">
      <h3 className="text-lg font-semibold mb-2">Citations</h3>
      <div className="space-y-3">
        {safeItems.map((raw, idx) => {
          // If server returned plain strings, render them directly
          if (typeof raw === 'string') {
            return (
              <div key={idx} className="border rounded p-3">
                <div className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap">{raw}</div>
              </div>
            )
          }
          const c = raw as Citation
          const authors = Array.isArray(c.authors) ? c.authors.join(', ') : undefined
          const title = c.title || (authors ? 'Citation' : 'Citation')
          return (
            <div key={idx} className="border rounded p-3">
              <div className="font-medium">{title}</div>
              <div className="text-sm text-gray-600 dark:text-gray-300">
                {authors}{c.year ? ` • ${c.year}` : ''}
              </div>
              {c.link && (
                <a className="text-blue-600" href={c.link} target="_blank" rel="noreferrer">Open</a>
              )}
            </div>
          )
        })}
      </div>
    </section>
  )
}
