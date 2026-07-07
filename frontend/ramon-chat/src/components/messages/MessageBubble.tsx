import type { ChatMessage } from '@/types/chat';
import { motion } from 'framer-motion';
import { Avatar } from '../helpers/Avatar';

import ProductCarousel from './ProductCarousel';

interface Props {
   message: ChatMessage;
}

export default function MessageBubble({ message }: Props) {
   const isUser = message.role === 'user';

   return (
      <motion.div
         initial={{ opacity: 0, y: 6 }}
         animate={{ opacity: 1, y: 0 }}
         className={`flex gap-3 my-4 ${isUser ? 'justify-end' : 'justify-start'}`}
      >
         {!isUser && <Avatar role='assistant' />}

         <div
            className={`max-w-[75%]  px-4 py-3 rounded-2xl text-sm leading-relaxed ${
               isUser
                  ? 'bg-blue-600 text-white rounded-br-sm'
                  : 'bg-gray-100 text-gray-900 rounded-bl-sm'
            }`}
         >
            {message.content && <p>{message.content}</p>}
            <div className='flex gap-3 '>
               {message.products && message.products.length > 0 && (
                  <ProductCarousel products={message.products} />
               )}
            </div>
         </div>

         {isUser && <Avatar role='user' />}
      </motion.div>
   );
}
