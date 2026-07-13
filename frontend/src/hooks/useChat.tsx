import { useEffect, useRef, useState } from 'react';
import type { ChatMessage, WSMessage } from '@/types/chat';
import { createSocket } from '@/services/websocket';
import { useRamonConfig } from '@/context/RamonContext';
import { loadHistory } from '@/services/history';

// const CHAT_ID = 'test';
// const currentProductId = '230670';

export function useChat() {
   const { apiUrl, token, productId } = useRamonConfig();
   const [messages, setMessages] = useState<ChatMessage[]>([]);

   const [loading, setLoading] = useState(false);
   const chatId = useRef(getChatId());
   function handleMessage(event: MessageEvent) {
      const data: WSMessage = JSON.parse(event.data);

      if (data.type === 'text') {
         setLoading(false);

         setMessages((prev) => {
            const index = prev.findIndex((m) => m.id === data.id);

            // Ya existe el mensaje -> añadir el nuevo fragmento
            if (index !== -1) {
               const updated = [...prev];

               updated[index] = {
                  ...updated[index],
                  content: updated[index].content + (data.content ?? ''),
               };

               return updated;
            }

            // Primer fragmento del mensaje
            return [
               ...prev,
               {
                  id: data.id!,
                  role: 'assistant',
                  content: data.content ?? '',
               },
            ];
         });
      }

      if (data.type === 'ui_data') {
         setMessages((prev) => {
            const updated = [...prev];

            const lastAssistant = [...updated]
               .reverse()
               .find((m) => m.role === 'assistant');

            if (!lastAssistant) return prev;

            lastAssistant.products = data.products ?? [];

            return [...updated];
         });
      }
   }
   async function loadOldHistory() {
      try {
         const history = await loadHistory({
            apiUrl,
            token,
            chatId: chatId.current,
         });

         setMessages(history);
      } catch (err) {
         console.error(err);
      }
   }
   useEffect(() => {
      loadOldHistory();
      socket.current = createSocket({
         apiUrl,
         token,
         chatId: chatId.current,
         onMessage: handleMessage,
      });

      return () => {
         socket.current?.close();
      };
   }, []);

   const socket = useRef<WebSocket | null>(null);

   const sendMessage = (text: string) => {
      // Mostrar inmediatamente el mensaje del usuario

      setMessages((prev) => [
         ...prev,

         {
            id: crypto.randomUUID(),

            role: 'user',

            content: text,
         },
      ]);

      // Mostrar "escribiendo..."

      setLoading(true);

      // Enviar al backend

      socket.current?.send(
         JSON.stringify({
            message: text,

            chat_id: chatId,

            current_product_id: productId,
         }),
      );
   };

   function getChatId() {
      const existing = localStorage.getItem('chat_id');

      if (existing) {
         return existing;
      }

      const id = `chat-${Date.now()}`;

      localStorage.setItem('chat_id', id);

      return id;
   }

   return {
      messages,

      loading,
      sendMessage,
   };
}
