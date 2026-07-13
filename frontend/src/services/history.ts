import type { ChatMessage, Product } from '@/types/chat';

interface HistoryResponse {
   id: string;
   role: 'user' | 'assistant';
   content?: string;
   products?: Product[];
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

   return data.map((message, index) => ({
      id: `history-${index}`,
      role: message.role,
      content: message.content,
      products: message.products,
   }));
}
