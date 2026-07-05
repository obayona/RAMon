import { SendHorizontal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function ChatInput() {
   return (
      <footer className='border-t p-4'>
         <div className='mx-auto flex max-w-4xl gap-3'>
            <Input
               placeholder='Pregunta sobre un producto...'
               className='h-12'
            />

            <Button size='icon' variant={'secondary'} className='h-12 w-12'>
               <SendHorizontal className='h-5 w-5' />
            </Button>
         </div>
      </footer>
   );
}
