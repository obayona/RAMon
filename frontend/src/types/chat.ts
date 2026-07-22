export interface Product {
   id: string;
   product_id: string;
   sku: string;
   name: string;
   description: string;
   categories: string;
   price: number;
   stock: number;
   url: string;
   image_url?: string;
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
