from flask import Blueprint, request, jsonify
from app.models import get_db_connection, close_connection

pago_bp = Blueprint('pago', __name__)

@pago_bp.route('/', methods=['GET'])
def get_pagos():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT p.*, c.nombre, c.apellido, m.tipo as membresia_tipo
            FROM pagos p
            JOIN clientes c ON p.cliente_id = c.id
            JOIN membresias m ON p.membresia_id = m.id
        """)
        pagos = cursor.fetchall()
        return jsonify(pagos), 200
    finally:
        close_connection(conn, cursor)

@pago_bp.route('/', methods=['POST'])
def create_pago():
    data = request.get_json()
    cliente_id = data.get('cliente_id')
    membresia_id = data.get('membresia_id')
    monto = data.get('monto')
    metodo_pago = data.get('metodo_pago')

    if not cliente_id or not membresia_id or not monto or not metodo_pago:
        return jsonify({"message": "Faltan datos obligatorios"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO pagos (cliente_id, membresia_id, monto, metodo_pago)
            VALUES (%s, %s, %s, %s)
        """, (cliente_id, membresia_id, monto, metodo_pago))
        conn.commit()
        return jsonify({"message": "Pago registrado exitosamente", "id": cursor.lastrowid}), 201
    finally:
        close_connection(conn, cursor)
