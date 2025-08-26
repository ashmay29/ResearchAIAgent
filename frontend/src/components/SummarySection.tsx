export default function SummarySection({ title, content }: { title: string; content: string }) {
  return (
    <section className="mb-6">
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <div className="prose dark:prose-invert max-w-none whitespace-pre-wrap">{content}</div>
    </section>
  )
}
