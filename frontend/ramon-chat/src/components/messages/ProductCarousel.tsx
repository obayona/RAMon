import type { Product } from '@/types/chat';
import ProductCard from './ProductCard';

interface Props {
   products: Product[];
}

export default function ProductCarousel({ products }: Props) {
   return (
      <div className='mt-3 flex gap-3 overflow-x-auto pb-2'>
         {products.map((product) => (
            <ProductCard key={product.id} product={product} />
         ))}
      </div>
   );
}
