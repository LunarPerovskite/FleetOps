import { AlertTriangle, RefreshCw, ArrowLeft } from 'lucide-react'

interface ErrorDisplayProps {
  title?: string
  message: string
  onRetry?: () => void
  onBack?: () => void
  fullPage?: boolean
}

export function ErrorDisplay({ 
  title = 'Something went wrong', 
  message, 
  onRetry, 
  onBack,
  fullPage = false 
}: ErrorDisplayProps) {
  const content = (
    <div className="flex flex-col items-center justify-center gap-4 text-center max-w-md mx-auto p-6">
      <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center">
        <AlertTriangle className="w-8 h-8 text-red-500" />
      </div>
      
      <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      <p className="text-gray-500">{message}</p>
      
      <div className="flex gap-3 mt-2">
        {onRetry && (
          <button
            onClick={onRetry}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Try Again
          </button>
        )}
        {onBack && (
          <button
            onClick={onBack}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Go Back
          </button>
        )}
      </div>
    </div>
  )

  if (fullPage) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        {content}
      </div>
    )
  }

  return <div className="p-8">{content}</div>
}

export function EmptyState({ 
  title = 'No items found', 
  message = 'Get started by creating your first item.',
  action
}: { 
  title?: string
  message?: string
  action?: { label: string; onClick: () => void }
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 text-center py-12">
      <p className="text-gray-900 font-medium">{title}</p>
      <p className="text-gray-500 text-sm">{message}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
        >
          {action.label}
        </button>
      )}
    </div>
  )
}
