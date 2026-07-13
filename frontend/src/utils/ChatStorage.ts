export function getChatId() {
   const chatId = localStorage.getItem('chat_id');

   if (chatId) {
      return chatId;
   }

   const newId = `chat-${Date.now()}`;

   localStorage.setItem('chat_id', newId);

   return newId;
}

export function getToken() {
   const el = document.getElementById('ramon_data');

   if (!el) return '';

   try {
      const data = JSON.parse(el.textContent ?? '{}');

      return data.token ?? '';
   } catch {
      return '';
   }
}
