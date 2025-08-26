export default function Toast({ message, onClose }: { message: string; onClose: () => void }) {
  if (!message) return null
  return (
    <div className="fixed bottom-4 right-4 bg-black text-white px-4 py-2 rounded shadow">
      <div className="flex items-center gap-3">
        <span>{message}</span>
        <button className="underline" onClick={onClose}>Close</button>
      </div>
    </div>
  )
}
