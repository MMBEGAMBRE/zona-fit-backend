from flask import Blueprint, request, jsonify, g
from app.models import get_db_connection, close_connection
from app.utils.decorators import token_required
from app.utils.auditoria import registrar

pago_bp = Blueprint('pago', __name__)

METODOS_PAGO_VALIDOS = ('Efectivo', 'Transferencia', 'Tarjeta')

@pago_bp.route('/', methods=['GET'])
@token_required
def get_pagos():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Error de conexión a la base de datos"}), 500
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
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        close_connection(conn, cursor)

@pago_bp.route('/', methods=['POST'])
@token_required
def create_pago():
    data = request.get_json()
    cliente_id = data.get('cliente_id')
    membresia_id = data.get('membresia_id')
    monto = data.get('monto')
    metodo_pago = data.get('metodo_pago')

    if not cliente_id or not membresia_id:
        return jsonify({"message": "Faltan datos obligatorios"}), 400

    if metodo_pago not in METODOS_PAGO_VALIDOS:
        return jsonify({"message": "Método de pago inválido. Usa Efectivo, Transferencia o Tarjeta"}), 400

    try:
        monto = float(monto)
        if monto <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({"message": "El monto es obligatorio y debe ser mayor a 0"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Error de conexión a la base de datos"}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO pagos (cliente_id, membresia_id, monto, metodo_pago)
            VALUES (%s, %s, %s, %s)
        """, (cliente_id, membresia_id, monto, metodo_pago))
        conn.commit()
        registrar(g.user_id, 'PAGO_REGISTRADO', f"Registró un pago de {monto} ({metodo_pago}) para el cliente {cliente_id}")
        return jsonify({"message": "Pago registrado exitosamente", "id": cursor.lastrowid}), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        close_connection(conn, cursor)
