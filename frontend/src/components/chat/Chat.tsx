import { useChat } from '@/hooks/useChat';
import ChatHeader from './ChatHeader';
import ChatInput from './ChatInput';
import ChatMessages from './ChatMessages';

interface Props {
   expanded: boolean;

   toggleExpanded: () => void;
}

export default function Chat({ expanded, toggleExpanded }: Props) {
   const { messages, loading, sendMessage } = useChat();

   return (
      <main className='flex h-full flex-col bg-white border border-solid border-b rounded-lg'>
         <ChatHeader
            expanded={expanded}
            toggleExpanded={toggleExpanded}
         />

         <ChatMessages messages={messages} loading={loading} />

         <ChatInput onSend={sendMessage} />
      </main>
   );
}
