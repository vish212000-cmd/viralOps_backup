import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Key, Plus, Copy, Trash2, CheckCircle2 } from 'lucide-react';
import { Button } from '../design/Button';
import { api } from "../../utils/api";
import { useToast } from '../../context/ToastContext';

export function APIKeyManager() {
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const [copiedId, setCopiedId] = useState<number | null>(null);

  const { data: tokens, isLoading } = useQuery({
    queryKey: ['api-tokens'],
    queryFn: async () => {
      const res = await api.get('/api/profiles/tokens/');
      return res.data;
    }
  });

  const generateMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post('/api/profiles/tokens/', { name: `Token ${new Date().toLocaleDateString()}` });
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['api-tokens'] });
      showToast('New API Token generated', 'success');
      // Ideally show the raw_token to the user here once, but for simplicity we rely on the list view if it was returned.
    }
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/api/profiles/tokens/${id}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-tokens'] });
      showToast('Token deleted', 'success');
    }
  });

  const handleCopy = (token: string, id: number) => {
    navigator.clipboard.writeText(token);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold text-white">API Tokens</h3>
        <Button 
          variant="outline" 
          size="sm" 
          className="h-8 gap-2"
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
        >
          <Plus size={14} /> Generate Token
        </Button>
      </div>
      <p className="text-sm text-text-muted mb-4">Use these tokens to integrate ViralOps with other services.</p>
      
      <div className="rounded-xl border border-white/10 overflow-hidden">
        {isLoading ? (
          <div className="p-4 bg-white/5 text-sm text-text-muted">Loading tokens...</div>
        ) : tokens && tokens.length > 0 ? (
          <div className="flex flex-col">
            {tokens.map((token: any) => (
              <div key={token.id} className="p-4 bg-white/5 border-b border-white/10 last:border-b-0 flex justify-between items-center">
                <div>
                  <p className="font-medium text-sm">{token.name}</p>
                  <p className="text-xs text-text-muted font-mono mt-1">
                    {token.raw_token || `${token.prefix}...`}
                  </p>
                </div>
                <div className="flex gap-2">
                  {token.raw_token && (
                    <Button variant="ghost" size="sm" onClick={() => handleCopy(token.raw_token, token.id)}>
                      {copiedId === token.id ? <CheckCircle2 size={16} className="text-accent-cyan" /> : <Copy size={16} />}
                    </Button>
                  )}
                  <Button variant="ghost" size="sm" className="text-red-400 hover:bg-red-400/10" onClick={() => deleteMutation.mutate(token.id)}>
                    <Trash2 size={16} />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-4 bg-white/5 text-sm text-text-muted flex justify-between">
            <span>You have no active API tokens.</span>
          </div>
        )}
      </div>
    </div>
  );
}
