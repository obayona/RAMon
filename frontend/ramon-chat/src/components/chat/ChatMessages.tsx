import type { ChatMessage } from '@/types/chat';
import MessageBubble from '../messages/MessageBubble';
import { WelcomeScreen } from '../helpers/WelcomeScreen';
import { useEffect, useRef } from 'react';

// const messages: ChatMessage[] = [
//    {
//       id: '1',
//       role: 'assistant',
//       content: '¡Hola! Soy RAMon. ¿En qué puedo ayudarte hoy?',
//    },
//    {
//       id: '2',
//       role: 'user',
//       content: 'Explícame qué es un switch PoE.',
//    },
//    {
//       id: '3',
//       role: 'assistant',
//       content:
//          'Un switch PoE permite transmitir datos y alimentación eléctrica por el mismo cable Ethernet.',
//    },
//    {
//       id: '4',
//       role: 'assistant',
//       content: 'Aqui tienes 3 productos que relacionados a tu request',
//       products: [
//          {
//             id: 1,
//             description: 'Camera sony with 20 megapixels, bluetooth, strap.',
//             name: 'Camara Sony',
//             price: 15000,
//          },
//          {
//             id: 2,
//             description: 'Camera sony with 20 megapixels, bluetooth, strap.',
//             name: 'Camara Sony',
//             price: 15000,
//          },
//          {
//             id: 3,
//             description: 'Camera sony with 20 megapixels, bluetooth, strap.',
//             name: 'Camara Sony',
//             price: 15000,
//          },
//       ],
//    },
// ];

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
