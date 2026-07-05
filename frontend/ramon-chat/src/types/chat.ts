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
