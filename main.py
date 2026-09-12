from flask import Flask, jsonify
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
import os
import datetime
from dotenv import load_dotenv


class ISODateJSONProvider(DefaultJSONProvider):
    """Por defecto, Flask serializa date/datetime como fecha HTTP
    ('Thu, 10 Sep 2026 12:10:08 GMT'). Esto los devuelve en ISO 8601
    ('2026-09-10' / '2026-09-10T12:10:08'), mucho más fácil de mostrar
    y de parsear en la app. Aplica a TODAS las rutas de una sola vez."""
    def default(self, o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        return super().default(o)

# Importar rutas
from app.routes.auth_routes import auth_bp
from app.routes.cliente_routes import cliente_bp
from app.routes.membresia_routes import membresia_bp
from app.routes.pago_routes import pago_bp
from app.routes.registro_routes import registro_bp
from app.routes.cuenta_routes import cuenta_bp

load_dotenv()

app = Flask(__name__)
app.json = ISODateJSONProvider(app)
CORS(app)

# Registrar Blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(cliente_bp, url_prefix='/api/clientes')
app.register_blueprint(membresia_bp, url_prefix='/api/membresias')
app.register_blueprint(pago_bp, url_prefix='/api/pagos')
app.register_blueprint(registro_bp, url_prefix='/api/registros')
app.register_blueprint(cuenta_bp, url_prefix='/api/cuentas')

@app.route('/')
def index():
    return {"message": "Zona Fit Evolution API is running"}

# Manejadores globales: aseguran que la API SIEMPRE responda JSON,
# incluso ante rutas inexistentes o métodos no soportados, para que
# la app cliente no reciba HTML y falle al parsear la respuesta.
@app.errorhandler(404)
def not_found(e):
    return jsonify({"message": "Recurso no encontrado"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"message": "Método no permitido"}), 405

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"message": "Error interno del servidor"}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5050))
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('1', 'true', 'yes')
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
