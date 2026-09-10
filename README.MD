# Zona Fit Evolution - API Backend

Backend de la aplicación móvil **Zona Fit Evolution** (gestión de un gimnasio: clientes, membresías, pagos y personal), construido con **Python** y **Flask**. Arquitectura modular con Blueprints, autenticación con **JWT** y control de acceso por rol en dos capas (interfaz + servidor).

## Guía de Instalación y Ejecución

### 1. Clonar el repositorio
```bash
git clone https://github.com/MMBEGAMBRE/zona-fit-backend.git
cd zona-fit-backend
```

### 2. Configurar el Entorno Virtual (venv)
```bash
# Crear el entorno
python -m venv venv

# Activar en Windows (PowerShell)
.\venv\Scripts\activate

# Activar en Windows (CMD)
.\venv\Scripts\activate.bat

# Activar en Mac/Linux
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno (.env)
El archivo `.env` **no se sube al repositorio** por seguridad. Créalo manualmente en la raíz del proyecto:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=zona_fit_evolution
JWT_SECRET=zonafitevolution_secret_key_2026
PORT=5050
FLASK_DEBUG=True
```

> `FLASK_DEBUG` solo debe estar en `True` en desarrollo local. En cualquier entorno expuesto a la red, déjalo en `False` o quítalo — con `True` se activa el debugger interactivo de Werkzeug, que permite ejecutar código arbitrario si algún endpoint falla.

### 5. Configurar la Base de Datos (MySQL)
1. Inicia tu servidor MySQL (XAMPP, Laragon, MySQL Installer, etc.).
2. Crea una base de datos llamada `zona_fit_evolution`.
3. Ejecuta el script `database/create-zonafit.sql` — crea las tablas e inserta el usuario administrador inicial.

### 6. Ejecutar el Servidor
```bash
python app.py
```
El servidor queda disponible en `http://localhost:5050`.

---

## Autenticación y Roles

La API usa **JWT** (JSON Web Token). Al iniciar sesión (`/api/auth/login`) se recibe un `token` que debe enviarse en cada petición protegida así:

```
Authorization: Bearer <token>
```

Hay dos roles, cada cuenta (`cuentas.rol`) tiene exactamente uno:

- **ADMINISTRADOR** — acceso completo a todo.
- **EMPLEADO** — solo Membresías y Pagos, y su propia cuenta (perfil / contraseña).

**Seguridad en dos capas:** la app oculta en la interfaz las opciones que un rol no puede usar, pero eso por sí solo no basta — cualquiera con la URL podría llamar al backend directamente saltándose la app. Por eso el servidor **vuelve a validar el rol en cada endpoint sensible**:
- Sin token → `401 Unauthorized`
- Con token pero rol insuficiente → `403 Forbidden`

Todo intento bloqueado (401 o 403) queda registrado automáticamente en el historial de auditoría (`/api/registros/`), junto con cada acción exitosa relevante (login, crear cliente, registrar pago, etc.).

### Usuarios de prueba

| Rol | Email | Contraseña |
|---|---|---|
| ADMINISTRADOR | `admin@zonafit.com` | `admin123` |
| EMPLEADO | `juan.empleado@zonafit.com` | `clave123` |

(El de administrador lo crea el script SQL inicial; el de empleado se crea desde la app con `POST /api/auth/register`, o repitiendo el mismo body contra ese endpoint.)

---

## Tabla de Endpoints

Todas las rutas cuelgan de la base `http://<host>:5050`. `¿Token?` = requiere `Authorization: Bearer`. `¿Rol?` = además del token, exige `ADMINISTRADOR`.

### Auth — `/api/auth`

| Método y ruta | ¿Token? | ¿Rol? | Body | Respuesta éxito | Errores |
|---|---|---|---|---|---|
| `POST /api/auth/login` | No | No | `{Email, PasswoRDkey}` | `200` `{message, token, user:{id,nombre,email,rol}}` | `400` faltan campos · `401` credenciales inválidas |
| `POST /api/auth/register` | Sí | **Admin** | `{nombre, email, password, rol}` (`rol`: `ADMINISTRADOR`\|`EMPLEADO`) | `201` `{message, id}` | `400` faltan campos / rol inválido · `401`/`403` sin permiso · `409` correo duplicado |

### Cuentas — `/api/cuentas` (propia cuenta, cualquier rol autenticado)

| Método y ruta | ¿Token? | ¿Rol? | Body | Respuesta éxito | Errores |
|---|---|---|---|---|---|
| `GET /api/cuentas/profile` | Sí | No | — | `200` `{message, user:{id,nombre,email,rol}}` | `401` · `404` |
| `PUT /api/cuentas/profile` | Sí | No | `{nombre, email}` | `200` `{message, user}` | `400` faltan campos · `401` · `409` correo duplicado |
| `PUT /api/cuentas/change-password` | Sí | No | `{current_password, new_password}` | `200` `{message}` | `400` faltan campos / actual incorrecta · `401` |

### Clientes — `/api/clientes` (solo Administrador)

| Método y ruta | ¿Token? | ¿Rol? | Body | Respuesta éxito | Errores |
|---|---|---|---|---|---|
| `GET /api/clientes/` | Sí | **Admin** | — | `200` `[{...cliente}]` | `401` / `403` |
| `GET /api/clientes/<id>` | Sí | **Admin** | — | `200` `{...cliente}` | `401` / `403` · `404` |
| `POST /api/clientes/` | Sí | **Admin** | `{nombre, apellido, documento, email, telefono, fecha_nacimiento}` | `201` `{message, id}` | `400` faltan campos · `401` / `403` |
| `POST /api/clientes/con-membresia` | Sí | **Admin** | `{nombre, apellido, documento, email, telefono, fecha_nacimiento, tipo, fecha_inicio?, metodo_pago, monto}` — crea cliente + membresía + pago **en una sola transacción** (todo o nada); `fecha_vencimiento` se calcula sola según `tipo` (Mensual=+1 mes, Trimestral=+3, Anual=+12); si no se envía `fecha_inicio` se usa hoy | `201` `{message, cliente, membresia, pago}` | `400` campos faltantes / tipo o método de pago inválido / monto ≤ 0 · `401` / `403` |
| `PUT /api/clientes/<id>` | Sí | **Admin** | `{nombre, apellido, documento, email, telefono, fecha_nacimiento, estado}` | `200` `{message}` | `400` · `401` / `403` |

### Membresías — `/api/membresias` (cualquier rol autenticado)

| Método y ruta | ¿Token? | ¿Rol? | Body | Respuesta éxito | Errores |
|---|---|---|---|---|---|
| `GET /api/membresias/` | Sí | No | — | `200` `[{...membresía, cliente_nombre, cliente_apellido}]` | `401` |
| `GET /api/membresias/<id>` | Sí | No | — | `200` `{...membresía}` | `401` · `404` |
| `POST /api/membresias/` | Sí | No | `{cliente_id, tipo, fecha_inicio, fecha_vencimiento}` | `201` `{message, id}` | `401` |
| `PUT /api/membresias/<id>` | Sí | No | `{estado}` (`ACTIVA`\|`VENCIDA`\|`CANCELADA`) | `200` `{message}` | `401` |

### Pagos — `/api/pagos` (cualquier rol autenticado)

| Método y ruta | ¿Token? | ¿Rol? | Body | Respuesta éxito | Errores |
|---|---|---|---|---|---|
| `GET /api/pagos/` | Sí | No | — | `200` `[{...pago, nombre, apellido, membresia_tipo}]` | `401` |
| `POST /api/pagos/` | Sí | No | `{cliente_id, membresia_id, monto, metodo_pago}` | `201` `{message, id}` | `400` método inválido / monto ≤ 0 · `401` |

### Registros de auditoría — `/api/registros` (ver = solo Admin; crear = cualquier rol)

| Método y ruta | ¿Token? | ¿Rol? | Body | Respuesta éxito | Errores |
|---|---|---|---|---|---|
| `GET /api/registros/` | Sí | **Admin** | — | `200` `[{id, fecha_hora, usuario_id, usuario_nombre, usuario_rol, accion, descripcion, ip}]` | `401` / `403` |
| `POST /api/registros/` | Sí | No | `{usuario_id, accion, descripcion}` (uso manual; el sistema ya registra automáticamente los eventos importantes) | `201` `{message}` | `401` |

---

## Sistema de auditoría (`registros`)

El backend escribe automáticamente en `registros` cada vez que ocurre uno de estos eventos (sin que la app tenga que llamarlo aparte):

| Acción (`accion`) | Cuándo se genera |
|---|---|
| `LOGIN` / `LOGIN_FALLIDO` | Al iniciar sesión, exitoso o no |
| `ACCESO_DENEGADO` | Sin token, token inválido/vencido, o rol insuficiente (401/403) |
| `EMPLEADO_CREADO` | Al registrar una cuenta nueva (`/api/auth/register`) |
| `PERFIL_ACTUALIZADO` / `CONTRASEÑA_CAMBIADA` | Al editar el perfil propio o cambiar la contraseña |
| `CLIENTE_CREADO` / `CLIENTE_EDITADO` | Al crear o editar un cliente |
| `MEMBRESIA_CREADA` / `MEMBRESIA_ACTUALIZADA` | Al crear una membresía o cambiar su estado |
| `PAGO_REGISTRADO` | Al registrar un pago |

Cada entrada guarda quién lo hizo (`usuario_id`, con nombre y rol vía `JOIN`), qué pasó (`accion` + `descripcion` en texto legible), cuándo (`fecha_hora`, en ISO 8601) y desde qué IP.

---

## Formato de fechas

Todas las fechas y horas que devuelve la API vienen en **ISO 8601** (`YYYY-MM-DD` para fechas, `YYYY-MM-DDTHH:MM:SS` para fecha+hora) — configurado globalmente en `app.py` (`ISODateJSONProvider`), no hay que parsear formato HTTP en ningún endpoint.

---

## Estructura del Proyecto
```
app/
  routes/         # Blueprints: auth, cliente, cuenta, membresia, pago, registro
  utils/
    decorators.py # @token_required, @admin_required
    auditoria.py  # registrar(): escribe en la tabla `registros`
  models.py       # Conexión a MySQL
database/
  create-zonafit.sql  # Esquema + usuario admin inicial
app.py            # Punto de entrada, blueprints, manejo global de errores y fechas
requirements.txt  # Dependencias
```

---

## Notas adicionales
- **Acceso desde Emulador Android**: usa `http://10.0.2.2:5050`.
- **Acceso desde Celular Físico**: mismo Wi-Fi que el PC, usa la IP de tu PC (ej. `http://192.168.1.65:5050`) y agrégala a `network_security_config.xml` del lado de Android si usas HTTP sin TLS.
- El token nunca viaja en la URL ni queda escrito en el código — siempre por el encabezado `Authorization`.
- Todas las rutas devuelven **JSON siempre**, incluso ante errores 404/405/500 (manejadores globales en `app.py`), para que la app cliente nunca reciba HTML y falle al parsear la respuesta.
