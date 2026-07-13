import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import type { Product } from '@/types/chat';
import { Cpu } from 'lucide-react';

interface Props {
   product: Product;
}

export default function ProductCard({ product }: Props) {
   return (
      <Card className='w-50 shrink-0 overflow-hidden transition-shadow hover:shadow-md'>
         <CardContent className='p-3'>
            <div className='mb-3 flex aspect-square items-center justify-center overflow-hidden rounded-lg bg-slate-100'>
               {product.image ? (
                  <img
                     src={product.image}
                     alt={product.name}
                     className='h-full w-full object-cover'
                  />
               ) : (
                  <Cpu className='h-10 w-10 text-slate-400' />
               )}
            </div>

            <h3 className='line-clamp-2 text-sm font-semibold'>
               {product.name}
            </h3>

            <p className='mt-1 line-clamp-2 text-xs text-muted-foreground'>
               {product.description}
            </p>

            <div className='mt-3 flex items-center justify-between'>
               <span className='font-semibold text-primary'>
                  ${product.price?.toFixed(2)}
               </span>

               <a href={`/p=${product.product_id}`} className='border border-solid p-2'>Ver</a>
            </div>
         </CardContent>
      </Card>
   );
}
