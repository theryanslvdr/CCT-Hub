import React, { useEffect, useCallback } from 'react';

/**
 * ContentProtection Component
 * Implements copy/screenshot prevention measures:
 * - Disables text selection (CSS)
 * - Blocks right-click context menu
 * - Blocks keyboard shortcuts (Ctrl+C, Ctrl+A, PrtScn, etc.)
 * - Shows watermark overlay with user info
 */
export const ContentProtection = ({ 
  enabled = false,
  userEmail = '',
  userName = '',
  showWatermark = true,
  disableCopy = true,
  disableRightClick = true,
  disableShortcuts = true
}) => {
  // Handle keyboard shortcuts
  const handleKeyDown = useCallback((e) => {
    if (!enabled || !disableShortcuts) return;
    
    // Block common copy/screenshot shortcuts
    const blockedCombos = [
      // Copy shortcuts
      { ctrl: true, key: 'c' },
      { ctrl: true, key: 'a' },
      { ctrl: true, key: 'x' },
      { ctrl: true, key: 'u' }, // View source
      { ctrl: true, key: 's' }, // Save page
      { ctrl: true, key: 'p' }, // Print
      // Screenshot shortcuts
      { ctrl: true, shift: true, key: 's' }, // Windows Snipping Tool
      { ctrl: true, shift: true, key: '4' }, // Mac screenshot
      { meta: true, shift: true, key: '3' }, // Mac full screenshot
      { meta: true, shift: true, key: '4' }, // Mac area screenshot
      { meta: true, shift: true, key: '5' }, // Mac screenshot menu
    ];
    
    // Check for Print Screen key
    if (e.key === 'PrintScreen' || e.keyCode === 44) {
      e.preventDefault();
      e.stopPropagation();
      
      // Flash screen or show warning
      showProtectionWarning();
      return false;
    }
    
    // Check for blocked combinations
    for (const combo of blockedCombos) {
      const ctrlMatch = combo.ctrl ? (e.ctrlKey || e.metaKey) : true;
      const shiftMatch = combo.shift ? e.shiftKey : !e.shiftKey || combo.shift === undefined;
      const metaMatch = combo.meta ? e.metaKey : true;
      const keyMatch = e.key?.toLowerCase() === combo.key;
      
      if (ctrlMatch && shiftMatch && metaMatch && keyMatch) {
        e.preventDefault();
        e.stopPropagation();
        showProtectionWarning();
        return false;
      }
    }
  }, [enabled, disableShortcuts]);
  
  // Handle right-click
  const handleContextMenu = useCallback((e) => {
    if (!enabled || !disableRightClick) return;
    e.preventDefault();
    showProtectionWarning();
    return false;
  }, [enabled, disableRightClick]);
  
  // Handle copy event
  const handleCopy = useCallback((e) => {
    if (!enabled || !disableCopy) return;
    e.preventDefault();
    showProtectionWarning();
    return false;
  }, [enabled, disableCopy]);
  
  // Handle cut event
  const handleCut = useCallback((e) => {
    if (!enabled || !disableCopy) return;
    e.preventDefault();
    showProtectionWarning();
    return false;
  }, [enabled, disableCopy]);
  
  // Show warning toast or flash
  const showProtectionWarning = () => {
    // Create temporary warning overlay
    const warning = document.createElement('div');
    warning.id = 'protection-warning';
    warning.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.9);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 99999;
      animation: fadeInOut 1.5s ease-in-out forwards;
    `;
    warning.innerHTML = `
      <div style="text-align: center; color: white;">
        <svg style="width: 64px; height: 64px; margin: 0 auto 16px;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
        </svg>
        <p style="font-size: 18px; font-weight: 600;">Content Protected</p>
        <p style="font-size: 14px; opacity: 0.7; margin-top: 8px;">This action is not allowed</p>
      </div>
    `;
    
    // Add animation style
    const style = document.createElement('style');
    style.textContent = `
      @keyframes fadeInOut {
        0% { opacity: 0; }
        20% { opacity: 1; }
        80% { opacity: 1; }
        100% { opacity: 0; }
      }
    `;
    document.head.appendChild(style);
    document.body.appendChild(warning);
    
    // Remove after animation
    setTimeout(() => {
      warning.remove();
      style.remove();
    }, 1500);
  };
  
  // Apply protection styles and event listeners
  useEffect(() => {
    if (!enabled) return;
    
    // Add event listeners
    document.addEventListener('keydown', handleKeyDown, true);
    document.addEventListener('contextmenu', handleContextMenu, true);
    document.addEventListener('copy', handleCopy, true);
    document.addEventListener('cut', handleCut, true);
    
    // Add CSS to disable text selection
    if (disableCopy) {
      document.body.style.userSelect = 'none';
      document.body.style.webkitUserSelect = 'none';
      document.body.style.msUserSelect = 'none';
      document.body.style.MozUserSelect = 'none';
    }
    
    // Cleanup
    return () => {
      document.removeEventListener('keydown', handleKeyDown, true);
      document.removeEventListener('contextmenu', handleContextMenu, true);
      document.removeEventListener('copy', handleCopy, true);
      document.removeEventListener('cut', handleCut, true);
      
      // Reset selection style
      document.body.style.userSelect = '';
      document.body.style.webkitUserSelect = '';
      document.body.style.msUserSelect = '';
      document.body.style.MozUserSelect = '';
    };
  }, [enabled, disableCopy, handleKeyDown, handleContextMenu, handleCopy, handleCut]);
  
  // Render watermark overlay if enabled
  if (!enabled || !showWatermark) return null;
  
  const watermarkText = userName || userEmail || 'Protected Content';
  
  return (
    <div 
      className="fixed inset-0 pointer-events-none z-[9999] overflow-hidden select-none"
      style={{ 
        opacity: 0.03,
        background: 'transparent'
      }}
      aria-hidden="true"
    >
      {/* Diagonal watermark pattern */}
      <div 
        className="absolute inset-0"
        style={{
          backgroundImage: `repeating-linear-gradient(
            -45deg,
            transparent,
            transparent 100px,
            rgba(255,255,255,0.02) 100px,
            rgba(255,255,255,0.02) 200px
          )`,
        }}
      />
      
      {/* Repeated watermark text */}
      <div 
        className="absolute inset-0 flex flex-wrap items-center justify-center gap-32"
        style={{
          transform: 'rotate(-30deg) scale(1.5)',
          transformOrigin: 'center center',
        }}
      >
        {Array.from({ length: 50 }).map((_, i) => (
          <span 
            key={i}
            className="text-white text-sm font-mono whitespace-nowrap"
            style={{ 
              opacity: 0.5,
              textShadow: '0 0 2px rgba(0,0,0,0.3)'
            }}
          >
            {watermarkText}
          </span>
        ))}
      </div>
    </div>
  );
};

export default ContentProtection;
