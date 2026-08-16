"""Ejecutar el servidor del chatbot."""
from app import app
from config import Config

if __name__ == "__main__":
    print(f"Iniciando servidor en http://{Config.HOST}:{Config.PORT}")
    print(f"Panel admin: http://localhost:{Config.PORT}/admin")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
