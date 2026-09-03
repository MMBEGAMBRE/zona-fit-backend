from flask import Blueprint, request, jsonify
from app.models import get_db_connection, close_connection

cliente_bp = Blueprint('cliente', __name__)

@cliente_bp.route('/', methods=['GET'])
def get_clientes():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM clientes")
        clientes = cursor.fetchall()
        return jsonify(clientes), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        close_connection(conn, cursor)

@cliente_bp.route('/<int:id>', methods=['GET'])
def get_cliente(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM clientes WHERE id = %s", (id,))
        cliente = cursor.fetchone()
        if cliente:
            return jsonify(cliente), 200
        return jsonify({"message": "Cliente no encontrado"}), 404
    finally:
        close_connection(conn, cursor)

@cliente_bp.route('/', methods=['POST'])
def create_cliente():
    data = request.get_json()
    nombre = data.get('nombre')
    apellido = data.get('apellido')
    documento = data.get('documento')
    email = data.get('email')
    telefono = data.get('telefono')
    fecha_nacimiento = data.get('fecha_nacimiento')

    if not nombre or not apellido or not documento:
        return jsonify({"message": "Nombre, apellido y documento son requeridos"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO clientes (nombre, apellido, documento, email, telefono, fecha_nacimiento)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (nombre, apellido, documento, email, telefono, fecha_nacimiento))
        conn.commit()
        return jsonify({"message": "Cliente creado exitosamente", "id": cursor.lastrowid}), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        close_connection(conn, cursor)

@cliente_bp.route('/<int:id>', methods=['PUT'])
def update_cliente(id):
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE clientes
            SET nombre=%s, apellido=%s, documento=%s, email=%s, telefono=%s, fecha_nacimiento=%s, estado=%s
            WHERE id=%s
        """, (data['nombre'], data['apellido'], data['documento'], data['email'],
              data['telefono'], data['fecha_nacimiento'], data['estado'], id))
        conn.commit()
        return jsonify({"message": "Cliente actualizado"}), 200
    finally:
        close_connection(conn, cursor)
