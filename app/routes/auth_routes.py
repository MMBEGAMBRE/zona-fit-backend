from flask import Blueprint, request, jsonify, g
from app.models import get_db_connection, close_connection
from app.utils.decorators import token_required, admin_required
from app.utils.auditoria import registrar
import bcrypt
import jwt
import datetime
import os

auth_bp = Blueprint('auth', __name__)

ROLES_VALIDOS = ('ADMINISTRADOR', 'EMPLEADO')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('Email')
    password = data.get('PasswoRDkey')

    if not email or not password:
        return jsonify({"message": "Email y contraseña son requeridos"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Error de conexión a la base de datos"}), 500
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM cuentas WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            token = jwt.encode({
                'id': user['id'],
                'rol': user['rol'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, os.getenv('JWT_SECRET'), algorithm="HS256")

            registrar(user['id'], 'LOGIN', f"{user['nombre']} inició sesión")

            return jsonify({
                "message": "Login exitoso",
                "token": token,
                "user": {
                    "id": user['id'],
                    "nombre": user['nombre'],
                    "email": user['email'],
                    "rol": user['rol']
                }
            }), 200
        else:
            registrar(None, 'LOGIN_FALLIDO', f"Intento fallido con el correo {email}")
            return jsonify({"message": "Credenciales inválidas"}), 401

    except Exception as e:
        return jsonify({"message": f"Error en el servidor: {str(e)}"}), 500
    finally:
        close_connection(conn, cursor)

# Registrar personal nuevo (empleado o administrador) con su propia cuenta.
# Solo un ADMINISTRADOR autenticado puede crear cuentas nuevas.
@auth_bp.route('/register', methods=['POST'])
@token_required
@admin_required
def register_staff():
    data = request.get_json()
    nombre = data.get('nombre')
    email = data.get('email')
    password = data.get('password')
    rol = data.get('rol')

    if not nombre or not email or not password:
        return jsonify({"message": "Nombre, correo y contraseña son requeridos"}), 400

    if rol not in ROLES_VALIDOS:
        return jsonify({"message": "Rol inválido. Usa ADMINISTRADOR o EMPLEADO"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Error de conexión a la base de datos"}), 500
    cursor = conn.cursor()
    try:
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("""
            INSERT INTO cuentas (nombre, email, password, rol)
            VALUES (%s, %s, %s, %s)
        """, (nombre, email, password_hash, rol))
        conn.commit()
        registrar(g.user_id, 'EMPLEADO_CREADO', f"Creó la cuenta de {nombre} ({email}) con rol {rol}")
        return jsonify({
            "message": "Empleado registrado exitosamente",
            "id": cursor.lastrowid
        }), 201
    except Exception as e:
        conn.rollback()
        if "Duplicate entry" in str(e):
            return jsonify({"message": "Ese correo ya está registrado"}), 409
        return jsonify({"message": str(e)}), 500
    finally:
        close_connection(conn, cursor)

@auth_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def get_users():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Error de conexión a la base de datos"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, nombre, email, rol FROM cuentas")
        users = cursor.fetchall()
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        close_connection(conn, cursor)

@auth_bp.route('/users/<int:id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(id):
    if g.user_id == id:
        return jsonify({"message": "No puedes eliminar tu propia cuenta"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Error de conexión a la base de datos"}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT nombre FROM cuentas WHERE id = %s", (id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"message": "Usuario no encontrado"}), 404

        cursor.execute("DELETE FROM cuentas WHERE id = %s", (id,))
        conn.commit()
        registrar(g.user_id, 'USUARIO_ELIMINADO', f"Eliminó la cuenta de {user[0]} (id {id})")
        return jsonify({"message": "Usuario eliminado"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"message": str(e)}), 500
    finally:
        close_connection(conn, cursor)
