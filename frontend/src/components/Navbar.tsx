import { Link, NavLink } from 'react-router-dom'
import ThemeToggle from './ThemeToggle'

export default function Navbar() {
  const navLink = ({ isActive }: { isActive: boolean }) => (
    'px-3 py-2 rounded-md text-sm font-medium ' + (isActive ? 'bg-gray-200 dark:bg-gray-800' : 'hover:bg-gray-100 dark:hover:bg-gray-800')
  )
  return (
    <header className="border-b border-gray-200 dark:border-gray-800">
      <div className="max-w-5xl mx-auto px-4 py-3 flex items-center gap-4">
        <Link to="/" className="font-semibold">Research Analyzer</Link>
        <nav className="flex gap-2">
          <NavLink to="/history" className={navLink}>History</NavLink>
          <NavLink to="/settings" className={navLink}>Settings</NavLink>
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <NavLink to="/login" className={navLink}>Login</NavLink>
          <NavLink to="/signup" className={navLink}>Sign Up</NavLink>
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
