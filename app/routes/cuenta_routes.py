from flask import Blueprint, request, jsonify, g
from app.models import get_db_connection, close_connection
from app.utils.decorators import token_required   # usa tu propio decorador si ya lo tienes
from app.utils.auditoria import registrar
import bcrypt

cuenta_bp = Blueprint('cuenta', __name__)

# Leer el perfil del usuario autenticado (usa el id que dejó el decorador en g.user_id)
@cuenta_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, nombre, email, rol FROM cuentas WHERE id = %s",
            (g.user_id,)
        )
        user = cursor.fetchone()
        if not user:
            return jsonify({"message": "Usuario no encontrado"}), 404
        return jsonify({"message": "OK", "user": user}), 200
    finally:
        close_connection(conn, cursor)

# Actualizar nombre y correo del usuario autenticado
@cuenta_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile():
    data = request.get_json()
    nombre = data.get('nombre')
    email = data.get('email')

    if not nombre or not email:
        return jsonify({"message": "Nombre y correo son requeridos"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "UPDATE cuentas SET nombre=%s, email=%s WHERE id=%s",
            (nombre, email, g.user_id)
        )
        conn.commit()
        cursor.execute(
            "SELECT id, nombre, email, rol FROM cuentas WHERE id = %s",
            (g.user_id,)
        )
        user = cursor.fetchone()
        registrar(g.user_id, 'PERFIL_ACTUALIZADO', f"Actualizó su perfil (nombre: {nombre}, correo: {email})")
        return jsonify({"message": "Perfil actualizado", "user": user}), 200
    except Exception as e:
        # Email duplicado -> UNIQUE constraint
        return jsonify({"message": str(e)}), 409
    finally:
        close_connection(conn, cursor)

# Cambiar la contraseña del usuario autenticado
@cuenta_bp.route('/change-password', methods=['PUT'])
@token_required
def change_password():
    data = request.get_json()
    actual = data.get('current_password')
    nueva = data.get('new_password')

    if not actual or not nueva:
        return jsonify({"message": "Completa los dos campos"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT password FROM cuentas WHERE id = %s", (g.user_id,))
        row = cursor.fetchone()

        if not row or not bcrypt.checkpw(actual.encode('utf-8'), row['password'].encode('utf-8')):
            return jsonify({"message": "La contraseña actual es incorrecta"}), 400

        nuevo_hash = bcrypt.hashpw(nueva.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("UPDATE cuentas SET password=%s WHERE id=%s", (nuevo_hash, g.user_id))
        conn.commit()
        registrar(g.user_id, 'CONTRASEÑA_CAMBIADA', "Cambió su contraseña")
        return jsonify({"message": "Contraseña actualizada"}), 200
    finally:
        close_connection(conn, cursor)
