import ChatHeader from './ChatHeader';
import ChatInput from './ChatInput';
import ChatMessages from './ChatMessages';

export default function Chat() {
   return (
      <main className='flex h-screen items-center justify-center bg-slate-100 p-6'>
         <section className='flex h-[90vh] w-full max-w-6xl flex-col overflow-hidden rounded-3xl border bg-white shadow-xl'>
            <ChatHeader />

            <ChatMessages />

            <ChatInput />
         </section>
      </main>
   );
}
