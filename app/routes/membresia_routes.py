from flask import Blueprint, request, jsonify
from app.models import get_db_connection, close_connection
from datetime import datetime

membresia_bp = Blueprint('membresia', __name__)

@membresia_bp.route('/', methods=['GET'])
def get_membresias():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT m.*, c.nombre as cliente_nombre, c.apellido as cliente_apellido
            FROM membresias m
            JOIN clientes c ON m.cliente_id = c.id
        """)
        membresias = cursor.fetchall()
        return jsonify(membresias), 200
    finally:
        close_connection(conn, cursor)

@membresia_bp.route('/', methods=['POST'])
def create_membresia():
    data = request.get_json()
    cliente_id = data.get('cliente_id')
    tipo = data.get('tipo')
    fecha_inicio = data.get('fecha_inicio')
    fecha_vencimiento = data.get('fecha_vencimiento')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO membresias (cliente_id, tipo, fecha_inicio, fecha_vencimiento, estado)
            VALUES (%s, %s, %s, %s, 'ACTIVA')
        """, (cliente_id, tipo, fecha_inicio, fecha_vencimiento))
        conn.commit()
        return jsonify({"message": "Membresía creada", "id": cursor.lastrowid}), 201
    finally:
        close_connection(conn, cursor)

@membresia_bp.route('/<int:id>', methods=['PUT'])
def update_membresia(id):
    data = request.get_json()
    estado = data.get('estado')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE membresias SET estado=%s WHERE id=%s", (estado, id))
        conn.commit()
        return jsonify({"message": "Estado de membresía actualizado"}), 200
    finally:
        close_connection(conn, cursor)
