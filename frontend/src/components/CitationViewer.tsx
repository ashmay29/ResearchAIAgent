type Citation = { title: string; authors: string[]; year?: number; link?: string }
export default function CitationViewer({ items }: { items: Citation[] }) {
  return (
    <section className="mb-6">
      <h3 className="text-lg font-semibold mb-2">Citations</h3>
      <div className="space-y-3">
        {items.map((c, idx) => (
          <div key={idx} className="border rounded p-3">
            <div className="font-medium">{c.title}</div>
            <div className="text-sm text-gray-600 dark:text-gray-300">{c.authors.join(', ')}{c.year ? ` • ${c.year}` : ''}</div>
            {c.link && <a className="text-blue-600" href={c.link} target="_blank">Open</a>}
          </div>
        ))}
      </div>
    </section>
  )
}
