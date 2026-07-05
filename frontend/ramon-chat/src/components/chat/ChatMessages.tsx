import type { ChatMessage } from '@/types/chat';
import MessageBubble from './MessageBubble';
import { WelcomeScreen } from '../helpers/WelcomeScreen';

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
   {
      id: '4',
      role: 'assistant',
      content: 'Aqui tienes 3 productos que relacionados a tu request',
      products: [
         {
            id: 1,
            description: 'Camera 1',
            name: 'Camara Sony',
            price: 15000,
         },
         {
            id: 2,
            description: 'Camera 1',
            name: 'Camara Sony',
            price: 15000,
         },
         {
            id: 3,
            description: 'Camera 1',
            name: 'Camara Sony',
            price: 15000,
         },
      ],
   },
];

export default function ChatMessages() {
   return (
      <div className='flex-1 overflow-y-auto p-6'>
         <div className='mx-auto flex w-full max-w-4xl flex-col gap-6'>
            {messages.length === 0 ? (
               <WelcomeScreen />
            ) : (
               messages.map((message) => (
                  <MessageBubble key={message.id} message={message} />
               ))
            )}
         </div>
      </div>
   );
}
