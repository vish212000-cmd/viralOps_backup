import { useState, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from "./api";

export type SaveStatus = 'idle' | 'saving' | 'saved' | 'failed';

export function useAutoSave<T>(
  endpoint: string, 
  debounceMs: number = 800
) {
  const [status, setStatus] = useState<SaveStatus>('idle');
  const queryClient = useQueryClient();
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const mutation = useMutation({
    mutationFn: async (data: Partial<T>) => {
      const response = await api.patch(endpoint, data);
      return response.data;
    },
    onMutate: () => {
      setStatus('saving');
    },
    onSuccess: () => {
      setStatus('saved');
      // Invalidate queries that might depend on this data
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      
      // Reset status back to idle after a few seconds
      setTimeout(() => setStatus('idle'), 3000);
    },
    onError: () => {
      setStatus('failed');
    }
  });

  const debouncedSave = (data: Partial<T>) => {
    setStatus('saving'); // immediate feedback that changes are registered
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    timeoutRef.current = setTimeout(() => {
      mutation.mutate(data);
    }, debounceMs);
  };

  return {
    debouncedSave,
    status,
    saveNow: (data: Partial<T>) => mutation.mutate(data),
    error: mutation.error
  };
}
