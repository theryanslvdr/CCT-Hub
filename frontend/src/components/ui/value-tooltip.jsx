import React, { useState, useRef, useEffect } from 'react';

/**
 * ValueTooltip - A component that shows exact values on hover/click
 * - Hover: Shows tooltip, disappears on mouse leave
 * - Click: Tooltip stays until user clicks elsewhere
 */
export const ValueTooltip = ({ 
  children, 
  exactValue, 
  className = '' 
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isLocked, setIsLocked] = useState(false);
  const containerRef = useRef(null);

  // Handle click outside to close locked tooltip
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsLocked(false);
        setIsVisible(false);
      }
    };

    if (isLocked) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isLocked]);

  const handleMouseEnter = () => {
    if (!isLocked) {
      setIsVisible(true);
    }
  };

  const handleMouseLeave = () => {
    if (!isLocked) {
      setIsVisible(false);
    }
  };

  const handleClick = (e) => {
    e.stopPropagation();
    if (isLocked) {
      setIsLocked(false);
      setIsVisible(false);
    } else {
      setIsLocked(true);
      setIsVisible(true);
    }
  };

  return (
    <div 
      ref={containerRef}
      className={`relative inline-block cursor-pointer ${className}`}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onClick={handleClick}
    >
      {children}
      
      {isVisible && (
        <div 
          className={`absolute z-50 px-3 py-2 text-sm font-mono rounded-lg shadow-lg whitespace-nowrap
            bg-[#1a1a1a] border border-white/[0.08] text-white
            bottom-full left-1/2 -translate-x-1/2 mb-2
            animate-in fade-in-0 zoom-in-95 duration-200
            ${isLocked ? 'ring-2 ring-orange-500/50' : ''}
          `}
        >
          <div className="flex items-center gap-2">
            <span className="text-zinc-400 text-xs">Exact:</span>
            <span className="text-emerald-400">{exactValue}</span>
          </div>
          {isLocked && (
            <p className="text-[10px] text-zinc-500 mt-1 text-center">Click to close</p>
          )}
          {/* Arrow */}
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-px">
            <div className="w-2 h-2 bg-[#1a1a1a] border-r border-b border-white/[0.08] rotate-45" />
          </div>
        </div>
      )}
    </div>
  );
};

export default ValueTooltip;
