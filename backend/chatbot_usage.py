from chatbot.service import ChatbotService
from chatbot.state import Product

# ------------------------------------------------------------------
# This scripts demonstarte the usage of the ChatbotService class
# ------------------------------------------------------------------


if __name__ == "__main__":
    svc = ChatbotService()
    # ---- Test 1: Product Recommendation ----
    user_query = "Necesito un KIT DE CAMARA EZVIZ, no importa el precio"
    print("=" * 72)
    print("TEST 1 — Product Recommendation")
    print(f"User: {user_query}")
    print("current_product: None")
    print("=" * 72)

    for data in svc.stream(
        user_query,
        thread_id="test-1",
    ):
        print(data)

    # ---- Test 2: Technical Compatibility ----
    user_query = "Es esta memoria RAM compatible con mi tarjeta ASUS Prime B450M?"
    print("\n" + "=" * 72)
    print("TEST 2 — Technical Compatibility")
    print(f"User: {user_query}")
    print("current_product: Corsair Vengeance LPX 16GB DDR4")
    print("=" * 72)

    current_ram: Product = {
        "id": "ram-001",
        "name": "Corsair Vengeance LPX 16GB (2x8GB) DDR4",
        "description": "DDR4 3200MHz CL16, 1.35V, Intel XMP 2.0, black PCB, dual-channel desktop memory kit",
        "price": 49.99,
        "url": "/products/ram-001",
    }

    for data in svc.stream(
        user_query,
        current_product=current_ram,
        thread_id="test-2",
    ):
        print(data)