from langchain_core.tools import tool
from datetime import datetime
from dotenv import load_dotenv
import os
import sqlalchemy
import pandas as pd

# Cargar variables de entorno
load_dotenv()

# Configuración de base de datos SQL Server usando SQLAlchemy
DB_CONFIG = {
    'database': os.getenv('DB_NAME', 'DW_DDS'),
    'driver': os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server'),
    'server': os.getenv('DB_SERVER', ''),  # Vacío para servidor local con Windows Auth
    'trusted_connection': os.getenv('DB_TRUSTED_CONNECTION', 'yes')
}

def get_db_engine():
    """
    Crea el engine de SQLAlchemy para SQL Server
    Usa autenticación de Windows por defecto
    """
    if DB_CONFIG['server']:
        # Si hay servidor especificado
        connection_string = (
            f"mssql+pyodbc://{DB_CONFIG['server']}/{DB_CONFIG['database']}"
            f"?driver={DB_CONFIG['driver']}"
            f"&trusted_connection={DB_CONFIG['trusted_connection']}"
        )
    else:
        # Servidor local con autenticación Windows (como tu ejemplo)
        connection_string = (
            f"mssql+pyodbc://@/{DB_CONFIG['database']}"
            f"?driver={DB_CONFIG['driver']}"
            f"&trusted_connection={DB_CONFIG['trusted_connection']}"
        )
    
    return sqlalchemy.create_engine(connection_string)


def ejecutar_query(query, params=None):
    """
    Ejecuta una query y retorna un DataFrame de pandas
    
    Args:
        query: Query SQL a ejecutar
        params: Parámetros para la query (opcional)
    
    Returns:
        DataFrame con los resultados
    """
    engine = get_db_engine()
    
    try:
        with engine.connect() as conexion_SQL:
            if params:
                # Si hay parámetros, usar text() de sqlalchemy
                from sqlalchemy import text
                resultado = pd.read_sql(text(query), conexion_SQL, params=params)
            else:
                resultado = pd.read_sql(query, conexion_SQL)
        return resultado
    except Exception as e:
        raise Exception(f"Error al conectarse a la base de datos: {str(e)}")


# ==================== HERRAMIENTAS ====================

@tool
def consultar_servicios(servicio: str = None) -> str:
    """
    Consulta servicios disponibles en la base de datos.
    
    Args:
        servicio: Nombre del servicio (opcional). Si no se proporciona, retorna todos.
    
    Returns:
        Información de servicios en formato legible
    """
    try:
        if servicio:
            query = """
                SELECT TOP 10 
                    [Instanceid],
                    [IddServicio],
                    [is_spacial_service],
                    [is_key_channel],
                    [name],
                    [sla]
                FROM [DW_DDS].[dbo].[TblDServicios]
                WHERE [name] LIKE :servicio
            """
            params = {'servicio': f'%{servicio}%'}
            servicios = ejecutar_query(query, params)
        else:
            query = """
                SELECT TOP 20 
                    [Instanceid],
                    [IddServicio],
                    [is_spacial_service],
                    [is_key_channel],
                    [name],
                    [sla]
                FROM [DW_DDS].[dbo].[TblDServicios]
            """
            servicios = ejecutar_query(query)
        
        if servicios.empty:
            return f"No se encontraron servicios{' con nombre similar a: ' + servicio if servicio else ''}."
        
        resultado = f"Se encontraron {len(servicios)} servicio(s):\n\n"
        
        for idx, row in servicios.iterrows():
            resultado += f"📋 Servicio: {row['name']}\n"
            resultado += f"   InstanceID: {row['Instanceid']}\n"
            resultado += f"   ID Servicio: {row['IddServicio']}\n"
            resultado += f"   SLA: {row['sla']}%\n"
            resultado += f"   Servicio Especial: {'Sí' if row['is_spacial_service'] else 'No'}\n"
            resultado += f"   Canal Clave: {'Sí' if row['is_key_channel'] else 'No'}\n"
            resultado += "\n"
        
        return resultado
    
    except Exception as e:
        return f"Error al consultar servicios: {str(e)}"


@tool
def consultar_promesa_servicio(servicio: str, fechaINI: str = None, fechaFIN: str = None) -> str:
    """
    Consulta la promesa de servicio (disponibilidad esperada) para un servicio específico.
    
    Args:
        servicio: Nombre del servicio
        fechaINI: Fecha inicial en formato YYYY-MM-DD (opcional)
        fechaFIN: Fecha final en formato YYYY-MM-DD (opcional)
    
    Returns:
        Información de promesa de servicio con minutos prometidos
    """
    try:
        if not fechaINI:
            # Definir fechaINI como el primer día del año en curso
            fechaINI = datetime(datetime.now().year, 1, 1).strftime('%Y-%m-%d')
            fechaFIN = datetime.now().strftime('%Y-%m-%d')
        
        query = """
            SELECT TOP 100 * 
            FROM [DW_DDS].[dbo].[TblDPromesaServicio] 
            WHERE [Servicio] LIKE :servicio
            AND [fecha] BETWEEN :fechaINI AND :fechaFIN
            ORDER BY [fecha] DESC
        """
        
        params = {
            'servicio': f'%{servicio}%',
            'fechaINI': fechaINI,
            'fechaFIN': fechaFIN
        }
        
        promesas = ejecutar_query(query, params)
        
        if promesas.empty:
            return f"No se encontró promesa de servicio para '{servicio}' entre {fechaINI} y {fechaFIN}."
        
        # Calcular totales
        total_minutos_promesa = promesas['minutos_promesa'].sum()
        
        resultado = f"📊 Promesa de servicio para '{servicio}' ({fechaINI} a {fechaFIN}):\n\n"
        resultado += f"Total de días registrados: {len(promesas)}\n"
        resultado += f"Total minutos prometidos: {total_minutos_promesa:,.0f}\n"
        resultado += f"Promedio diario: {total_minutos_promesa / len(promesas):.0f} minutos\n\n"
        
        # Mostrar algunos ejemplos
        resultado += "Últimos registros:\n"
        for idx, row in promesas.head(5).iterrows():
            resultado += f"{idx + 1}. Fecha: {row['fecha']}\n"
            resultado += f"   Día: {row.get('dia', 'N/A')}\n"
            resultado += f"   Festivo: {'Sí' if row.get('es_festivo') else 'No'}\n"
            resultado += f"   Minutos: {row['minutos_promesa']:,.0f}\n\n"
        
        return resultado
    
    except Exception as e:
        return f"Error al consultar promesa de servicio: {str(e)}"


@tool
def consultar_afectaciones(servicio: str, fecha_inicio: str = None, fecha_fin: str = None) -> str:
    """
    Consulta las afectaciones (downtime) de un servicio en un rango de fechas.
    
    Args:
        servicio: Nombre del servicio
        fecha_inicio: Fecha inicial en formato YYYY-MM-DD (opcional)
        fecha_fin: Fecha final en formato YYYY-MM-DD (opcional)
    
    Returns:
        Información de afectaciones con tiempos de caída
    """
    try:
        if not fecha_inicio:
            # Definir fecha_inicio como el primer día del año en curso
            fecha_inicio = datetime(datetime.now().year, 1, 1).strftime('%Y-%m-%d')
            fecha_fin = datetime.now().strftime('%Y-%m-%d')
        
        query = """
            SELECT TOP 100 * 
            FROM [DW_DDS].[dbo].[TblHAfectaciones] 
            WHERE [servicio] LIKE :servicio
            AND [fecha_hora_ini_afectacion] BETWEEN :fecha_inicio AND :fecha_fin
            ORDER BY [fecha_hora_ini_afectacion] DESC
        """
        
        params = {
            'servicio': f'%{servicio}%',
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin
        }
        
        afectaciones = ejecutar_query(query, params)
        
        if afectaciones.empty:
            return f"✅ No se encontraron afectaciones para '{servicio}' entre {fecha_inicio} y {fecha_fin}."
        
        total_minutos = afectaciones['minutos'].sum()
        
        resultado = f"⚠️ Afectaciones para '{servicio}' ({fecha_inicio} a {fecha_fin}):\n\n"
        resultado += f"Total de afectaciones: {len(afectaciones)}\n"
        resultado += f"Total minutos afectados: {total_minutos:,.0f}\n"
        resultado += f"Promedio por afectación: {total_minutos / len(afectaciones):.1f} minutos\n\n"
        
        # Mostrar las afectaciones más recientes
        resultado += "Últimas afectaciones:\n"
        for idx, row in afectaciones.head(10).iterrows():
            resultado += f"{idx + 1}. Inicio: {row['fecha_hora_ini_afectacion']}\n"
            resultado += f"   Fin: {row['fecha_hora_fin_afectacion']}\n"
            resultado += f"   Minutos: {row['minutos']:,.0f}\n"
            
            # Agregar motivo si existe
            if pd.notna(row.get('motivo')):
                resultado += f"   Motivo: {row['motivo']}\n"
            
            resultado += "\n"
        
        if len(afectaciones) > 10:
            resultado += f"... y {len(afectaciones) - 10} afectaciones más.\n"
        
        return resultado
    
    except Exception as e:
        return f"Error al consultar afectaciones: {str(e)}"


@tool
def calcular_disponibilidad(servicio: str, fechaINI: str = None, fechaFIN: str = None) -> str:
    """
    Calcula la disponibilidad real de un servicio comparando promesa vs afectaciones.
    
    Args:
        servicio: Nombre del servicio
        fechaINI: Fecha inicial en formato YYYY-MM-DD (opcional)
        fechaFIN: Fecha final en formato YYYY-MM-DD (opcional)
    
    Returns:
        Porcentaje de disponibilidad y análisis comparativo
    """
    try:
        if not fechaINI:
            # Definir fechaINI como el primer día del año en curso
            fechaINI = datetime(datetime.now().year, 1, 1).strftime('%Y-%m-%d')
            fechaFIN = datetime.now().strftime('%Y-%m-%d')
        
        # Obtener promesa
        query_promesa = """
            SELECT SUM([minutos_promesa]) as minutos_promesa 
            FROM [DW_DDS].[dbo].[TblDPromesaServicio]
            WHERE [Servicio] LIKE :servicio
            AND [fecha] BETWEEN :fechaINI AND :fechaFIN
        """
        
        params_promesa = {
            'servicio': f'%{servicio}%',
            'fechaINI': fechaINI,
            'fechaFIN': fechaFIN
        }
        
        promesa_df = ejecutar_query(query_promesa, params_promesa)
        
        if promesa_df.empty or pd.isna(promesa_df.iloc[0]['minutos_promesa']):
            return f"❌ No hay promesa de servicio registrada para '{servicio}' en el período {fechaINI} a {fechaFIN}."
        
        minutos_promesa = float(promesa_df.iloc[0]['minutos_promesa'])
        
        # Obtener afectaciones
        query_afectaciones = """
            SELECT ISNULL(SUM([minutos]), 0) as total_afectacion
            FROM [DW_DDS].[dbo].[TblHAfectaciones]
            WHERE [servicio] LIKE :servicio
            AND [fecha_hora_ini_afectacion] BETWEEN :fechaINI AND :fechaFIN
        """
        
        params_afectaciones = {
            'servicio': f'%{servicio}%',
            'fechaINI': fechaINI,
            'fechaFIN': fechaFIN
        }
        
        afectacion_df = ejecutar_query(query_afectaciones, params_afectaciones)
        
        minutos_afectacion = float(afectacion_df.iloc[0]['total_afectacion']) if not afectacion_df.empty else 0
        minutos_disponibles = minutos_promesa - minutos_afectacion
        
        if minutos_promesa > 0:
            porcentaje = (minutos_disponibles / minutos_promesa) * 100
        else:
            porcentaje = 0
        
        # Calcular días y horas para mejor legibilidad
        dias_promesa = minutos_promesa / 1440
        horas_afectacion = minutos_afectacion / 60
        
        resultado = f"📈 Análisis de Disponibilidad para '{servicio}'\n"
        resultado += f"Período: {fechaINI} a {fechaFIN}\n"
        resultado += f"{'='*60}\n\n"
        
        resultado += f"📊 Minutos prometidos: {minutos_promesa:,.0f} ({dias_promesa:.1f} días)\n"
        resultado += f"⚠️  Minutos afectados: {minutos_afectacion:,.0f} ({horas_afectacion:.1f} horas)\n"
        resultado += f"✅ Minutos disponibles: {minutos_disponibles:,.0f}\n\n"
        
        resultado += f"🎯 DISPONIBILIDAD: {porcentaje:.4f}%\n\n"
        
        if porcentaje >= 99.9:
            resultado += "Estado: ✅ EXCELENTE - Cumple SLA\n"
            resultado += "El servicio está operando dentro de los parámetros óptimos."
        elif porcentaje >= 99.0:
            resultado += "Estado: ✔️  BUENO - Dentro de límites aceptables\n"
            resultado += "El servicio cumple con los estándares mínimos."
        elif porcentaje >= 95.0:
            resultado += "Estado: ⚠️  REGULAR - Requiere atención\n"
            resultado += "Se recomienda revisar las causas de las afectaciones."
        else:
            resultado += "Estado: ❌ CRÍTICO - SLA comprometido\n"
            resultado += "Se requiere acción inmediata para mejorar la disponibilidad."
        
        return resultado
    
    except Exception as e:
        return f"Error al calcular disponibilidad: {str(e)}"