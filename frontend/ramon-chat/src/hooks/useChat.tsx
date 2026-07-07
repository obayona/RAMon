import { useEffect, useRef, useState } from 'react';
import type { ChatMessage, WSMessage } from '@/types/chat';
import { createSocket } from '@/services/websocket';

const CHAT_ID = 'test';
const currentProductId = '230670';

export function useChat() {
   const [messages, setMessages] = useState<ChatMessage[]>([]);

   const [loading, setLoading] = useState(false);

   const socket = useRef<WebSocket | null>(null);
   function handleMessage(event: MessageEvent) {
      const data: WSMessage = JSON.parse(event.data);

      console.log(data);
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

   useEffect(() => {
      socket.current = createSocket(handleMessage);

      // ws.onmessage = (event) => {
      //    const data: WSMessage = JSON.parse(event.data);

      //    console.log(data);
      //    if (data.type === 'text') {
      //       setLoading(false);

      //       setMessages((prev) => {
      //          const index = prev.findIndex((m) => m.id === data.id);

      //          // El mensaje ya existe → streaming
      //          if (index !== -1) {
      //             const copy = [...prev];

      //             copy[index] = {
      //                ...copy[index],
      //                content: copy[index].content + (data.content ?? ''),
      //             };

      //             return copy;
      //          }

      //          // Primer fragmento
      //          return [
      //             ...prev,
      //             {
      //                id: data.id ?? crypto.randomUUID(),
      //                role: 'assistant',
      //                content: data.content ?? '',
      //             },
      //          ];
      //       });
      //    }

      //    if (data.type === 'ui_data') {
      //       setMessages((prev) => {
      //          const copy = [...prev];

      //          const lastAssistant = [...copy]
      //             .reverse()
      //             .find((m) => m.role === 'assistant');

      //          if (!lastAssistant) return prev;

      //          lastAssistant.products = data.products ?? [];

      //          return [...copy];
      //       });
      //    }
      // };

      return () => {
         socket.current?.close();
      };
   }, []);

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

            chat_id: CHAT_ID,

            current_product_id: currentProductId,
         }),
      );
   };

   return {
      messages,

      loading,
      sendMessage,
   };
}
