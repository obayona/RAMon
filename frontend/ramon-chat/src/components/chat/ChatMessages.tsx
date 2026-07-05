import type { ChatMessage } from '@/types/chat';
import MessageBubble from './MessageBubble';

const messages: ChatMessage[] = [
   {
      id: '1',
      role: 'assistant',
      content: '¡Hola! Soy RAMon. ¿En qué puedo ayudarte hoy?',
   },
   {
      id: '2',
      role: 'user',
      content: 'Explícame qué es un switch PoE.',
   },
   {
      id: '3',
      role: 'assistant',
      content:
         'Un switch PoE permite transmitir datos y alimentación eléctrica por el mismo cable Ethernet.',
   },
];

export default function ChatMessages() {
   return (
      <div className='flex-1 overflow-y-auto p-6'>
         <div className='mx-auto flex w-full max-w-4xl flex-col gap-6'>
            {messages.map((message) => (
               <MessageBubble key={message.id} message={message} />
            ))}
         </div>
      </div>
   );
}
