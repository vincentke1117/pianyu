import React from 'react';
import { Search, Sun, Moon, Feather } from 'lucide-react';

interface NavbarProps {
  isDark: boolean;
  toggleTheme: () => void;
  onHomeClick: () => void;
  onSearchClick: () => void;
}

const Navbar: React.FC<NavbarProps> = ({ isDark, toggleTheme, onHomeClick, onSearchClick }) => {
  return (
    <nav className="fixed top-0 left-0 right-0 h-16 z-50 transition-colors duration-500 backdrop-blur-md border-b 
      dark:bg-mineral-900/80 dark:border-white/10 
      bg-paper-50/80 border-black/5">
      
      <div className="max-w-7xl mx-auto px-4 h-full flex items-center justify-between">
        {/* Left: Logo & Slogan */}
        <div 
          className="flex items-center gap-4 cursor-pointer group"
          onClick={onHomeClick}
        >
          <div className="relative">
            <Feather 
              className="w-6 h-6 dark:text-gold text-gold-light transition-transform duration-500 group-hover:rotate-12" 
              strokeWidth={1.5}
            />
          </div>
          <div className="flex flex-col">
            <h1 className="text-xl font-serif font-bold tracking-wide dark:text-mineral-100 text-paper-900 leading-none">
              片羽
            </h1>
            <span className="hidden sm:block text-[10px] tracking-[0.2em] uppercase mt-1 dark:text-gray-400 text-gray-500 font-sans">
              Fragments of Wisdom
            </span>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={onSearchClick}
            className="p-2 rounded-full transition-all duration-300 dark:hover:bg-white/10 hover:bg-black/5 dark:text-mineral-100 text-paper-900 hover:text-gold dark:hover:text-gold"
            aria-label="Search"
          >
            <Search className="w-5 h-5" strokeWidth={1.5} />
          </button>
          
          <button 
            onClick={toggleTheme}
            className="p-2 rounded-full transition-all duration-300 dark:hover:bg-white/10 hover:bg-black/5 dark:text-gold text-gold-light overflow-hidden relative w-10 h-10 flex items-center justify-center"
            aria-label="Toggle Theme"
          >
            <div className={`absolute transition-transform duration-500 ${isDark ? 'rotate-0 scale-100' : 'rotate-90 scale-0'}`}>
               <Moon className="w-5 h-5" strokeWidth={1.5} />
            </div>
            <div className={`absolute transition-transform duration-500 ${!isDark ? 'rotate-0 scale-100' : '-rotate-90 scale-0'}`}>
               <Sun className="w-5 h-5" strokeWidth={1.5} />
            </div>
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;