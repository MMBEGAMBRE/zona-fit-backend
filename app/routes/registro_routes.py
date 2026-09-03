from flask import Blueprint, request, jsonify
from app.models import get_db_connection, close_connection

registro_bp = Blueprint('registro', __name__)

@registro_bp.route('/', methods=['GET'])
def get_registros():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Se asume que solo el ADMIN entra aquí (la validación de rol se haría con un decorador JWT)
        cursor.execute("""
            SELECT r.*, c.nombre as usuario_nombre, c.rol as usuario_rol
            FROM registros r
            LEFT JOIN cuentas c ON r.usuario_id = c.id
            ORDER BY r.fecha_hora DESC
        """)
        registros = cursor.fetchall()
        return jsonify(registros), 200
    finally:
        close_connection(conn, cursor)

@registro_bp.route('/', methods=['POST'])
def create_registro():
    data = request.get_json()
    usuario_id = data.get('usuario_id')
    accion = data.get('accion')
    descripcion = data.get('descripcion')
    ip = request.remote_addr

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO registros (usuario_id, accion, descripcion, ip)
            VALUES (%s, %s, %s, %s)
        """, (usuario_id, accion, descripcion, ip))
        conn.commit()
        return jsonify({"message": "Registro de auditoría creado"}), 201
    finally:
        close_connection(conn, cursor)
