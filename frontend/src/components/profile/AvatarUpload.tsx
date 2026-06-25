import React, { useCallback, useState, useRef } from 'react';
import { Camera, UploadCloud, X, Loader2 } from 'lucide-react';
import { useToast } from '../../context/ToastContext';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from "../../utils/api";

interface AvatarUploadProps {
  currentAvatarUrl?: string | null;
  username: string;
}

export function AvatarUpload({ currentAvatarUrl, username }: AvatarUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(currentAvatarUrl || null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: async (file: Blob) => {
      const formData = new FormData();
      formData.append('avatar', file, 'avatar.jpg');
      const res = await api.post('/api/profiles/me/avatar/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return res.data;
    },
    onSuccess: (data) => {
      showToast('Avatar updated successfully', 'success');
      setPreviewUrl(data.avatar_url);
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
    onError: () => {
      showToast('Failed to upload avatar', 'error');
    }
  });

  const deleteMutation = useMutation({
    mutationFn: async () => {
      await api.delete('/api/profiles/me/avatar/');
    },
    onSuccess: () => {
      showToast('Avatar removed', 'success');
      setPreviewUrl(null);
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
    onError: () => {
      showToast('Failed to remove avatar', 'error');
    }
  });

  // Client-side compression and resizing (512x512)
  const processImage = (file: File) => {
    if (file.size > 5 * 1024 * 1024) {
      showToast('File too large. Maximum 5MB.', 'error');
      return;
    }
    
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      showToast('Only JPG, PNG, and WEBP formats are allowed.', 'error');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const MAX_SIZE = 512;
        let width = img.width;
        let height = img.height;

        if (width > height) {
          if (width > MAX_SIZE) {
            height *= MAX_SIZE / width;
            width = MAX_SIZE;
          }
        } else {
          if (height > MAX_SIZE) {
            width *= MAX_SIZE / height;
            height = MAX_SIZE;
          }
        }

        canvas.width = MAX_SIZE;
        canvas.height = MAX_SIZE;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.fillStyle = '#1e1e24'; // bg-main equivalent
          ctx.fillRect(0, 0, MAX_SIZE, MAX_SIZE);
          const dx = (MAX_SIZE - width) / 2;
          const dy = (MAX_SIZE - height) / 2;
          ctx.drawImage(img, dx, dy, width, height);
          
          canvas.toBlob((blob) => {
            if (blob) {
              const url = URL.createObjectURL(blob);
              setPreviewUrl(url); // Optimistic preview
              uploadMutation.mutate(blob);
            }
          }, 'image/jpeg', 0.85); // Compress to 85% JPEG
        }
      };
      img.src = e.target?.result as string;
    };
    reader.readAsDataURL(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processImage(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      processImage(e.target.files[0]);
    }
  };

  return (
    <div className="flex gap-6 items-center">
      <div 
        className={`relative w-24 h-24 rounded-full overflow-hidden border-2 flex items-center justify-center transition-all cursor-pointer ${
          dragActive ? 'border-accent-cyan bg-accent-cyan/10' : 'border-white/10 bg-gradient-to-br from-gray-700 to-gray-900'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input 
          ref={fileInputRef}
          type="file" 
          className="hidden" 
          accept="image/jpeg, image/png, image/webp" 
          onChange={handleChange} 
        />
        
        {previewUrl ? (
          <img src={previewUrl} alt="Avatar" className="w-full h-full object-cover" />
        ) : (
          <span className="text-3xl font-bold uppercase tracking-widest text-white/70">
            {username.charAt(0)}
          </span>
        )}

        <div className="absolute inset-0 bg-black/60 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
          {uploadMutation.isPending ? (
            <Loader2 className="animate-spin text-white" size={24} />
          ) : (
            <Camera className="text-white" size={24} />
          )}
        </div>
      </div>
      
      <div className="flex flex-col gap-2">
        <div className="flex gap-3">
          <button 
            onClick={() => fileInputRef.current?.click()}
            className="text-sm font-medium text-white bg-white/10 hover:bg-white/15 px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
          >
            <UploadCloud size={16} /> Upload New
          </button>
          
          {previewUrl && (
            <button 
              onClick={() => deleteMutation.mutate()}
              disabled={deleteMutation.isPending}
              className="text-sm font-medium text-red-400 hover:text-red-300 bg-red-400/10 hover:bg-red-400/20 px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
            >
              <X size={16} /> Remove
            </button>
          )}
        </div>
        <p className="text-xs text-text-muted">Max size: 5MB. Formats: JPG, PNG, WEBP.</p>
      </div>
    </div>
  );
}
