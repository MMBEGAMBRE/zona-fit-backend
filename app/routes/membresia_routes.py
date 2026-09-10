from flask import Blueprint, request, jsonify, g
from app.models import get_db_connection, close_connection
from app.utils.decorators import token_required
from app.utils.auditoria import registrar
from datetime import datetime

membresia_bp = Blueprint('membresia', __name__)

@membresia_bp.route('/', methods=['GET'])
@token_required
def get_membresias():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Error de conexión a la base de datos"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT m.*, c.nombre as cliente_nombre, c.apellido as cliente_apellido
            FROM membresias m
            JOIN clientes c ON m.cliente_id = c.id
        """)
        membresias = cursor.fetchall()
        return jsonify(membresias), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        close_connection(conn, cursor)

@membresia_bp.route('/<int:id>', methods=['GET'])
@token_required
def get_membresia(id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Error de conexión a la base de datos"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT m.*, c.nombre as cliente_nombre, c.apellido as cliente_apellido
            FROM membresias m
            JOIN clientes c ON m.cliente_id = c.id
            WHERE m.id = %s
        """, (id,))
        membresia = cursor.fetchone()
        if membresia:
            return jsonify(membresia), 200
        return jsonify({"message": "Membresía no encontrada"}), 404
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        close_connection(conn, cursor)

@membresia_bp.route('/', methods=['POST'])
@token_required
def create_membresia():
    data = request.get_json()
    cliente_id = data.get('cliente_id')
    tipo = data.get('tipo')
    fecha_inicio = data.get('fecha_inicio')
    fecha_vencimiento = data.get('fecha_vencimiento')

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Error de conexión a la base de datos"}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO membresias (cliente_id, tipo, fecha_inicio, fecha_vencimiento, estado)
            VALUES (%s, %s, %s, %s, 'ACTIVA')
        """, (cliente_id, tipo, fecha_inicio, fecha_vencimiento))
        conn.commit()
        registrar(g.user_id, 'MEMBRESIA_CREADA', f"Creó una membresía {tipo} para el cliente {cliente_id}")
        return jsonify({"message": "Membresía creada", "id": cursor.lastrowid}), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        close_connection(conn, cursor)

@membresia_bp.route('/<int:id>', methods=['PUT'])
@token_required
def update_membresia(id):
    data = request.get_json()
    estado = data.get('estado')
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Error de conexión a la base de datos"}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE membresias SET estado=%s WHERE id=%s", (estado, id))
        conn.commit()
        registrar(g.user_id, 'MEMBRESIA_ACTUALIZADA', f"Cambió el estado de la membresía {id} a {estado}")
        return jsonify({"message": "Estado de membresía actualizado"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        close_connection(conn, cursor)
