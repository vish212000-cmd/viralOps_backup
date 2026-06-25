import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { Button } from './design/Button';
import { cn } from '../utils/cn';
import { 
  Sparkles, LayoutDashboard, Video, Palette, BarChart2, Settings, ChevronRight, X, CreditCard, User
} from 'lucide-react';

interface SidebarProps {
  isMobileOpen?: boolean;
  onClose?: () => void;
}

export default function Sidebar({ isMobileOpen = false, onClose = () => {} }: SidebarProps) {
  const { user, orgs, currentOrg, logoutUser, selectOrg, loadWorkspaces } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isHovered, setIsHovered] = useState(false);
  const [showOrgDropdown, setShowOrgDropdown] = useState(false);

  // Responsive state logic
  const [windowWidth, setWindowWidth] = useState(typeof window !== 'undefined' ? window.innerWidth : 1200);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const isExpandedDesktop = windowWidth >= 1280;
  const isNormalDesktop = windowWidth >= 1024 && windowWidth < 1280;
  const isMobile = windowWidth < 1024;

  const showExpanded = isExpandedDesktop || (isNormalDesktop && isHovered) || (isMobile && isMobileOpen);

  const handleLogout = () => {
    logoutUser();
    navigate('/');
  };

  const navItems = [
    { name: 'Overview', path: '/dashboard', icon: LayoutDashboard },
    { name: 'My Content', path: '/content', icon: Video },
    { name: 'Brand Kit', path: '/brand-kit', icon: Palette },
    { name: 'Performance', path: '/performance', icon: BarChart2 },
    { name: 'Billing', path: '/billing', icon: CreditCard },
    { name: 'Profile', path: '/profile', icon: User },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  // Animation values based on screen size responsive rules
  let asideWidth = '240px';
  let asideX: string | number = 0;

  if (isMobile) {
    asideWidth = '240px';
    asideX = isMobileOpen ? '0%' : '-100%';
  } else if (isNormalDesktop) {
    asideWidth = isHovered ? '240px' : '80px';
    asideX = '0%';
  } else {
    // isExpandedDesktop
    asideWidth = '240px';
    asideX = '0%';
  }

  return (
    <motion.aside
      initial={isMobile ? { x: '-100%', width: '240px' } : { width: isNormalDesktop ? '80px' : '240px', x: 0 }}
      animate={{ width: asideWidth, x: asideX }}
      transition={{ type: "spring", stiffness: 220, damping: 26 }}
      onHoverStart={() => !isMobile && !isExpandedDesktop && setIsHovered(true)}
      onHoverEnd={() => !isMobile && !isExpandedDesktop && setIsHovered(false)}
      className={cn(
        "fixed top-0 bottom-0 z-50 flex flex-col justify-between bg-bg-surface/95 backdrop-blur-md border-r border-white/5 py-8 overflow-hidden group",
        isMobile ? "left-0 shadow-[5px_0_25px_-5px_rgba(0,0,0,0.5)]" : "left-0"
      )}
    >
      {/* Absolute ambient glow */}
      <div className="absolute top-0 right-0 w-full h-full bg-gradient-to-b from-accent-primary/5 to-transparent pointer-events-none" />

      <div className="flex flex-col gap-8 w-full relative z-10 px-6">
        {/* Logo Area & Mobile Close Button */}
        <div className="flex items-center justify-between">
          <Link 
            to="/dashboard" 
            onClick={() => isMobile && onClose()}
            className="flex items-center gap-4 text-white hover:text-accent-cyan transition-colors group-hover:px-2"
          >
            <div className="relative flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center shadow-lg shadow-accent-primary/20">
              <Sparkles size={20} className="text-white" />
            </div>
            <AnimatePresence>
              {showExpanded && (
                <motion.span 
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  className="font-display font-bold text-xl whitespace-nowrap"
                >
                  ViralOps
                </motion.span>
              )}
            </AnimatePresence>
          </Link>
          
          {isMobile && (
            <button 
              onClick={onClose} 
              className="text-text-muted hover:text-white lg:hidden cursor-pointer"
              aria-label="Close sidebar menu"
            >
              <X size={20} />
            </button>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex flex-col gap-2" aria-label="Main Navigation">
          {navItems.map((item) => {
            const active = location.pathname === item.path;
            const Icon = item.icon;
            
            return (
              <Link 
                key={item.path}
                to={item.path} 
                onClick={() => isMobile && onClose()}
                className={cn(
                  "relative flex items-center gap-4 p-3 rounded-2xl transition-all group/item overflow-hidden",
                  active ? "text-white" : "text-text-muted hover:text-white"
                )}
              >
                {active && (
                  <motion.div 
                    layoutId="activeNavBackground"
                    className="absolute inset-0 bg-white/5 rounded-2xl border border-white/10"
                    transition={{ type: "spring", stiffness: 200, damping: 20 }}
                  />
                )}
                
                <div className="relative z-10 flex-shrink-0 w-6 h-6 flex items-center justify-center">
                  <Icon size={20} className={active ? "text-accent-cyan" : ""} />
                </div>
                
                <AnimatePresence>
                  {showExpanded && (
                    <motion.span
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: 'auto' }}
                      exit={{ opacity: 0, width: 0 }}
                      className="relative z-10 font-medium whitespace-nowrap overflow-hidden"
                    >
                      {item.name}
                    </motion.span>
                  )}
                </AnimatePresence>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* User / Workspace Area */}
      <div className="flex flex-col gap-4 relative z-10 px-6">
        <div className="w-full h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
        
        <div className="relative">
          <button 
            onClick={() => showExpanded && setShowOrgDropdown(!showOrgDropdown)}
            className="flex items-center gap-4 p-2 rounded-xl hover:bg-white/5 transition-colors w-full text-left focus-visible:ring-2 focus-visible:ring-accent-cyan outline-none"
            aria-expanded={showOrgDropdown}
            aria-haspopup="menu"
            aria-label="User Workspace Menu"
          >
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-gray-700 to-gray-900 border border-white/10 flex items-center justify-center text-sm font-bold shadow-inner text-white">
              {user?.username?.charAt(0).toUpperCase()}
            </div>
            
            <AnimatePresence>
              {showExpanded && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex-1 min-w-0"
                >
                  <div className="font-semibold text-sm truncate text-white">{user?.username}</div>
                  <div className="text-xs text-text-dim truncate">{currentOrg?.name || 'No Workspace'}</div>
                </motion.div>
              )}
            </AnimatePresence>

            <AnimatePresence>
              {showExpanded && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <ChevronRight size={16} className="text-text-dim" />
                </motion.div>
              )}
            </AnimatePresence>
          </button>
        </div>
      </div>
    </motion.aside>
  );
}
