import { useChat } from '@/hooks/useChat';
import ChatHeader from './ChatHeader';
import ChatInput from './ChatInput';
import ChatMessages from './ChatMessages';
import { useState } from 'react';
import { FilterMenu } from '../helpers/FilterMenu';
interface Props {
   expanded: boolean;

   toggleExpanded: () => void;
}

export default function Chat({ expanded, toggleExpanded }: Props) {
   const { messages, loading, sendMessage } = useChat();
   const [filtersOpen, setFiltersOpen] = useState(false);
   return (
      <main className='flex h-full flex-col bg-white border border-solid border-b rounded-lg'>
         <ChatHeader
            expanded={expanded}
            toggleExpanded={toggleExpanded}
            filtersOpen={filtersOpen}
            toggleFilters={() => setFiltersOpen(!filtersOpen)}
         />
         <FilterMenu open={filtersOpen} />

         <ChatMessages messages={messages} loading={loading} />

         <ChatInput onSend={sendMessage} />
      </main>
   );
}
