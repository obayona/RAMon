import Chat from '@/components/chat/Chat';

interface Props {
   open: boolean;
}

export default function ChatWindow({ open }: Props) {
   if (!open) return null;

   return (
      <div className='mb-4 flex h-[700px] w-[420px] flex-col overflow-hidden rounded-2xl border bg-background shadow-2xl'>
         <Chat />
      </div>
   );
}
