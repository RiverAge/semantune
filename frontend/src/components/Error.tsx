import { AlertCircle } from 'lucide-react';

export default function Error({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <AlertCircle className="h-12 w-12 text-red-500" />
      <p className="mt-4 text-gray-900 font-medium">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 btn btn-primary"
        >
          重试
        </button>
      )}
    </div>
  );
}
