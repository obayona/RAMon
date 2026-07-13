import { useState } from 'react';

import FloatingButton from './FloatingButton';
import ChatWindow from './ChatWindow';

export default function RamonWidget() {
   const [open, setOpen] = useState(false);

   return (
      <div className='fixed bottom-6 right-6 z-[999999] flex flex-col items-end'>
         <ChatWindow open={open} />

         <FloatingButton open={open} onClick={() => setOpen((v) => !v)} />
      </div>
   );
}
