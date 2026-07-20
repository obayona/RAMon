<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Tests\Unit\Domain;

use PHPUnit\Framework\TestCase;
use Ramon\Chatbot\Domain\ProductData;

final class ProductDataTest extends TestCase
{
    public function testFromArray(): void
    {
        $data = [
            'product_id' => '42',
            'sku' => 'GPU-001',
            'name' => 'RTX 4090',
            'description' => 'Top-tier GPU',
            'categories' => 'Graphics Cards,NVIDIA',
            'price' => 1599.99,
            'stock' => 5,
            'in_stock' => true,
            'url' => 'https://example.com/product/42',
            'image_url' => 'https://example.com/img/42.jpg',
            'status' => 'publish',
        ];

        $product = ProductData::fromArray($data);

        $this->assertSame('42', $product->productId);
        $this->assertSame('GPU-001', $product->sku);
        $this->assertSame('RTX 4090', $product->name);
        $this->assertSame('Top-tier GPU', $product->description);
        $this->assertSame('Graphics Cards,NVIDIA', $product->categories);
        $this->assertSame(1599.99, $product->price);
        $this->assertSame(5, $product->stock);
        $this->assertTrue($product->inStock);
        $this->assertSame('https://example.com/product/42', $product->url);
        $this->assertSame('https://example.com/img/42.jpg', $product->imageUrl);
        $this->assertSame('publish', $product->status);
    }

    public function testFromArrayWithDefaults(): void
    {
        $product = ProductData::fromArray([]);

        $this->assertSame('', $product->productId);
        $this->assertSame('', $product->sku);
        $this->assertSame(0.0, $product->price);
        $this->assertSame(0, $product->stock);
        $this->assertTrue($product->inStock);
        $this->assertSame('published', $product->status);
    }

    public function testToArray(): void
    {
        $product = new ProductData(
            productId: '10',
            sku: 'CPU-002',
            name: 'Ryzen 9',
            description: 'Fast CPU',
            categories: 'Processors',
            price: 599.0,
            stock: 10,
            inStock: true,
            url: 'https://example.com/10',
            imageUrl: 'https://example.com/img/10.jpg',
            status: 'publish',
        );

        $array = $product->toArray();

        $this->assertSame('10', $array['product_id']);
        $this->assertSame('CPU-002', $array['sku']);
        $this->assertSame('Ryzen 9', $array['name']);
        $this->assertSame(599.0, $array['price']);
        $this->assertSame(10, $array['stock']);
        $this->assertTrue($array['in_stock']);
        $this->assertSame('publish', $array['status']);
    }

    public function testRoundTrip(): void
    {
        $original = [
            'product_id' => '99',
            'sku' => 'RAM-003',
            'name' => '32GB DDR5',
            'description' => 'Fast RAM',
            'categories' => 'Memory',
            'price' => 149.99,
            'stock' => 0,
            'in_stock' => false,
            'url' => 'https://example.com/99',
            'image_url' => '',
            'status' => 'draft',
        ];

        $product = ProductData::fromArray($original);
        $roundTripped = $product->toArray();

        $this->assertSame($original, $roundTripped);
    }
}
