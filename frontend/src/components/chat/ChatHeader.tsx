import { Bot, Funnel, Maximize2, Minimize2 } from 'lucide-react';
import { Button } from '../ui/button';

interface Props {
   expanded: boolean;
   filtersOpen: boolean;
   toggleExpanded: () => void;
   toggleFilters: () => void;
}

export default function ChatHeader({
   expanded,
   toggleExpanded,
   filtersOpen,
   toggleFilters,
}: Props) {
   return (
      <header className='flex items-center justify-between border-b px-6 py-4'>
         <div className='flex items-center gap-4'>
            <div className='rounded-2xl bg-blue-600 p-3 text-white'>
               <Bot className='h-6 w-6' />
            </div>

            <div>
               <h1 className='font-semibold text-slate-900'>RAMon</h1>

               <p className='text-sm text-slate-500'>Hardware Assistant</p>
            </div>
         </div>

         <div className='flex items-center gap-2'>
            <Button variant='ghost' size='icon' onClick={toggleFilters}>
               <Funnel className={filtersOpen ? 'text-blue-600' : ''} />
            </Button>
            <Button size='icon' variant='ghost' onClick={toggleExpanded}>
               {expanded ? <Minimize2 /> : <Maximize2 />}
            </Button>
         </div>
      </header>
   );
}
