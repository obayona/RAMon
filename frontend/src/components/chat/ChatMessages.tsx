import type { ChatMessage } from '@/types/chat';
import MessageBubble from '../messages/MessageBubble';
import { WelcomeScreen } from '../helpers/WelcomeScreen';
import { useEffect, useRef } from 'react';

interface Props {
   messages: ChatMessage[];
   loading: boolean;
}

export default function ChatMessages({ messages, loading }: Props) {
   const containerRef = useRef<HTMLDivElement>(null);

   useEffect(() => {
      if (!containerRef.current) return;

      containerRef.current.scrollTop = containerRef.current.scrollHeight;
   }, [messages]);
   return (
      <div ref={containerRef} className='flex-1 overflow-y-auto p-6'>
         <div className='mx-auto flex w-full max-w-4xl flex-col gap-6'>
            {messages.length === 0 ? (
               <WelcomeScreen />
            ) : (
               messages.map((message) => (
                  <MessageBubble key={message.id} message={message} />
               ))
            )}

            {loading && (
               <div className='text-sm text-slate-400'>
                  RAMon está escribiendo...
               </div>
            )}
         </div>
      </div>
   );
}
