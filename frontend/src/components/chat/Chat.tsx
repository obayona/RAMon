import { useChat } from '@/hooks/useChat';
import ChatHeader from './ChatHeader';
import ChatInput from './ChatInput';
import ChatMessages from './ChatMessages';

export default function Chat() {
   const { messages, loading, sendMessage } = useChat();
   return (
      <main className='flex h-full flex-col bg-white border border-solid border-b'>
         <ChatHeader />

         <ChatMessages messages={messages} loading={loading} />

         <ChatInput onSend={sendMessage} />
      </main>
   );
}
