<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Domain;

/**
 * Immutable value object representing product data for sync.
 */
final class ProductData
{
    public function __construct(
        public readonly string $productId,
        public readonly string $sku,
        public readonly string $name,
        public readonly string $description,
        public readonly string $categories,
        public readonly float $price,
        public readonly int $stock,
        public readonly bool $inStock,
        public readonly string $url,
        public readonly string $imageUrl,
        public readonly string $status,
    ) {
    }

    /**
     * Create from an associative array.
     */
    public static function fromArray(array $data): self
    {
        return new self(
            productId: (string) ($data['product_id'] ?? ''),
            sku: (string) ($data['sku'] ?? ''),
            name: (string) ($data['name'] ?? ''),
            description: (string) ($data['description'] ?? ''),
            categories: (string) ($data['categories'] ?? ''),
            price: (float) ($data['price'] ?? 0.0),
            stock: (int) ($data['stock'] ?? 0),
            inStock: (bool) ($data['in_stock'] ?? true),
            url: (string) ($data['url'] ?? ''),
            imageUrl: (string) ($data['image_url'] ?? ''),
            status: (string) ($data['status'] ?? 'publish'),
        );
    }

    /**
     * Convert to an associative array.
     */
    public function toArray(): array
    {
        return [
            'product_id' => $this->productId,
            'sku' => $this->sku,
            'name' => $this->name,
            'description' => $this->description,
            'categories' => $this->categories,
            'price' => $this->price,
            'stock' => $this->stock,
            'in_stock' => $this->inStock,
            'url' => $this->url,
            'image_url' => $this->imageUrl,
            'status' => $this->status,
        ];
    }
}
