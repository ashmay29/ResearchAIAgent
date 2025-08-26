export default function FindingsList({ items }: { items: string[] }) {
  return (
    <section className="mb-6">
      <h3 className="text-lg font-semibold mb-2">Key Findings</h3>
      <ul className="list-disc pl-5 space-y-1">
        {items.map((i, idx) => <li key={idx}>{i}</li>)}
      </ul>
    </section>
  )
}
