from functools import wraps
from flask import request, jsonify, g
from app.utils.auditoria import registrar
import jwt
import os


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0] == 'Bearer':
                token = parts[1]

        if not token:
            registrar(None, 'ACCESO_DENEGADO', f"Intento sin token a {request.path}")
            return jsonify({"message": "Token no proporcionado"}), 401

        try:
            payload = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=["HS256"])
            g.user_id = payload['id']
            g.user_rol = payload.get('rol')
        except jwt.ExpiredSignatureError:
            registrar(None, 'ACCESO_DENEGADO', f"Token expirado en intento a {request.path}")
            return jsonify({"message": "El token ha expirado"}), 401
        except jwt.InvalidTokenError:
            registrar(None, 'ACCESO_DENEGADO', f"Token inválido en intento a {request.path}")
            return jsonify({"message": "Token inválido"}), 401

        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Va DESPUÉS de @token_required en la pila de decoradores, para que
    g.user_rol ya exista cuando se evalúa. Bloquea con 403 a cualquiera
    que no sea ADMINISTRADOR."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if getattr(g, 'user_rol', None) != 'ADMINISTRADOR':
            registrar(getattr(g, 'user_id', None), 'ACCESO_DENEGADO',
                      f"Intentó acceder a {request.path} sin permisos de administrador")
            return jsonify({"message": "Requiere permisos de administrador"}), 403
        return f(*args, **kwargs)
    return decorated
