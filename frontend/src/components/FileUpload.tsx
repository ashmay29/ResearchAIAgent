import { useRef, useState } from 'react'
import { api } from '@/lib/api'

type Props = {
  onStart: (paperIds: string[]) => void
  onUploaded?: (paperIds: string[]) => void
  starting?: boolean
}

export default function FileUpload({ onStart, onUploaded, starting }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [drag, setDrag] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState<string>('')
  const [ids, setIds] = useState<string[]>([])

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return
    const valid: File[] = Array.from(files).filter(f => f.name.toLowerCase().endsWith('.pdf'))
    if (valid.length === 0) {
      alert('Only PDF files are supported')
      return
    }
    setUploading(true)
    const newIds: string[] = []
    try {
      for (let i = 0; i < valid.length; i++) {
        const f = valid[i]
        setProgress(`Uploading ${i + 1} / ${valid.length} ...`)
        const form = new FormData()
        form.append('file', f)
        const { data } = await api.post('/papers/upload', form)
        newIds.push(data.paper_id)
      }
      const all = [...ids, ...newIds]
      setIds(all)
      onUploaded?.(all)
    } finally {
      setUploading(false)
      setProgress('')
    }
  }

  return (
    <div className="h-full w-full flex flex-col items-center justify-center gap-4">
      <div
        className={`w-full flex-1 min-h-[240px] border-2 border-dashed rounded-lg px-6 py-8 md:px-8 md:py-10 flex flex-col items-center justify-center text-center transition-colors ${drag ? 'border-blue-500 bg-gradient-to-br from-blue-50 to-indigo-50' : 'border-blue-200 hover:border-blue-300'}`}
        onDragOver={e => { e.preventDefault(); setDrag(true) }}
        onDragLeave={() => setDrag(false)}
        onDrop={e => { e.preventDefault(); setDrag(false); handleFiles(e.dataTransfer.files) }}
      >
        <p className="mb-3 text-base md:text-lg">Drag & drop PDF(s) here, or</p>
        <button
          className="px-4 py-2 rounded text-white bg-gradient-to-r from-blue-600 to-indigo-600 shadow hover:from-blue-500 hover:to-indigo-500 focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-50"
          onClick={() => inputRef.current?.click()}
          disabled={uploading || starting}
        >
          {uploading ? 'Uploading...' : 'Choose File(s)'}
        </button>
        {progress && <div className="mt-3 text-sm text-gray-600">{progress}</div>}
        {ids.length > 0 && !uploading && (
          <div className="mt-3 text-xs text-gray-500">{ids.length} file(s) ready</div>
        )}
        <input ref={inputRef} type="file" className="hidden" accept="application/pdf" multiple onChange={e => handleFiles(e.target.files)} />
      </div>
      <button
        className="px-4 py-2 rounded text-white bg-gradient-to-r from-blue-600 to-indigo-600 shadow hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 flex items-center gap-2"
        disabled={ids.length === 0 || uploading || !!starting}
        onClick={() => onStart(ids)}
        title={ids.length === 0 ? 'Upload PDF(s) first' : 'Start analysis'}
      >
        {starting && (
          <span className="inline-block h-3 w-3 rounded-full border-2 border-white border-t-transparent animate-spin"></span>
        )}
        {starting ? 'Starting…' : 'Start analysis'}
      </button>
    </div>
  )
}
