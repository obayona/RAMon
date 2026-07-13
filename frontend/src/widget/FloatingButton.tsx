import { MessageCircle, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Props {
   open: boolean;
   onClick: () => void;
}

export default function FloatingButton({ open, onClick }: Props) {
   return (
      <Button
         size='icon'
         onClick={onClick}
         className='h-14 w-14 rounded-full shadow-xl'
      >
         {open ? (
            <X className='h-6 w-6' />
         ) : (
            <MessageCircle className='h-6 w-6' />
         )}
      </Button>
   );
}
