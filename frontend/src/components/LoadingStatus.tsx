export default function LoadingStatus({ status }: { status: string }) {
  return (
    <div className="flex items-center gap-3">
      <div className="h-4 w-4 rounded-full border-2 border-blue-600 border-t-transparent animate-spin"></div>
      <span className="text-sm text-gray-600 dark:text-gray-300">{status}</span>
    </div>
  )
}
