import uvicorn
from pyngrok import ngrok
import signal
import sys

def cleanup():
    print("Shutting down ngrok tunnel...")
    ngrok.disconnect(public_url)
    ngrok.kill()
    print("Ngrok tunnel stopped.")

if __name__ == "__main__":
    try:
        # Start ngrok tunnel
        public_url = ngrok.connect(8080)
        print(f"Public URL: {public_url}")
        
        # Start the FastAPI server
        uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
    except KeyboardInterrupt:
        cleanup()
        print("FastAPI server stopped.")
        sys.exit(0)

