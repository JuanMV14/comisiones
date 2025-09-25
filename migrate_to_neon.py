#!/usr/bin/env python3
"""
Script para migrar de Supabase a Neon
Autor: Asistente IA
Fecha: 2024
"""

import os
import pandas as pd
import psycopg2
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# Cargar variables de entorno
load_dotenv()

class SupabaseToNeonMigrator:
    def __init__(self):
        # Supabase (origen)
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        # Neon (destino) - Necesitarás configurar estas variables
        self.neon_host = os.getenv("NEON_HOST")
        self.neon_database = os.getenv("NEON_DATABASE")
        self.neon_user = os.getenv("NEON_USER")
        self.neon_password = os.getenv("NEON_PASSWORD")
        
        if not all([self.supabase_url, self.supabase_key]):
            raise ValueError("Faltan las variables de entorno de Supabase")
        
        if not all([self.neon_host, self.neon_database, self.neon_user, self.neon_password]):
            raise ValueError("Faltan las variables de entorno de Neon")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.neon_conn = None
    
    def connect_to_neon(self):
        """Conecta a la base de datos Neon"""
        try:
            self.neon_conn = psycopg2.connect(
                host=self.neon_host,
                database=self.neon_database,
                user=self.neon_user,
                password=self.neon_password,
                sslmode='require'
            )
            print("✅ Conectado a Neon exitosamente")
            return True
        except Exception as e:
            print(f"❌ Error conectando a Neon: {e}")
            return False
    
    def create_neon_tables(self):
        """Crea las tablas en Neon"""
        print("🏗️ Creando tablas en Neon...")
        
        create_tables_sql = """
        -- Tabla comisiones
        CREATE TABLE IF NOT EXISTS comisiones (
            id SERIAL PRIMARY KEY,
            pedido VARCHAR(255) NOT NULL,
            cliente VARCHAR(255) NOT NULL,
            factura VARCHAR(255),
            valor DECIMAL(15,2) NOT NULL,
            valor_neto DECIMAL(15,2),
            iva DECIMAL(15,2),
            base_comision DECIMAL(15,2),
            comision DECIMAL(15,2),
            porcentaje DECIMAL(5,2),
            fecha_factura DATE,
            fecha_pago_est DATE,
            fecha_pago_max DATE,
            fecha_pago_real DATE,
            dias_pago_real INTEGER,
            pagado BOOLEAN DEFAULT FALSE,
            cliente_propio BOOLEAN DEFAULT FALSE,
            condicion_especial BOOLEAN DEFAULT FALSE,
            descuento_pie_factura BOOLEAN DEFAULT FALSE,
            descuento_adicional DECIMAL(5,2) DEFAULT 0,
            comision_perdida BOOLEAN DEFAULT FALSE,
            razon_perdida TEXT,
            comision_ajustada DECIMAL(15,2),
            valor_devuelto DECIMAL(15,2) DEFAULT 0,
            metodo_pago VARCHAR(100),
            referencia VARCHAR(255),
            observaciones_pago TEXT,
            comprobante_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Tabla devoluciones
        CREATE TABLE IF NOT EXISTS devoluciones (
            id SERIAL PRIMARY KEY,
            factura_id INTEGER REFERENCES comisiones(id),
            valor_devuelto DECIMAL(15,2) NOT NULL,
            motivo TEXT,
            fecha_devolucion DATE,
            afecta_comision BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Tabla metas_mensuales
        CREATE TABLE IF NOT EXISTS metas_mensuales (
            id SERIAL PRIMARY KEY,
            mes VARCHAR(7) UNIQUE NOT NULL,
            meta_ventas DECIMAL(15,2) NOT NULL,
            meta_clientes_nuevos INTEGER NOT NULL,
            ventas_actuales DECIMAL(15,2) DEFAULT 0,
            clientes_nuevos_actuales INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Índices para optimizar consultas
        CREATE INDEX IF NOT EXISTS idx_comisiones_cliente ON comisiones(cliente);
        CREATE INDEX IF NOT EXISTS idx_comisiones_fecha ON comisiones(fecha_factura);
        CREATE INDEX IF NOT EXISTS idx_comisiones_pagado ON comisiones(pagado);
        CREATE INDEX IF NOT EXISTS idx_devoluciones_factura ON devoluciones(factura_id);
        """
        
        try:
            cursor = self.neon_conn.cursor()
            cursor.execute(create_tables_sql)
            self.neon_conn.commit()
            cursor.close()
            print("✅ Tablas creadas exitosamente en Neon")
            return True
        except Exception as e:
            print(f"❌ Error creando tablas: {e}")
            return False
    
    def migrate_comisiones(self):
        """Migra datos de comisiones"""
        print("📦 Migrando comisiones...")
        
        try:
            # Obtener datos de Supabase
            response = self.supabase.table("comisiones").select("*").execute()
            
            if not response.data:
                print("   ℹ️ No hay comisiones para migrar")
                return True
            
            print(f"   - Encontradas {len(response.data)} comisiones")
            
            # Preparar datos para inserción
            cursor = self.neon_conn.cursor()
            
            for record in response.data:
                # Limpiar datos nulos
                cleaned_record = {}
                for key, value in record.items():
                    if value is None or value == "NULL":
                        cleaned_record[key] = None
                    else:
                        cleaned_record[key] = value
                
                # Insertar en Neon
                insert_sql = """
                INSERT INTO comisiones (
                    pedido, cliente, factura, valor, valor_neto, iva, base_comision,
                    comision, porcentaje, fecha_factura, fecha_pago_est, fecha_pago_max,
                    fecha_pago_real, dias_pago_real, pagado, cliente_propio, condicion_especial,
                    descuento_pie_factura, descuento_adicional, comision_perdida, razon_perdida,
                    comision_ajustada, valor_devuelto, metodo_pago, referencia, observaciones_pago,
                    comprobante_url, created_at, updated_at
                ) VALUES (
                    %(pedido)s, %(cliente)s, %(factura)s, %(valor)s, %(valor_neto)s, %(iva)s, %(base_comision)s,
                    %(comision)s, %(porcentaje)s, %(fecha_factura)s, %(fecha_pago_est)s, %(fecha_pago_max)s,
                    %(fecha_pago_real)s, %(dias_pago_real)s, %(pagado)s, %(cliente_propio)s, %(condicion_especial)s,
                    %(descuento_pie_factura)s, %(descuento_adicional)s, %(comision_perdida)s, %(razon_perdida)s,
                    %(comision_ajustada)s, %(valor_devuelto)s, %(metodo_pago)s, %(referencia)s, %(observaciones_pago)s,
                    %(comprobante_url)s, %(created_at)s, %(updated_at)s
                )
                """
                
                cursor.execute(insert_sql, cleaned_record)
            
            self.neon_conn.commit()
            cursor.close()
            
            print(f"   ✅ Migradas {len(response.data)} comisiones exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error migrando comisiones: {e}")
            return False
    
    def migrate_devoluciones(self):
        """Migra datos de devoluciones"""
        print("🔄 Migrando devoluciones...")
        
        try:
            response = self.supabase.table("devoluciones").select("*").execute()
            
            if not response.data:
                print("   ℹ️ No hay devoluciones para migrar")
                return True
            
            print(f"   - Encontradas {len(response.data)} devoluciones")
            
            cursor = self.neon_conn.cursor()
            
            for record in response.data:
                cleaned_record = {}
                for key, value in record.items():
                    if value is None or value == "NULL":
                        cleaned_record[key] = None
                    else:
                        cleaned_record[key] = value
                
                insert_sql = """
                INSERT INTO devoluciones (
                    factura_id, valor_devuelto, motivo, fecha_devolucion, 
                    afecta_comision, created_at
                ) VALUES (
                    %(factura_id)s, %(valor_devuelto)s, %(motivo)s, %(fecha_devolucion)s,
                    %(afecta_comision)s, %(created_at)s
                )
                """
                
                cursor.execute(insert_sql, cleaned_record)
            
            self.neon_conn.commit()
            cursor.close()
            
            print(f"   ✅ Migradas {len(response.data)} devoluciones exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error migrando devoluciones: {e}")
            return False
    
    def migrate_metas(self):
        """Migra datos de metas"""
        print("🎯 Migrando metas...")
        
        try:
            response = self.supabase.table("metas_mensuales").select("*").execute()
            
            if not response.data:
                print("   ℹ️ No hay metas para migrar")
                return True
            
            print(f"   - Encontradas {len(response.data)} metas")
            
            cursor = self.neon_conn.cursor()
            
            for record in response.data:
                cleaned_record = {}
                for key, value in record.items():
                    if value is None or value == "NULL":
                        cleaned_record[key] = None
                    else:
                        cleaned_record[key] = value
                
                insert_sql = """
                INSERT INTO metas_mensuales (
                    mes, meta_ventas, meta_clientes_nuevos, ventas_actuales,
                    clientes_nuevos_actuales, created_at, updated_at
                ) VALUES (
                    %(mes)s, %(meta_ventas)s, %(meta_clientes_nuevos)s, %(ventas_actuales)s,
                    %(clientes_nuevos_actuales)s, %(created_at)s, %(updated_at)s
                )
                """
                
                cursor.execute(insert_sql, cleaned_record)
            
            self.neon_conn.commit()
            cursor.close()
            
            print(f"   ✅ Migradas {len(response.data)} metas exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error migrando metas: {e}")
            return False
    
    def verify_migration(self):
        """Verifica que la migración fue exitosa"""
        print("🔍 Verificando migración...")
        
        try:
            cursor = self.neon_conn.cursor()
            
            # Contar registros en cada tabla
            cursor.execute("SELECT COUNT(*) FROM comisiones")
            comisiones_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM devoluciones")
            devoluciones_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM metas_mensuales")
            metas_count = cursor.fetchone()[0]
            
            cursor.close()
            
            print(f"   📊 Registros en Neon:")
            print(f"      - Comisiones: {comisiones_count}")
            print(f"      - Devoluciones: {devoluciones_count}")
            print(f"      - Metas: {metas_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error verificando migración: {e}")
            return False
    
    def create_env_template(self):
        """Crea template de variables de entorno para Neon"""
        template = """
# Variables de entorno para Neon
NEON_HOST=your-neon-host.neon.tech
NEON_DATABASE=your-database-name
NEON_USER=your-username
NEON_PASSWORD=your-password

# Mantén las variables de Supabase para referencia
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
"""
        
        with open('.env.neon.template', 'w') as f:
            f.write(template)
        
        print("📄 Template de variables de entorno creado: .env.neon.template")
    
    def close_connections(self):
        """Cierra las conexiones"""
        if self.neon_conn:
            self.neon_conn.close()
            print("🔌 Conexión a Neon cerrada")

def main():
    """Función principal de migración"""
    print("🚀 Iniciando migración de Supabase a Neon...")
    print("=" * 60)
    
    try:
        migrator = SupabaseToNeonMigrator()
        
        # 1. Conectar a Neon
        if not migrator.connect_to_neon():
            return
        
        print("\n" + "=" * 60)
        
        # 2. Crear tablas
        if not migrator.create_neon_tables():
            return
        
        print("\n" + "=" * 60)
        
        # 3. Migrar datos
        if not migrator.migrate_comisiones():
            return
        
        if not migrator.migrate_devoluciones():
            return
        
        if not migrator.migrate_metas():
            return
        
        print("\n" + "=" * 60)
        
        # 4. Verificar migración
        migrator.verify_migration()
        
        print("\n" + "=" * 60)
        
        # 5. Crear template de configuración
        migrator.create_env_template()
        
        print("\n✅ Migración completada exitosamente!")
        print("\n📋 Próximos pasos:")
        print("   1. Actualiza tu archivo .env con las credenciales de Neon")
        print("   2. Modifica app.py para usar psycopg2 en lugar de supabase-py")
        print("   3. Prueba la aplicación con la nueva base de datos")
        print("   4. Una vez verificado, puedes eliminar los datos de Supabase")
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
    
    finally:
        if 'migrator' in locals():
            migrator.close_connections()

if __name__ == "__main__":
    main()
