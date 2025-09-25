#!/usr/bin/env python3
"""
Script para optimizar el uso de espacio en Supabase
Autor: Asistente IA
Fecha: 2024
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# Cargar variables de entorno
load_dotenv()

class SupabaseOptimizer:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
    
    def analyze_database_usage(self):
        """Analiza el uso actual de la base de datos"""
        print("🔍 Analizando uso de la base de datos...")
        
        try:
            # Analizar tabla comisiones
            comisiones_response = self.supabase.table("comisiones").select("*").execute()
            comisiones_count = len(comisiones_response.data) if comisiones_response.data else 0
            
            # Analizar tabla devoluciones
            devoluciones_response = self.supabase.table("devoluciones").select("*").execute()
            devoluciones_count = len(devoluciones_response.data) if devoluciones_response.data else 0
            
            # Analizar tabla metas
            metas_response = self.supabase.table("metas_mensuales").select("*").execute()
            metas_count = len(metas_response.data) if metas_response.data else 0
            
            print(f"📊 Resumen de datos:")
            print(f"   - Comisiones: {comisiones_count} registros")
            print(f"   - Devoluciones: {devoluciones_count} registros")
            print(f"   - Metas: {metas_count} registros")
            
            # Analizar archivos en storage
            try:
                files_response = self.supabase.storage.from_("comprobantes").list()
                files_count = len(files_response) if files_response else 0
                print(f"   - Archivos de comprobantes: {files_count} archivos")
            except Exception as e:
                print(f"   - Error analizando archivos: {e}")
            
            return {
                'comisiones': comisiones_count,
                'devoluciones': devoluciones_count,
                'metas': metas_count,
                'archivos': files_count
            }
            
        except Exception as e:
            print(f"❌ Error analizando base de datos: {e}")
            return None
    
    def clean_old_data(self, days_to_keep=730):
        """Limpia datos antiguos (más de 2 años por defecto)"""
        print(f"🧹 Limpiando datos más antiguos de {days_to_keep} días...")
        
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        
        try:
            # Limpiar comisiones antiguas
            old_comisiones = self.supabase.table("comisiones").select("id").lt("created_at", cutoff_date).execute()
            
            if old_comisiones.data:
                print(f"   - Encontradas {len(old_comisiones.data)} comisiones antiguas")
                
                # Crear backup antes de eliminar
                self.create_backup("comisiones_antiguas", old_comisiones.data)
                
                # Eliminar registros antiguos
                for record in old_comisiones.data:
                    self.supabase.table("comisiones").delete().eq("id", record["id"]).execute()
                
                print(f"   ✅ Eliminadas {len(old_comisiones.data)} comisiones antiguas")
            else:
                print("   ℹ️ No hay comisiones antiguas para eliminar")
            
            return True
            
        except Exception as e:
            print(f"❌ Error limpiando datos antiguos: {e}")
            return False
    
    def create_backup(self, table_name, data):
        """Crea backup de datos antes de eliminarlos"""
        try:
            backup_filename = f"backup_{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(backup_filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"   💾 Backup creado: {backup_filename}")
            return backup_filename
            
        except Exception as e:
            print(f"❌ Error creando backup: {e}")
            return None
    
    def optimize_storage(self):
        """Optimiza el almacenamiento de archivos"""
        print("🗂️ Optimizando almacenamiento de archivos...")
        
        try:
            # Listar archivos en storage
            files = self.supabase.storage.from_("comprobantes").list()
            
            if not files:
                print("   ℹ️ No hay archivos en storage")
                return True
            
            print(f"   - Encontrados {len(files)} archivos")
            
            # Identificar archivos duplicados o muy grandes
            large_files = []
            for file in files:
                if file.get('metadata', {}).get('size', 0) > 5 * 1024 * 1024:  # > 5MB
                    large_files.append(file)
            
            if large_files:
                print(f"   ⚠️ Encontrados {len(large_files)} archivos grandes (>5MB)")
                print("   💡 Considera comprimir estos archivos manualmente")
            
            return True
            
        except Exception as e:
            print(f"❌ Error optimizando storage: {e}")
            return False
    
    def create_optimization_report(self):
        """Crea un reporte de optimización"""
        print("📋 Generando reporte de optimización...")
        
        usage = self.analyze_database_usage()
        if not usage:
            return
        
        report = {
            'fecha_analisis': datetime.now().isoformat(),
            'uso_actual': usage,
            'recomendaciones': []
        }
        
        # Recomendaciones basadas en el análisis
        if usage['comisiones'] > 1000:
            report['recomendaciones'].append("Considera archivar comisiones antiguas (>2 años)")
        
        if usage['archivos'] > 100:
            report['recomendaciones'].append("Revisa archivos de comprobantes duplicados")
        
        if usage['comisiones'] > 5000:
            report['recomendaciones'].append("Considera migrar a un plan de pago o base de datos externa")
        
        # Guardar reporte
        report_filename = f"optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"   📄 Reporte guardado: {report_filename}")
        
        # Mostrar recomendaciones
        print("\n🎯 Recomendaciones:")
        for i, rec in enumerate(report['recomendaciones'], 1):
            print(f"   {i}. {rec}")
        
        return report

def main():
    """Función principal"""
    print("🚀 Iniciando optimización de Supabase...")
    print("=" * 50)
    
    try:
        optimizer = SupabaseOptimizer()
        
        # 1. Analizar uso actual
        usage = optimizer.analyze_database_usage()
        if not usage:
            return
        
        print("\n" + "=" * 50)
        
        # 2. Crear reporte
        report = optimizer.create_optimization_report()
        
        print("\n" + "=" * 50)
        
        # 3. Preguntar si limpiar datos antiguos
        response = input("\n¿Deseas limpiar datos antiguos (>2 años)? (s/n): ").lower()
        if response == 's':
            optimizer.clean_old_data()
        
        print("\n" + "=" * 50)
        
        # 4. Optimizar storage
        optimizer.optimize_storage()
        
        print("\n✅ Optimización completada!")
        print("\n💡 Próximos pasos recomendados:")
        print("   1. Revisa los archivos de backup generados")
        print("   2. Considera migrar a Neon o Railway si necesitas más espacio")
        print("   3. Implementa limpieza automática de datos antiguos")
        
    except Exception as e:
        print(f"❌ Error durante la optimización: {e}")

if __name__ == "__main__":
    main()
