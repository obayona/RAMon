import type { ChatMessage } from '@/types/chat';

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

   return await response.json();
}
