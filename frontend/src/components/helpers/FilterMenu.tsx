// import { Button } from '@/components/ui/button';

import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { cn } from '@/lib/utils';
import { useState } from 'react';

interface Props {
   open: boolean;
}

export function FilterMenu({ open }: Props) {
   const [value, setValue] = useState([0, 3000]);
   return (
      <div
         className={cn(
            'overflow-hidden transition-all duration-300 border-b',
            open ? 'max-h-96' : 'max-h-0 border-b-0',
         )}
      >
         <div className='  space-y-5 bg-slate-50 p-4'>
            {/* <div className='space-y-2' flex-1>
               <Label>Brand</Label>

               <div className='flex flex-wrap gap-2'>
                  <Button variant='outline' size='sm'>
                     AMD
                  </Button>

                  <Button variant='outline' size='sm'>
                     Intel
                  </Button>

                  <Button variant='outline' size='sm'>
                     NVIDIA
                  </Button>

                  <Button variant='outline' size='sm'>
                     ASUS
                  </Button>
               </div>
            </div> */}

            <div className='space-y-2 w-1/4'>
               <div className='flex justify-between'>
                  <Label>Price</Label>

                  <span className='text-xs text-muted-foreground'>
                     ${value.join('-$')}
                  </span>
               </div>

               <Slider
                  defaultValue={[0, 3000]}
                  min={0}
                  max={3000}
                  step={50}
                  value={value}
                  onValueChange={(value) => setValue(value as number[])}
               />
            </div>

            {/* <div className='flex justify-end gap-2'>
               <Button variant='ghost' size='sm'>
                  Clear
               </Button>

               <Button size='sm'>Apply</Button>
            </div> */}
         </div>
      </div>
   );
}
