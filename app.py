from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Importar rutas
from app.routes.auth_routes import auth_bp
from app.routes.cliente_routes import cliente_bp
from app.routes.membresia_routes import membresia_bp
from app.routes.pago_routes import pago_bp
from app.routes.registro_routes import registro_bp

load_dotenv()

app = Flask(__name__)
CORS(app)

# Registrar Blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(cliente_bp, url_prefix='/api/clientes')
app.register_blueprint(membresia_bp, url_prefix='/api/membresias')
app.register_blueprint(pago_bp, url_prefix='/api/pagos')
app.register_blueprint(registro_bp, url_prefix='/api/registros')

@app.route('/')
def index():
    return {"message": "Zona Fit Evolution API is running"}

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5050))
    app.run(host='0.0.0.0', port=port, debug=True)
