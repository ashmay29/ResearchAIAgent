export default function FeedbackSection({ feedback }: { feedback: string }) {
  return (
    <section className="mb-6">
      <h3 className="text-lg font-semibold mb-2">Critique / Feedback</h3>
      <div className="prose dark:prose-invert max-w-none whitespace-pre-wrap">{feedback}</div>
    </section>
  )
}
