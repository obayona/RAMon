"""Unit tests for domain ports — runtime_checkable Protocol checks."""

from chatbot.domain.ports import EmbeddingService, ProductRepository


class _GoodEmbeddingService:
    async def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


class _GoodProductRepository:
    async def search_by_similarity(
        self,
        embedding: list[float],
        min_price=None,
        max_price=None,
        min_similarity=None,
        limit=3,
    ) -> list[dict]:
        return []


class TestEmbeddingServiceProtocol:
    def test_valid_implementation(self) -> None:
        assert isinstance(_GoodEmbeddingService(), EmbeddingService)

    def test_plain_object_fails(self) -> None:
        assert not isinstance(object(), EmbeddingService)

    def test_class_with_missing_method_fails(self) -> None:
        class NoMethod:
            pass

        assert not isinstance(NoMethod(), EmbeddingService)


class TestProductRepositoryProtocol:
    def test_valid_implementation(self) -> None:
        assert isinstance(_GoodProductRepository(), ProductRepository)

    def test_plain_object_fails(self) -> None:
        assert not isinstance(object(), ProductRepository)

    def test_incomplete_implementation_fails(self) -> None:
        class Incomplete:
            pass

        assert not isinstance(Incomplete(), ProductRepository)
