import { SendHorizontal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useState } from 'react';

interface Props {
   onSend(message: string): void;
}

export default function ChatInput({ onSend }: Props) {
   const [text, setText] = useState('');

   function handleSubmit(e: React.SubmitEvent<HTMLFormElement>) {
      e.preventDefault();

      if (!text.trim()) return;

      onSend(text);

      setText('');
   }
   return (
      <form onSubmit={handleSubmit} className='border-t p-4'>
         <div className='mx-auto flex max-w-4xl gap-3'>
            <Input
               value={text}
               onChange={(e) => setText(e.target.value)}
               placeholder='Pregunta sobre un producto...'
               className='h-12'
            />

            <Button
               type='submit'
               size='icon'
               variant={'secondary'}
               className='h-12 w-12'
            >
               <SendHorizontal className='h-5 w-5' />
            </Button>
         </div>
      </form>
   );
}
