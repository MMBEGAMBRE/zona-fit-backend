from flask import request
from app.models import get_db_connection, close_connection


def registrar(usuario_id, accion, descripcion):
    """Escribe un evento en el historial de auditoría (tabla `registros`).

    Usa su propia conexión, separada de la transacción principal que
    disparó el evento, y NUNCA propaga una excepción hacia afuera: si el
    registro de auditoría falla por cualquier razón, se ignora en
    silencio para no tumbar la operación que ya se completó con éxito
    (o que ya fue bloqueada, en el caso de un acceso denegado).
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return
        cursor = conn.cursor()
        ip = request.remote_addr
        cursor.execute(
            "INSERT INTO registros (usuario_id, accion, descripcion, ip) VALUES (%s, %s, %s, %s)",
            (usuario_id, accion, descripcion, ip)
        )
        conn.commit()
    except Exception:
        pass
    finally:
        close_connection(conn, cursor)
