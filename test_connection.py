"""
Script para probar la conexión a SQL Server usando el mismo método
que funciona en tu código
"""

import os
from dotenv import load_dotenv
import sqlalchemy
import pandas as pd

load_dotenv()

def test_connection():
    """Prueba la conexión a SQL Server"""
    
    print("🔍 Probando conexión a SQL Server...")
    print("="*60)
    
    # Configuración
    database = os.getenv('DB_NAME', 'DW_DDS')
    driver = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
    server = os.getenv('DB_SERVER', '')
    trusted = os.getenv('DB_TRUSTED_CONNECTION', 'yes')
    
    print(f"📊 Base de datos: {database}")
    print(f"🔧 Driver: {driver}")
    print(f"🖥️  Servidor: {server if server else '(Local con Windows Auth)'}")
    print(f"🔐 Auth Windows: {trusted}")
    print("="*60)
    
    try:
        # Construir connection string igual que tu código
        if server:
            connection_string = (
                f"mssql+pyodbc://{server}/{database}"
                f"?driver={driver}"
                f"&trusted_connection={trusted}"
            )
        else:
            # Servidor local con autenticación Windows
            connection_string = (
                f"mssql+pyodbc://@/{database}"
                f"?driver={driver}"
                f"&trusted_connection={trusted}"
            )
        
        print(f"\n🔗 Connection string:")
        print(f"   {connection_string}")
        print()
        
        # Crear engine
        engine = sqlalchemy.create_engine(connection_string)
        
        # Query de prueba 1: Versión de SQL Server
        print("📋 Prueba 1: Versión de SQL Server")
        query_version = "SELECT @@VERSION as version"
        
        with engine.connect() as conexion_SQL:
            version = pd.read_sql(query_version, conexion_SQL)
            print(f"✅ Conexión exitosa!")
            print(f"   Versión: {version.iloc[0]['version'][:80]}...")
        
        # Query de prueba 2: Contar servicios
        print("\n📋 Prueba 2: Contar servicios en TblDServicios")
        query_count = """
            SELECT COUNT(*) as total 
            FROM [DW_DDS].[dbo].[TblDServicios]
        """
        
        with engine.connect() as conexion_SQL:
            count = pd.read_sql(query_count, conexion_SQL)
            print(f"✅ Total de servicios: {count.iloc[0]['total']}")
        
        # Query de prueba 3: Primeros 5 servicios
        print("\n📋 Prueba 3: Primeros 5 servicios")
        query_servicios = """
            SELECT TOP 5 
                [Instanceid],
                [name],
                [sla]
            FROM [DW_DDS].[dbo].[TblDServicios]
        """
        
        with engine.connect() as conexion_SQL:
            servicios = pd.read_sql(query_servicios, conexion_SQL)
            print(f"✅ Servicios encontrados:")
            for idx, row in servicios.iterrows():
                print(f"   {idx + 1}. {row['name']} (SLA: {row['sla']}%)")
        
        # Query de prueba 4: Verificar TblDPromesaServicio
        print("\n📋 Prueba 4: Verificar TblDPromesaServicio")
        query_promesa = """
            SELECT COUNT(*) as total,
                   MIN(fecha) as fecha_min,
                   MAX(fecha) as fecha_max
            FROM [DW_DDS].[dbo].[TblDPromesaServicio]
        """
        
        with engine.connect() as conexion_SQL:
            promesa = pd.read_sql(query_promesa, conexion_SQL)
            print(f"✅ Registros de promesa: {promesa.iloc[0]['total']}")
            print(f"   Rango de fechas: {promesa.iloc[0]['fecha_min']} a {promesa.iloc[0]['fecha_max']}")
        
        # Query de prueba 5: Verificar TblHAfectaciones
        print("\n📋 Prueba 5: Verificar TblHAfectaciones")
        query_afectaciones = """
            SELECT COUNT(*) as total,
                   MIN(fecha_hora_ini_afectacion) as fecha_min,
                   MAX(fecha_hora_ini_afectacion) as fecha_max
            FROM [DW_DDS].[dbo].[TblHAfectaciones]
        """
        
        with engine.connect() as conexion_SQL:
            afectaciones = pd.read_sql(query_afectaciones, conexion_SQL)
            print(f"✅ Registros de afectaciones: {afectaciones.iloc[0]['total']}")
            print(f"   Rango de fechas: {afectaciones.iloc[0]['fecha_min']} a {afectaciones.iloc[0]['fecha_max']}")
        
        print("\n" + "="*60)
        print("✅ TODAS LAS PRUEBAS EXITOSAS")
        print("🚀 El agente debería funcionar correctamente")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\n" + "="*60)
        print("💡 SOLUCIONES POSIBLES:")
        print("1. Verifica que SQL Server esté corriendo")
        print("2. Verifica el nombre de la base de datos en .env (DB_NAME)")
        print("3. Verifica que tengas permisos en la base de datos")
        print("4. Si usas autenticación Windows, verifica DB_TRUSTED_CONNECTION=yes")
        print("5. Verifica que el driver ODBC esté instalado")
        print("="*60)
        
        return False


if __name__ == "__main__":
    test_connection()