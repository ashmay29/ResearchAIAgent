import { ReactNode, ButtonHTMLAttributes } from 'react'

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode
  variant?: 'primary' | 'secondary'
  loading?: boolean
  icon?: ReactNode
}

export default function GradientButton({ 
  children, 
  variant = 'primary', 
  loading = false,
  icon,
  className = '',
  disabled,
  ...props 
}: Props) {
  const baseClasses = `
    relative inline-flex items-center justify-center gap-2
    px-6 py-3 font-medium rounded-xl
    transition-all duration-300
    disabled:opacity-50 disabled:cursor-not-allowed
    active:scale-95
  `

  const variantClasses = {
    primary: `
      text-white
      bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-600
      bg-[length:200%_200%] animate-gradient-x
      shadow-lg shadow-blue-500/20 dark:shadow-blue-500/30
      hover:scale-105 hover:shadow-xl hover:shadow-blue-500/30 dark:hover:shadow-blue-500/40
    `,
    secondary: `
      text-blue-700 dark:text-blue-300
      border-2 border-blue-200 dark:border-blue-900/40
      bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm
      hover:bg-blue-50 dark:hover:bg-blue-900/20
      hover:border-blue-300 dark:hover:border-blue-800
      hover:scale-105
    `
  }

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <span className="inline-block h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
      )}
      {icon && !loading && icon}
      <span>{children}</span>
    </button>
  )
}
