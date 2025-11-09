import { ReactNode } from 'react'

type Props = {
  children: ReactNode
  icon?: ReactNode
  variant?: 'blue' | 'indigo' | 'sky'
}

export default function AnimatedBadge({ children, icon, variant = 'blue' }: Props) {
  const variantClasses = {
    blue: 'bg-blue-50/80 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 border-blue-200/60 dark:border-blue-800/40 hover:border-blue-300 dark:hover:border-blue-700',
    indigo: 'bg-indigo-50/80 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-300 border-indigo-200/60 dark:border-indigo-800/40 hover:border-indigo-300 dark:hover:border-indigo-700',
    sky: 'bg-sky-50/80 dark:bg-sky-900/20 text-sky-700 dark:text-sky-300 border-sky-200/60 dark:border-sky-800/40 hover:border-sky-300 dark:hover:border-sky-700'
  }

  const glowClasses = {
    blue: 'hover:shadow-[0_0_15px_rgba(59,130,246,0.3)]',
    indigo: 'hover:shadow-[0_0_15px_rgba(99,102,241,0.3)]',
    sky: 'hover:shadow-[0_0_15px_rgba(14,165,233,0.3)]'
  }

  return (
    <div className={`
      relative inline-flex items-center gap-2 px-3 py-1.5 rounded-full
      border backdrop-blur-sm overflow-hidden
      text-sm font-medium
      transition-all duration-300
      hover:scale-105
      animate-fade-in
      ${variantClasses[variant]}
      ${glowClasses[variant]}
    `}>
      <div className="absolute inset-0 -translate-x-full animate-shimmer-slow bg-gradient-to-r from-transparent via-white/20 to-transparent" />
      {icon && <span className="relative z-10 animate-pulse">{icon}</span>}
      <span className="relative z-10">{children}</span>
    </div>
  )
}
