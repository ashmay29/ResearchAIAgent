import { ReactNode, CSSProperties } from 'react'

type Props = {
  children: ReactNode
  className?: string
  hover?: boolean
  glow?: boolean
  style?: CSSProperties
}

export default function GlassCard({ children, className = '', hover = true, glow = false, style }: Props) {
  return (
    <div
      className={`
        relative rounded-2xl 
        border border-blue-100/60 dark:border-blue-900/40
        bg-white/80 dark:bg-gray-900/80 backdrop-blur-md
        shadow-lg shadow-blue-500/5 dark:shadow-blue-500/10
        transition-all duration-300
        ${hover ? 'hover:scale-[1.02] hover:shadow-xl hover:shadow-blue-500/10 dark:hover:shadow-blue-500/20 hover:-translate-y-1' : ''}
        ${glow ? 'ring-1 ring-blue-500/10 dark:ring-blue-500/20' : ''}
        ${className}
      `}
      style={style}
    >
      {glow && (
        <div className="absolute inset-0 -z-10 rounded-2xl bg-gradient-to-br from-blue-500/10 via-indigo-500/5 to-transparent blur-xl" />
      )}
      {children}
    </div>
  )
}
