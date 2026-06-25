import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Monitor } from 'lucide-react';
import { Button } from '../design/Button';
import { api } from "../../utils/api";
import { useToast } from '../../context/ToastContext';

export function SessionManager() {
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  const { data: sessions, isLoading } = useQuery({
    queryKey: ['sessions'],
    queryFn: async () => {
      const res = await api.get('/api/profiles/sessions/');
      return res.data;
    }
  });

  const revokeAllMutation = useMutation({
    mutationFn: async () => {
      await api.post('/api/profiles/sessions/revoke_all_others/');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      showToast('All other sessions have been logged out', 'success');
    }
  });

  return (
    <div>
      <h3 className="font-semibold text-white mb-4">Active Sessions</h3>
      <div className="flex flex-col gap-3">
        {isLoading ? (
          <div className="text-sm text-text-muted">Loading sessions...</div>
        ) : sessions?.length > 0 ? (
          sessions.map((session: any) => (
            <div key={session.id} className="flex justify-between items-center p-3 rounded-lg bg-white/5 border border-white/10">
              <div className="flex items-center gap-3">
                <Monitor size={20} className={session.is_current ? "text-accent-cyan" : "text-text-muted"} />
                <div>
                  <p className="font-medium text-sm">{session.device} • {session.browser}</p>
                  <p className="text-xs text-text-muted">
                    {session.location || 'Unknown Location'} • {session.is_current ? 'Active Now' : new Date(session.last_activity).toLocaleString()}
                  </p>
                </div>
              </div>
              {session.is_current && (
                <span className="text-xs bg-accent-cyan/20 text-accent-cyan px-2 py-1 rounded-md font-medium">Current</span>
              )}
            </div>
          ))
        ) : (
          <div className="text-sm text-text-muted">No active sessions.</div>
        )}
      </div>
      
      {sessions?.length > 1 && (
        <div className="mt-4 flex justify-end">
          <Button 
            variant="danger" 
            size="sm" 
            onClick={() => revokeAllMutation.mutate()}
            disabled={revokeAllMutation.isPending}
          >
            Log out all other sessions
          </Button>
        </div>
      )}
    </div>
  );
}
