from chatbot.service import ChatbotService
from IPython.display import Image, display

# ------------------------------------------------------------------
# This scripts generates an image of the chatbot graph
# ------------------------------------------------------------------

if __name__ == "__main__":
    svc = ChatbotService()
    graph = svc.compiled_graph.get_graph()
    png_bytes = graph.draw_mermaid_png()

    # Save the bytes directly to a file
    with open("graph.png", "wb") as f:
        f.write(png_bytes)
