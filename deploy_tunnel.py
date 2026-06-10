import threading
import time
from pyngrok import ngrok
from app import app

PORT = 5001

def run_app():
    app.run(host='0.0.0.0', port=PORT, debug=False)

if __name__ == '__main__':
    thread = threading.Thread(target=run_app, daemon=True)
    thread.start()
    time.sleep(1)
    public_url = ngrok.connect(PORT, "http").public_url
    print('App is running locally on http://127.0.0.1:%s' % PORT)
    print('Public ngrok URL:', public_url)
    print('Keep this process running to keep the tunnel open.')
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        ngrok.disconnect(public_url)
        ngrok.kill()
        print('Tunnel closed.')
