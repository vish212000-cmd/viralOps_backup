import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { Button } from './design/Button';
import { cn } from '../utils/cn';
import { 
  Sparkles, Folder, Settings, BarChart2, CreditCard, Shield, LogOut, ChevronRight
} from 'lucide-react';

export default function Sidebar() {
  const { user, orgs, currentOrg, logoutUser, selectOrg, loadWorkspaces } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isHovered, setIsHovered] = useState(false);
  const [showOrgDropdown, setShowOrgDropdown] = useState(false);

  const handleLogout = () => {
    logoutUser();
    navigate('/');
  };

  const navItems = [
    { name: 'Projects', path: '/dashboard', icon: Folder },
    { name: 'Brand Voice', path: '/preferences', icon: Settings },
    { name: 'Analytics', path: '/analytics', icon: BarChart2 },
    { name: 'Billing', path: '/billing', icon: CreditCard },
    { name: 'Admin Center', path: '/admin', icon: Shield },
  ];

  return (
    <motion.aside
      initial={{ width: '80px' }}
      animate={{ width: isHovered ? '280px' : '80px' }}
      transition={{ type: "spring", stiffness: 200, damping: 25 }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      className="fixed left-0 top-0 bottom-0 z-50 flex flex-col justify-between bg-bg-surface/95 backdrop-blur-md border-r border-white/5 py-8 overflow-hidden group"
    >
      {/* Absolute ambient glow */}
      <div className="absolute top-0 right-0 w-full h-full bg-gradient-to-b from-accent-primary/5 to-transparent pointer-events-none" />

      <div className="flex flex-col gap-8 w-full relative z-10 px-6">
        {/* Logo Area */}
        <Link to="/dashboard" className="flex items-center gap-4 text-white hover:text-accent-cyan transition-colors group-hover:px-2">
          <div className="relative flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center shadow-lg shadow-accent-primary/20">
            <Sparkles size={20} className="text-white" />
          </div>
          <AnimatePresence>
            {isHovered && (
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

        {/* Navigation */}
        <nav className="flex flex-col gap-2">
          {navItems.map((item) => {
            const active = location.pathname === item.path;
            const Icon = item.icon;
            
            return (
              <Link 
                key={item.path}
                to={item.path} 
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
                  {isHovered && (
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
            onClick={() => isHovered && setShowOrgDropdown(!showOrgDropdown)}
            className="flex items-center gap-4 p-2 rounded-xl hover:bg-white/5 transition-colors w-full text-left"
          >
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-gray-700 to-gray-900 border border-white/10 flex items-center justify-center text-sm font-bold shadow-inner">
              {user?.username?.charAt(0).toUpperCase()}
            </div>
            
            <AnimatePresence>
              {isHovered && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex-1 min-w-0"
                >
                  <div className="font-semibold text-sm truncate">{user?.username}</div>
                  <div className="text-xs text-text-dim truncate">{currentOrg?.name || 'No Workspace'}</div>
                </motion.div>
              )}
            </AnimatePresence>

            <AnimatePresence>
              {isHovered && (
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
