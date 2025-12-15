# 🤖 Agente de Disponibilidad de Servicios con LangGraph

Sistema inteligente que utiliza LangGraph y OpenAI para consultar y analizar la disponibilidad de servicios mediante consultas en lenguaje natural a una base de datos PostgreSQL.

## 📋 Descripción del Flujo

```
INI → LLM → TOOLS → LLM → END
        ↑      ↓
        └──────┘
```

El agente:
1. Recibe preguntas en lenguaje natural
2. El LLM decide qué herramientas usar
3. Ejecuta consultas a PostgreSQL
4. Procesa y formatea los resultados
5. Retorna respuestas comprensibles

## 🗄️ Estructura de la Base de Datos

### `tbldservicios`
Contiene todos los servicios de la organización:
- `instanceid` (PK): Identificador único del servicio
- `nombre_servicio`: Nombre descriptivo
- `descripcion`: Descripción detallada
- `tipo_servicio`: Web, API, Database, etc.
- `criticidad`: Alta, Media, Baja, Crítica
- `responsable`: Equipo o persona responsable

### `tbldpromesaservicio`
Promesas de servicio (SLA) por día:
- `instanceid` (FK): Referencia al servicio
- `fecha`: Fecha específica
- `dia_semana`: Lunes, Martes, etc.
- `festivo`: Si es día festivo
- `minutos_promesa`: Minutos de disponibilidad comprometidos

### `tblhafectaciones`
Registro de afectaciones (downtime):
- `instanceid` (FK): Referencia al servicio
- `fecha`: Fecha de la afectación
- `fechahoraini`: Timestamp de inicio
- `fechahorafin`: Timestamp de fin
- `minutos_afectacion`: Duración en minutos
- `motivo`: Razón de la afectación
- `tipo_afectacion`: Planificado, Incidente, etc.

## 🛠️ Herramientas del Agente

1. **`consultar_servicios`**: Lista servicios disponibles
2. **`consultar_promesa_servicio`**: Obtiene el SLA de un servicio
3. **`consultar_afectaciones`**: Busca downtime en un rango de fechas
4. **`calcular_disponibilidad`**: Calcula % de disponibilidad real

## 🚀 Instalación

### 1. Clonar o crear el proyecto

```bash
mkdir agente-disponibilidad
cd agente-disponibilidad
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
OPENAI_API_KEY=tu_api_key_aqui
OPENAI_MODEL=gpt-5-nano

DB_HOST=localhost
DB_PORT=5432
DB_NAME=servicios_db
DB_USER=postgres
DB_PASSWORD=tu_password
```

### 5. Configurar PostgreSQL

```bash
# Crear base de datos
createdb servicios_db

# Ejecutar schema
psql -d servicios_db -f schema.sql
```

## 💻 Uso

### Modo Básico

```python
from agente import consultar_agente

# Hacer una pregunta
respuesta = consultar_agente("¿Cuál es la disponibilidad del servicio SRV-001?")
print(respuesta)
```

### Modo Interactivo

```python
if __name__ == "__main__":
    while True:
        pregunta = input("\n👤 Tú: ")
        if pregunta.lower() in ['salir', 'exit', 'quit']:
            break
        
        respuesta = consultar_agente(pregunta)
        print(f"🤖 Agente: {respuesta}")
```

## 📝 Ejemplos de Preguntas

```python
# Listar servicios
"¿Qué servicios tenemos disponibles?"

# Consultar disponibilidad
"¿Cuál es la disponibilidad del servicio SRV-001 hoy?"

# Ver afectaciones
"Muéstrame las afectaciones del SRV-002 en los últimos 7 días"

# Calcular métricas
"Calcula el porcentaje de disponibilidad para SRV-001 el 2024-12-10"

# Análisis comparativo
"¿Qué servicio tuvo más afectaciones esta semana?"
```

## 🔧 Personalización

### Agregar nuevas herramientas

```python
@tool
def tu_nueva_herramienta(parametro: str) -> str:
    """Descripción de la herramienta"""
    # Tu lógica aquí
    return resultado

# Agregar a la lista de tools
tools.append(tu_nueva_herramienta)
```

### Cambiar el modelo LLM

En el archivo `.env`:
```env
OPENAI_MODEL=gpt-4-turbo
# o
OPENAI_MODEL=gpt-3.5-turbo
```

## 📊 Visualización del Grafo

Para visualizar el flujo de LangGraph:

```python
from IPython.display import Image, display

display(Image(app.get_graph().draw_mermaid_png()))
```

## 🐛 Troubleshooting

### Error de conexión a PostgreSQL
- Verifica que PostgreSQL esté corriendo: `pg_isready`
- Revisa las credenciales en `.env`
- Confirma que la base de datos existe

### Error con OpenAI API
- Verifica tu API key en `.env`
- Confirma que el modelo existe (gpt-5-nano es ejemplo)
- Revisa tu saldo de créditos

### Error al instalar psycopg2
En Windows:
```bash
pip install psycopg2-binary
```

## 📦 Estructura del Proyecto

```
agente-disponibilidad/
├── agente.py           # Código principal del agente
├── .env                # Variables de entorno
├── requirements.txt    # Dependencias
├── schema.sql          # Esquema de base de datos
├── README.md           # Este archivo
└── venv/              # Entorno virtual (no incluir en git)
```

## 🔐 Seguridad

- **NUNCA** subas el archivo `.env` a git
- Agrega `.env` a tu `.gitignore`
- Usa variables de entorno en producción
- Limita permisos de usuario de base de datos

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📧 Contacto

Para preguntas o soporte, abre un issue en el repositorio.
