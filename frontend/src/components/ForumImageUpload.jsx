import React, { useState, useRef } from 'react';
import { publitioAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { ImagePlus, X, Loader2, AlertCircle } from 'lucide-react';

const MAX_FILE_SIZE = 2 * 1024 * 1024; // 2MB
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];

/**
 * Forum Image Upload Component
 * Supports multiple images with preview, validation, and Publitio upload
 */
export default function ForumImageUpload({ 
  images = [], 
  onChange, 
  folder = 'forum/general',
  maxImages = 4,
  disabled = false 
}) {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef(null);

  const validateFile = (file) => {
    if (file.size > MAX_FILE_SIZE) {
      return `File "${file.name}" exceeds 2MB limit`;
    }
    if (!ALLOWED_TYPES.includes(file.type)) {
      return `File "${file.name}" is not a supported image type`;
    }
    return null;
  };

  const handleFileSelect = async (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    // Check remaining slots
    const remainingSlots = maxImages - images.length;
    if (remainingSlots <= 0) {
      toast.error(`Maximum ${maxImages} images allowed`);
      return;
    }

    const filesToUpload = files.slice(0, remainingSlots);

    // Validate all files first
    for (const file of filesToUpload) {
      const error = validateFile(file);
      if (error) {
        toast.error(error);
        return;
      }
    }

    setUploading(true);
    setUploadProgress(0);

    const newImages = [...images];

    for (let i = 0; i < filesToUpload.length; i++) {
      const file = filesToUpload[i];
      try {
        const response = await publitioAPI.uploadImage(
          file, 
          folder,
          (progress) => setUploadProgress(Math.round((i * 100 + progress) / filesToUpload.length))
        );
        
        if (response.data?.success && response.data?.url) {
          newImages.push({
            url: response.data.url,
            id: response.data.id,
            thumbnail: response.data.url_thumbnail || response.data.url,
          });
        } else {
          throw new Error('Upload failed');
        }
      } catch (err) {
        const msg = err.response?.data?.detail || 'Failed to upload image';
        toast.error(msg);
        break;
      }
    }

    setUploading(false);
    setUploadProgress(0);
    onChange(newImages);
    
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleRemove = (index) => {
    const newImages = images.filter((_, i) => i !== index);
    onChange(newImages);
  };

  const canAddMore = images.length < maxImages && !disabled;

  return (
    <div className="space-y-2">
      {/* Preview Grid */}
      {images.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {images.map((img, idx) => (
            <div 
              key={idx} 
              className="relative group w-20 h-20 rounded-lg overflow-hidden border border-white/[0.08] bg-[#1a1a1a]"
            >
              <img 
                src={img.thumbnail || img.url} 
                alt={`Upload ${idx + 1}`}
                className="w-full h-full object-cover"
              />
              {!disabled && (
                <button
                  type="button"
                  onClick={() => handleRemove(idx)}
                  className="absolute top-1 right-1 w-5 h-5 rounded-full bg-red-500 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                  data-testid={`remove-image-${idx}`}
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Upload Button */}
      <div className="flex items-center gap-2">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/gif,image/webp"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          disabled={!canAddMore || uploading}
          data-testid="image-file-input"
        />
        
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => fileInputRef.current?.click()}
          disabled={!canAddMore || uploading}
          className="gap-1.5 text-xs btn-secondary"
          data-testid="add-image-btn"
        >
          {uploading ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Uploading {uploadProgress}%
            </>
          ) : (
            <>
              <ImagePlus className="w-3.5 h-3.5" />
              Add Image
            </>
          )}
        </Button>
        
        {images.length > 0 && (
          <span className="text-[10px] text-zinc-500">
            {images.length}/{maxImages} images
          </span>
        )}
      </div>

      {/* Size limit notice */}
      <p className="text-[10px] text-zinc-600 flex items-center gap-1">
        <AlertCircle className="w-3 h-3" />
        Max 2MB per image. Supported: JPG, PNG, GIF, WebP
      </p>
    </div>
  );
}
