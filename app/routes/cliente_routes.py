from flask import Blueprint, request, jsonify, g
from app.models import get_db_connection, close_connection
from app.utils.decorators import token_required, admin_required
from app.utils.auditoria import registrar
from datetime import date, datetime
import calendar

cliente_bp = Blueprint('cliente', __name__)

# Duración de cada plan, en meses (regla de negocio centralizada aquí:
# si cambia la duración de un plan, solo se toca este diccionario)
DURACION_PLANES_MESES = {
    'Mensual': 1,
    'Trimestral': 3,
    'Anual': 12
}

METODOS_PAGO_VALIDOS = ('Efectivo', 'Transferencia', 'Tarjeta')

def _sumar_meses(fecha, meses):
    """Suma 'meses' calendario a 'fecha', ajustando el día si el mes
    resultante tiene menos días (ej. 31 ene + 1 mes -> 28/29 feb)."""
    mes_total = fecha.month - 1 + meses
    año = fecha.year + mes_total // 12
    mes = mes_total % 12 + 1
    dia = min(fecha.day, calendar.monthrange(año, mes)[1])
    return date(año, mes, dia)

@cliente_bp.route('/', methods=['GET'])
@token_required
def get_clientes():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Error de conexión a la base de datos"}), 500
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
@token_required
def get_cliente(id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Error de conexión a la base de datos"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM clientes WHERE id = %s", (id,))
        cliente = cursor.fetchone()
        if cliente:
            return jsonify(cliente), 200
        return jsonify({"message": "Cliente no encontrado"}), 404
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        close_connection(conn, cursor)

@cliente_bp.route('/', methods=['POST'])
@token_required
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
    if conn is None:
        return jsonify({"message": "Error de conexión a la base de datos"}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO clientes (nombre, apellido, documento, email, telefono, fecha_nacimiento)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (nombre, apellido, documento, email, telefono, fecha_nacimiento))
        conn.commit()
        registrar(g.user_id, 'CLIENTE_CREADO', f"Creó el cliente {nombre} {apellido}")
        return jsonify({"message": "Cliente creado exitosamente", "id": cursor.lastrowid}), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        close_connection(conn, cursor)

@cliente_bp.route('/con-membresia', methods=['POST'])
@token_required
def create_cliente_con_membresia():
    data = request.get_json()
    nombre = data.get('nombre')
    apellido = data.get('apellido')
    documento = data.get('documento')
    email = data.get('email')
    telefono = data.get('telefono')
    fecha_nacimiento = data.get('fecha_nacimiento')
    tipo = data.get('tipo')
    fecha_inicio_str = data.get('fecha_inicio')
    metodo_pago = data.get('metodo_pago')
    monto = data.get('monto')

    if not nombre or not apellido or not documento:
        return jsonify({"message": "Nombre, apellido y documento son requeridos"}), 400

    if tipo not in DURACION_PLANES_MESES:
        return jsonify({"message": "Tipo de plan inválido. Usa Mensual, Trimestral o Anual"}), 400

    if metodo_pago not in METODOS_PAGO_VALIDOS:
        return jsonify({"message": "Método de pago inválido. Usa Efectivo, Transferencia o Tarjeta"}), 400

    try:
        monto = float(monto)
        if monto <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({"message": "El monto del pago es obligatorio y debe ser mayor a 0"}), 400

    # Si no envían fecha de inicio, se asume "hoy"
    if fecha_inicio_str:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"message": "fecha_inicio debe tener formato YYYY-MM-DD"}), 400
    else:
        fecha_inicio = date.today()

    fecha_vencimiento = _sumar_meses(fecha_inicio, DURACION_PLANES_MESES[tipo])

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Error de conexión a la base de datos"}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO clientes (nombre, apellido, documento, email, telefono, fecha_nacimiento)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (nombre, apellido, documento, email, telefono, fecha_nacimiento))
        cliente_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO membresias (cliente_id, tipo, fecha_inicio, fecha_vencimiento, estado)
            VALUES (%s, %s, %s, %s, 'ACTIVA')
        """, (cliente_id, tipo, fecha_inicio, fecha_vencimiento))
        membresia_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO pagos (cliente_id, membresia_id, monto, metodo_pago)
            VALUES (%s, %s, %s, %s)
        """, (cliente_id, membresia_id, monto, metodo_pago))
        pago_id = cursor.lastrowid

        conn.commit()

        registrar(
            g.user_id, 'CLIENTE_CREADO',
            f"Creó el cliente {nombre} {apellido} con membresía {tipo} "
            f"(vence {fecha_vencimiento.isoformat()}) y pago de {monto} ({metodo_pago})"
        )

        return jsonify({
            "message": "Cliente, membresía y pago registrados",
            "cliente": {
                "id": cliente_id,
                "nombre": nombre,
                "apellido": apellido,
                "documento": documento,
                "email": email,
                "telefono": telefono,
                "fecha_nacimiento": fecha_nacimiento,
                "estado": "ACTIVO"
            },
            "membresia": {
                "id": membresia_id,
                "cliente_id": cliente_id,
                "tipo": tipo,
                "fecha_inicio": fecha_inicio.isoformat(),
                "fecha_vencimiento": fecha_vencimiento.isoformat(),
                "estado": "ACTIVA",
                "cliente_nombre": nombre,
                "cliente_apellido": apellido
            },
            "pago": {
                "id": pago_id,
                "cliente_id": cliente_id,
                "membresia_id": membresia_id,
                "monto": monto,
                "metodo_pago": metodo_pago,
                "fecha_pago": datetime.now().isoformat(),
                "nombre": nombre,
                "apellido": apellido,
                "membresia_tipo": tipo
            }
        }), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"message": str(e)}), 500
    finally:
        close_connection(conn, cursor)

@cliente_bp.route('/<int:id>', methods=['PUT'])
@token_required
def update_cliente(id):
    data = request.get_json()
    nombre = data.get('nombre')
    apellido = data.get('apellido')
    documento = data.get('documento')
    email = data.get('email')
    telefono = data.get('telefono')
    fecha_nacimiento = data.get('fecha_nacimiento')
    estado = data.get('estado')

    if not nombre or not apellido or not documento:
        return jsonify({"message": "Nombre, apellido y documento son requeridos"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Error de conexión a la base de datos"}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE clientes
            SET nombre=%s, apellido=%s, documento=%s, email=%s, telefono=%s, fecha_nacimiento=%s, estado=%s
            WHERE id=%s
        """, (nombre, apellido, documento, email, telefono, fecha_nacimiento, estado, id))
        conn.commit()
        registrar(g.user_id, 'CLIENTE_EDITADO', f"Editó el cliente {nombre} {apellido} (id {id})")
        return jsonify({"message": "Cliente actualizado"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        close_connection(conn, cursor)

@cliente_bp.route('/<int:id>', methods=['DELETE'])
@token_required
@admin_required
def delete_cliente(id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Error de conexión a la base de datos"}), 500
    cursor = conn.cursor()
    try:
        # Primero verificamos si el cliente existe para la auditoría
        cursor.execute("SELECT nombre, apellido FROM clientes WHERE id = %s", (id,))
        cliente = cursor.fetchone()
        if not cliente:
            return jsonify({"message": "Cliente no encontrado"}), 404

        # Eliminamos el cliente (la DB debería manejar el ON DELETE CASCADE si está configurado,
        # si no, habría que borrar membresías y pagos primero. Asumimos integridad referencial).
        cursor.execute("DELETE FROM clientes WHERE id = %s", (id,))
        conn.commit()
        registrar(g.user_id, 'CLIENTE_ELIMINADO', f"Eliminó al cliente {cliente[0]} {cliente[1]} (id {id})")
        return jsonify({"message": "Cliente eliminado exitosamente"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"message": str(e)}), 500
    finally:
        close_connection(conn, cursor)

@cliente_bp.route('/buscar/<string:documento>', methods=['GET'])
@token_required
def buscar_cliente_por_documento(documento):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Error de conexión a la base de datos"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        # Buscamos al cliente y el estado de su membresía más reciente
        cursor.execute("""
            SELECT c.*, m.estado as membresia_estado, m.fecha_vencimiento, m.id as membresia_id
            FROM clientes c
            LEFT JOIN membresias m ON c.id = m.cliente_id
            WHERE c.documento = %s
            ORDER BY m.id DESC LIMIT 1
        """, (documento,))
        cliente = cursor.fetchone()
        if cliente:
            return jsonify(cliente), 200
        return jsonify({"message": "Socio no encontrado"}), 404
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        close_connection(conn, cursor)
