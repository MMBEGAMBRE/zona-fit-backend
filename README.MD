# 🏋️ Zona Fit Evolution - API Backend

Este proyecto es el backend para la aplicación móvil **Zona Fit Evolution**, construido con **Python** y **Flask**. Sigue una arquitectura modular basada en Blueprints para gestionar clientes, membresías, pagos y autenticación.

## 🚀 Guía de Instalación y Ejecución

Si eres nuevo en el proyecto o te acabas de clonar el repositorio, sigue estos pasos:

### 1. Clonar el repositorio
Si aún no lo tienes:
```bash
git clone https://github.com/MMBEGAMBRE/zona-fit-backend.git
cd zona-fit-backend
```

### 2. Configurar el Entorno Virtual (venv)
Es fundamental para que las librerías no choquen con otras versiones de tu PC.
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
Una vez activado el entorno (verás `(venv)` en tu terminal):
```bash
pip install -r requirement.txt
```

### 4. Configurar Variables de Entorno (.env)
El archivo `.env` **no se sube al repositorio** por seguridad. Debes crearlo manualmente en la raíz del proyecto con este contenido:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=zona_fit_evolution
JWT_SECRET=zonafitevolution_secret_key_2026
PORT=5050
```

### 5. Configurar la Base de Datos (MySQL)
1. Inicia tu servidor MySQL (XAMPP, Laragon, etc.).
2. Crea una base de datos llamada `zona_fit_evolution`.
3. Ejecuta el script SQL ubicado en `database/create-zonafit.sql` para crear las tablas e insertar el usuario administrador inicial.

### 6. Ejecutar el Servidor
```bash
python app.py
```
El servidor estará disponible en: `http://localhost:5050`

---

## 🛠️ Estructura del Proyecto
- `app/`: Lógica principal.
  - `routes/`: Endpoints de la API (Auth, Clientes, Membresías, etc.).
  - `models.py`: Configuración de la conexión a la base de datos.
- `database/`: Scripts SQL para la creación del esquema.
- `app.py`: Punto de entrada del servidor Flask.
- `requirement.txt`: Lista de librerías necesarias.

---

## 💡 Notas adicionales
- **Acceso desde Emulador Android**: Usa la IP `http://10.0.2.2:5050`.
- **Acceso desde Celular Físico**: Asegúrate de estar en el mismo Wi-Fi y usa la IP de tu PC (ej: `http://192.168.0.x:5050`).
