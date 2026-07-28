import Chat from '@/components/chat/Chat';
import { cn } from '@/lib/utils';
import { useState } from 'react';

interface Props {
   open: boolean;
}

export default function ChatWindow({ open }: Props) {
   const [expanded, setExpanded] = useState(true);

   if (!open) return null;

   return (
      <div
         className={cn(
            'mb-4 relative flex h-[700px] w-[420px] flex-col overflow-hidden rounded-lg border bg-background shadow-2xl',

            expanded ? 'h-[90vh] w-[90vw] max-w-6xl' : 'h-[650px] w-[420px]',
         )}
      >
         <Chat
            expanded={expanded}
            toggleExpanded={() => setExpanded(!expanded)}
         />
      </div>
   );
}
