import { getChatId } from '@/utils/ChatStorage';

export function createSocket(onMessage: (event: MessageEvent) => void) {
   const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

   const chatId = getChatId();

   const socket = new WebSocket(
      `${protocol}//localhost:8080/ws?chat_id=${chatId}`,
   );

   socket.onopen = () => {
      console.log('Connected');
   };

   socket.onclose = () => {
      console.log('Disconnected');
   };

   socket.onmessage = onMessage;

   return socket;
}
