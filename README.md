# Sistema de Registro de Pacientes y Sesiones

Permite registrar pacientes, buscarlos y llevar el historial de sesiones de cada uno.

# Cómo ejecutarlo

Solo necesitas Python 3.10 o superior.

```bash
# 1. Instalar la única dependencia
pip install -r requirements.txt

# 2. (Opcional) Cargar pacientes de ejemplo, todos ficticios
python datos_ejemplo.py

# 3. Arrancar el sistema
python app.py
```

Se abre en el navegador en **http://127.0.0.1:5000**

| Usuario | Contraseña |
|---|---|
| `psicologa` | `psicologa123` |

Para detenerlo: `Ctrl+C` en la terminal.

---

## Qué hace cada archivo

```text
sistema_pacientes/
│
├── app.py                Las páginas del sistema (rutas) y el arranque.
├── base_datos.py         Esquema de la base de datos y todas las consultas.
├── datos_ejemplo.py      Carga pacientes y sesiones ficticios para probar.
├── requirements.txt      Dependencias (solo Flask).
│
├── templates/            Las pantallas, en HTML.
│   ├── base.html               Estructura común (barra de navegación).
│   ├── _mensajes.html          Avisos de éxito y error.
│   ├── login.html              Acceso al sistema.
│   ├── inicio.html             Pantalla principal con los totales.
│   ├── pacientes.html          Listado y buscador.
│   ├── formulario_paciente.html  Alta y edición de paciente.
│   ├── paciente.html           Ficha del paciente.
│   ├── formulario_sesion.html  Alta y edición de sesión.
│   ├── historial.html          Historial cronológico de sesiones.
│   ├── sesion.html             Nota completa de una sesión.
│   └── error.html              Página no encontrada.
│
├── static/css/estilos.css   Toda la apariencia (los colores están arriba).
│
└── datos/sistema.db      La base de datos. Se crea sola al arrancar.

```
