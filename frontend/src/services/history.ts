import type { ChatMessage, Product } from '@/types/chat';

interface HistoryResponse {
   id: string;
   type: 'human' | 'ai';
   text?: string;
   ui_data?: {
      layout: 'carousel';
      products: Product[];
   };
}

interface LoadHistoryParams {
   apiUrl: string;
   token: string;
   chatId: string;
}

export async function loadHistory({
   apiUrl,
   token,
   chatId,
}: LoadHistoryParams): Promise<ChatMessage[]> {
   const response = await fetch(`${apiUrl}/chat/${chatId}`, {
      headers: {
         Authorization: `Bearer ${token}`,
      },
   });

   if (!response.ok) {
      throw new Error('Failed to load chat history');
   }

   const data: HistoryResponse[] = await response.json();

   return data.map((message) => ({
      id: message.id,
      role: message.type === 'human' ? 'user' : 'assistant',
      content: message.text,
      products: message.ui_data?.products,
   }));
}
