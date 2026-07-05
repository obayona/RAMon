import type { ChatMessage } from '@/types/chat';

interface Props {
   message: ChatMessage;
}

export default function MessageBubble({ message }: Props) {
   const isUser = message.role === 'user';

   return (
      <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
         <div
            className={`
          max-w-[75%]
          rounded-2xl
          px-5
          py-3
          text-sm
          leading-7
          shadow-sm
          ${isUser ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-900'}
        `}
         >
            {message.content}
         </div>
      </div>
   );
}
