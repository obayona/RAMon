import type { Product } from '@/types/chat';
interface Props {
   product: Product;
}

export const ProductCard = ({ product }: Props) => {
   return (
      <div className='border rounded-xl p-3 mt-3 bg-white shadow-sm'>
         <div className='font-semibold'>{product.name}</div>
         <div className='text-sm text-gray-500'>{product.description}</div>
         <div className='mt-2 font-bold'>${product.price}</div>
      </div>
   );
};
