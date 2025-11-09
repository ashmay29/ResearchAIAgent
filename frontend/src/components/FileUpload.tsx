import { useRef, useState } from 'react'
import { api } from '@/lib/api'
import { UploadCloud, FileCheck } from 'lucide-react'
import GradientButton from './ui/GradientButton'

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
        className={`
          relative w-full flex-1 min-h-[240px] 
          border-2 border-dashed rounded-xl 
          px-6 py-8 md:px-8 md:py-10 
          flex flex-col items-center justify-center text-center 
          transition-all duration-300
          ${drag 
            ? 'border-blue-500 dark:border-blue-400 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 shadow-[0_0_20px_rgba(59,130,246,0.3)] scale-[1.02]' 
            : 'border-blue-200 dark:border-blue-800/50 hover:border-blue-300 dark:hover:border-blue-700 hover:shadow-[0_0_15px_rgba(59,130,246,0.2)]'
          }
        `}
        onDragOver={e => { e.preventDefault(); setDrag(true) }}
        onDragLeave={() => setDrag(false)}
        onDrop={e => { e.preventDefault(); setDrag(false); handleFiles(e.dataTransfer.files) }}
      >
        {drag && (
          <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-blue-500/10 to-indigo-500/10 animate-pulse" />
        )}
        <UploadCloud className={`h-12 w-12 mb-4 text-blue-500 dark:text-blue-400 transition-all duration-300 ${drag ? 'scale-110 animate-bounce' : ''}`} />
        <p className="mb-3 text-base md:text-lg font-medium text-gray-700 dark:text-gray-300">
          {drag ? 'Drop your PDFs here!' : 'Drag & drop PDF(s) here, or'}
        </p>
        <button
          className="px-5 py-2.5 rounded-lg text-white font-medium bg-gradient-to-r from-blue-600 to-indigo-600 shadow-lg shadow-blue-500/20 hover:shadow-xl hover:shadow-blue-500/30 hover:scale-105 active:scale-95 transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={() => inputRef.current?.click()}
          disabled={uploading || starting}
        >
          {uploading ? 'Uploading...' : 'Choose File(s)'}
        </button>
        {progress && (
          <div className="mt-4 text-sm text-blue-600 dark:text-blue-400 font-medium animate-pulse">
            {progress}
          </div>
        )}
        {ids.length > 0 && !uploading && (
          <div className="mt-4 flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 text-sm font-medium border border-green-200 dark:border-green-800/40 animate-fade-in">
            <FileCheck className="h-4 w-4" />
            <span>{ids.length} file(s) ready</span>
          </div>
        )}
        <input ref={inputRef} type="file" className="hidden" accept="application/pdf" multiple onChange={e => handleFiles(e.target.files)} />
      </div>
      <GradientButton
        disabled={ids.length === 0 || uploading || !!starting}
        onClick={() => onStart(ids)}
        loading={starting}
        className="w-full"
      >
        {starting ? 'Starting…' : 'Start Analysis'}
      </GradientButton>
    </div>
  )
}
