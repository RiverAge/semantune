import { Loader2 } from 'lucide-react';

export default function Loading({ message = '加载中...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <Loader2 className="h-8 w-8 text-primary-600 animate-spin" />
      <p className="mt-4 text-gray-600">{message}</p>
    </div>
  );
}
