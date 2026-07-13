interface CreateSocketOptions {
   apiUrl: string;
   token: string;
   chatId: string;
   onMessage: (event: MessageEvent) => void;
}

export function createSocket({
   apiUrl,
   token,
   chatId,
   onMessage,
}: CreateSocketOptions) {
   const wsUrl =
      apiUrl.replace(/^http/, 'ws') +
      `/ws?chat_id=${chatId}&token=${encodeURIComponent(token)}`;

   const socket = new WebSocket(wsUrl);

   socket.onopen = () => {
      console.log('Connected');
   };

   socket.onclose = () => {
      console.log('Disconnected');
   };

   socket.onmessage = onMessage;

   return socket;
}
