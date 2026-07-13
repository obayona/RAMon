import { Bot } from 'lucide-react';

export default function ChatHeader() {
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
            <span className='h-2 w-2 rounded-full bg-green-500' />

            <span className='text-sm text-slate-500'>Online</span>
         </div>
      </header>
   );
}
