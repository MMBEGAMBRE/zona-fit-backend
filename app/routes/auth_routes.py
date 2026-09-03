from flask import Blueprint, request, jsonify
from app.models import get_db_connection, close_connection
import bcrypt
import jwt
import datetime
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('Email')
    password = data.get('PasswoRDkey')

    if not email or not password:
        return jsonify({"message": "Email y contraseña son requeridos"}), 400

    conn = get_db_connection()
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
            return jsonify({"message": "Credenciales inválidas"}), 401

    except Exception as e:
        return jsonify({"message": f"Error en el servidor: {str(e)}"}), 500
    finally:
        close_connection(conn, cursor)
