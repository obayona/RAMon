export interface Product {
   id: number;
   name: string;
   description: string;
   price: number;
   image?: string;
}

export interface ChatMessage {
   id: string;
   role: 'user' | 'assistant';
   content?: string;
   products?: Product[];
}

export interface WSMessage {
   type: 'text' | 'ui_data';
   id?: string;
   content?: string;
   products?: Product[];
}
