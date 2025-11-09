import { Link, NavLink } from 'react-router-dom'
import ThemeToggle from './ThemeToggle'
import { FlaskConical } from 'lucide-react'

export default function Navbar() {
  const navLink = ({ isActive }: { isActive: boolean }) => (
    `inline-flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-200
    ${isActive 
      ? 'bg-gradient-to-r from-blue-100 to-indigo-100 dark:from-blue-900/30 dark:to-indigo-900/30 text-blue-700 dark:text-blue-300' 
      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100/80 dark:hover:bg-gray-800/80'
    }`
  )
  
  return (
    <header className="sticky top-0 z-50 border-b border-gray-200/50 dark:border-gray-800/50 backdrop-blur-lg bg-white/80 dark:bg-gray-900/70 shadow-sm">
      <div className="max-w-5xl mx-auto px-4 py-3 flex items-center gap-6">
        <Link 
          to="/" 
          className="flex items-center gap-2 font-bold text-lg bg-gradient-to-r from-blue-700 via-indigo-700 to-sky-600 bg-clip-text text-transparent"
        >
          <FlaskConical className="h-6 w-6 text-blue-600 dark:text-blue-400" />
          <span>Cognito Research</span>
        </Link>
        <nav className="flex items-center gap-2">
          <NavLink to="/history" className={navLink}>History</NavLink>
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
