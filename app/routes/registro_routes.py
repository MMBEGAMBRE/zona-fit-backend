from flask import Blueprint, request, jsonify
from app.models import get_db_connection, close_connection
from app.utils.decorators import token_required, admin_required

registro_bp = Blueprint('registro', __name__)

@registro_bp.route('/', methods=['GET'])
@token_required
@admin_required
def get_registros():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Error de conexión a la base de datos"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT r.*, c.nombre as usuario_nombre, c.rol as usuario_rol
            FROM registros r
            LEFT JOIN cuentas c ON r.usuario_id = c.id
            ORDER BY r.fecha_hora DESC
        """)
        registros = cursor.fetchall()
        return jsonify(registros), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        close_connection(conn, cursor)

@registro_bp.route('/', methods=['POST'])
@token_required
def create_registro():
    # Cualquier usuario autenticado (admin o empleado) puede generar un registro
    # de auditoría sobre su propia acción; ver el historial completo sí es solo admin.
    data = request.get_json()
    usuario_id = data.get('usuario_id')
    accion = data.get('accion')
    descripcion = data.get('descripcion')
    ip = request.remote_addr

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Error de conexión a la base de datos"}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO registros (usuario_id, accion, descripcion, ip)
            VALUES (%s, %s, %s, %s)
        """, (usuario_id, accion, descripcion, ip))
        conn.commit()
        return jsonify({"message": "Registro de auditoría creado"}), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        close_connection(conn, cursor)
