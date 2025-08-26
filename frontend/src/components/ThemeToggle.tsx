import { useEffect, useState } from 'react'

export default function ThemeToggle() {
  const [dark, setDark] = useState(() => localStorage.getItem('theme') === 'dark')
  useEffect(() => {
    if (dark) {
      document.documentElement.classList.add('dark')
      localStorage.setItem('theme', 'dark')
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('theme', 'light')
    }
  }, [dark])
  return (
    <button className="px-3 py-2 rounded-md text-sm bg-gray-100 dark:bg-gray-800" onClick={() => setDark(d => !d)}>
      {dark ? 'Light' : 'Dark'} Mode
    </button>
  )
}
