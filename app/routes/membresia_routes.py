from flask import Blueprint, request, jsonify, g
from app.models import get_db_connection, close_connection
from app.utils.decorators import token_required
from app.utils.auditoria import registrar
from datetime import datetime, date
import calendar

membresia_bp = Blueprint('membresia', __name__)

DURACION_PLANES_MESES = {
    'Mensual': 1,
    'Trimestral': 3,
    'Anual': 12
}

def _sumar_meses(fecha, meses):
    mes_total = fecha.month - 1 + meses
    año = fecha.year + mes_total // 12
    mes = mes_total % 12 + 1
    dia = min(fecha.day, calendar.monthrange(año, mes)[1])
    return date(año, mes, dia)

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

@membresia_bp.route('/renovar', methods=['POST'])
@token_required
def renovar_membresia():
    data = request.get_json()
    membresia_id = data.get('membresia_id')
    monto = data.get('monto')
    metodo_pago = data.get('metodo_pago')

    if not membresia_id or not monto or not metodo_pago:
        return jsonify({"message": "ID de membresía, monto y método son requeridos"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Error de conexión a la base de datos"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Obtener datos actuales de la membresía
        cursor.execute("SELECT * FROM membresias WHERE id = %s", (membresia_id,))
        m = cursor.fetchone()
        if not m:
            return jsonify({"message": "Membresía no encontrada"}), 404

        # 2. Calcular nuevas fechas
        # Si la membresía está vencida, empezamos desde HOY.
        # Si aún no vence, sumamos al vencimiento actual.
        hoy = date.today()
        vencimiento_actual = m['fecha_vencimiento']
        if isinstance(vencimiento_actual, str):
             vencimiento_actual = datetime.strptime(vencimiento_actual, "%Y-%m-%d").date()

        base_fecha = hoy if vencimiento_actual < hoy else vencimiento_actual
        nueva_fecha_fin = _sumar_meses(base_fecha, DURACION_PLANES_MESES.get(m['tipo'], 1))

        # 3. Registrar el Pago
        cursor.execute("""
            INSERT INTO pagos (cliente_id, membresia_id, monto, metodo_pago)
            VALUES (%s, %s, %s, %s)
        """, (m['cliente_id'], membresia_id, monto, metodo_pago))

        # 4. Actualizar la Membresía
        cursor.execute("""
            UPDATE membresias
            SET fecha_inicio = %s, fecha_vencimiento = %s, estado = 'ACTIVA'
            WHERE id = %s
        """, (base_fecha, nueva_fecha_fin, membresia_id))

        conn.commit()
        registrar(g.user_id, 'RENOVACION', f"Renovó membresía {membresia_id} hasta {nueva_fecha_fin}")

        return jsonify({
            "message": "Membresía renovada con éxito",
            "nueva_fecha": nueva_fecha_fin.isoformat()
        }), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"message": str(e)}), 500
    finally:
        close_connection(conn, cursor)

@membresia_bp.route('/con-pago', methods=['POST'])
@token_required
def create_membresia_con_pago():
    data = request.get_json()
    cliente_id = data.get('cliente_id')
    tipo = data.get('tipo')
    fecha_inicio = data.get('fecha_inicio')
    fecha_vencimiento = data.get('fecha_vencimiento')
    monto = data.get('monto')
    metodo_pago = data.get('metodo_pago')

    if not cliente_id or not monto or not metodo_pago:
        return jsonify({"message": "Datos incompletos"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Error de conexión a la base de datos"}), 500
    cursor = conn.cursor()
    try:
        # 1. Crear membresía
        cursor.execute("""
            INSERT INTO membresias (cliente_id, tipo, fecha_inicio, fecha_vencimiento, estado)
            VALUES (%s, %s, %s, %s, 'ACTIVA')
        """, (cliente_id, tipo, fecha_inicio, fecha_vencimiento))
        membresia_id = cursor.lastrowid

        # 2. Crear pago
        cursor.execute("""
            INSERT INTO pagos (cliente_id, membresia_id, monto, metodo_pago)
            VALUES (%s, %s, %s, %s)
        """, (cliente_id, membresia_id, monto, metodo_pago))

        conn.commit()
        registrar(g.user_id, 'MEMBRESIA_CON_PAGO', f"Creó membresía {tipo} para cliente {cliente_id} con pago de {monto}")
        return jsonify({"message": "Membresía y pago registrados con éxito"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"message": str(e)}), 500
    finally:
        close_connection(conn, cursor)
