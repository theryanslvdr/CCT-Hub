import React from 'react';
import { Smartphone, Monitor } from 'lucide-react';

/**
 * MobileNotice - Shows a notice when a feature is not optimized for mobile
 * Use this wrapper around components that don't work well on mobile
 */
export const MobileNotice = ({ 
  children, 
  featureName = 'This feature',
  showOnMobile = false  // If true, shows both notice and content
}) => {
  const [isMobile, setIsMobile] = React.useState(false);

  React.useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  if (!isMobile) {
    return <>{children}</>;
  }

  const notice = (
    <div className="p-6 text-center" data-testid="mobile-notice">
      <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-amber-500/20 border border-amber-500/50 flex items-center justify-center">
        <Smartphone className="w-8 h-8 text-amber-400" />
      </div>
      <h3 className="text-lg font-medium text-white mb-2">
        Better on Desktop
      </h3>
      <p className="text-sm text-zinc-400 max-w-sm mx-auto">
        {featureName} is currently not optimized for mobile devices. 
        Please use a desktop browser for the best experience.
      </p>
      <div className="mt-4 flex items-center justify-center gap-2 text-xs text-zinc-500">
        <Monitor className="w-4 h-4" />
        <span>Recommended: 768px or wider</span>
      </div>
    </div>
  );

  if (showOnMobile) {
    return (
      <>
        {children}
      </>
    );
  }

  return notice;
};

/**
 * useMobileDetect - Hook to detect mobile devices
 */
export const useMobileDetect = () => {
  const [isMobile, setIsMobile] = React.useState(false);
  const [isTablet, setIsTablet] = React.useState(false);

  React.useEffect(() => {
    const checkDevice = () => {
      const width = window.innerWidth;
      setIsMobile(width < 640);
      setIsTablet(width >= 640 && width < 1024);
    };
    
    checkDevice();
    window.addEventListener('resize', checkDevice);
    return () => window.removeEventListener('resize', checkDevice);
  }, []);

  return { isMobile, isTablet, isDesktop: !isMobile && !isTablet };
};

export default MobileNotice;
