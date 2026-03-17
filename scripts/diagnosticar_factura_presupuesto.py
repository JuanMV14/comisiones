"""
Script para diagnosticar por qué una factura no se está sumando al presupuesto por marcas
"""

import sys
import os
from datetime import datetime
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

load_dotenv()

def diagnosticar_factura(num_factura="50701"):
    try:
        from supabase import create_client
        from config.settings import AppConfig
        import pandas as pd
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            print("ERROR: Faltan variables de entorno")
            return
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        print(f"DIAGNOSTICO PARA FACTURA {num_factura}\n")
        
        # 1. Buscar la factura en comisiones
        print("1. Buscando factura en comisiones...")
        factura_response = supabase.table("comisiones").select("*").eq("factura", num_factura).execute()
        
        if not factura_response.data:
            print(f"   ERROR: No se encontro la factura {num_factura} en comisiones")
            return
        
        factura = factura_response.data[0]
        print(f"   OK: Factura encontrada:")
        print(f"      ID: {factura['id']}")
        print(f"      Cliente: {factura.get('cliente', 'N/A')}")
        print(f"      Fecha: {factura.get('fecha_factura', 'N/A')}")
        print(f"      Valor: {factura.get('valor', 0)}")
        
        # Parsear fecha de factura
        fecha_factura_str = factura.get('fecha_factura', '')
        if fecha_factura_str:
            fecha_factura = pd.to_datetime(fecha_factura_str.split('T')[0])
            mes_factura = fecha_factura.strftime('%Y-%m')
            print(f"      Mes factura: {mes_factura}")
        
        # 2. Buscar compras relacionadas por número de documento
        print(f"\n2. Buscando compras con num_documento = {num_factura}...")
        compras_response = supabase.table("compras_clientes").select("*").eq("num_documento", num_factura).eq("es_devolucion", False).execute()
        
        if not compras_response.data:
            print(f"   ERROR: No se encontraron compras con num_documento = {num_factura}")
            print(f"   Verificando variaciones del numero...")
            # Intentar buscar sin guiones, espacios, etc.
            compras_response2 = supabase.table("compras_clientes").select("*").ilike("num_documento", f"%{num_factura}%").eq("es_devolucion", False).execute()
            if compras_response2.data:
                print(f"   ATENCION: Encontradas {len(compras_response2.data)} compras con variaciones del numero:")
                for compra in compras_response2.data[:5]:
                    print(f"      Doc: {compra.get('num_documento', 'N/A')}, Marca: {compra.get('marca', 'N/A')}, Total: {compra.get('total', 0)}")
            return
        
        compras = compras_response.data
        print(f"   OK: Encontradas {len(compras)} compras")
        
        df_compras = pd.DataFrame(compras)
        
        # 3. Verificar cliente
        print(f"\n3. Verificando cliente...")
        nit_cliente = df_compras['nit_cliente'].iloc[0] if 'nit_cliente' in df_compras.columns and not df_compras.empty else None
        print(f"   NIT cliente en compras: {nit_cliente}")
        
        cliente_response = supabase.table("clientes_b2b").select("*").eq("nit", nit_cliente).execute()
        if cliente_response.data:
            cliente = cliente_response.data[0]
            print(f"   OK: Cliente encontrado: {cliente.get('nombre', 'N/A')}")
            print(f"      Cliente propio: {cliente.get('cliente_propio', False)}")
            print(f"      Activo: {cliente.get('activo', True)}")
        else:
            print(f"   ERROR: Cliente no encontrado en clientes_b2b")
        
        # 4. Verificar fechas de compras
        print(f"\n4. Verificando fechas de compras...")
        if 'fecha' in df_compras.columns:
            df_compras['fecha'] = pd.to_datetime(df_compras['fecha'], errors='coerce', dayfirst=False)
            df_compras['mes_compra'] = df_compras['fecha'].dt.strftime('%Y-%m')
            
            print(f"   Fechas encontradas:")
            print(f"      Mínima: {df_compras['fecha'].min()}")
            print(f"      Máxima: {df_compras['fecha'].max()}")
            print(f"      Meses únicos: {df_compras['mes_compra'].unique()}")
            
            if mes_factura:
                compras_mes = df_compras[df_compras['mes_compra'] == mes_factura]
                print(f"   Compras del mes {mes_factura}: {len(compras_mes)}")
        
        # 5. Verificar marcas
        print(f"\n5. Verificando marcas...")
        marcas_objetivo = ['EFFIX', 'MOTEK USA', 'KBS', 'TOYAMA']
        if 'marca' in df_compras.columns:
            df_compras['marca_normalizada'] = df_compras['marca'].astype(str).str.upper().str.strip()
            marcas_encontradas = df_compras['marca_normalizada'].unique()
            print(f"   Marcas encontradas en compras: {list(marcas_encontradas)}")
            
            # Verificar si alguna coincide con las marcas objetivo
            marcas_coincidentes = []
            for marca_obj in marcas_objetivo:
                for marca_encontrada in marcas_encontradas:
                    if marca_obj.upper() in marca_encontrada or marca_encontrada in marca_obj.upper():
                        marcas_coincidentes.append((marca_obj, marca_encontrada))
            
            if marcas_coincidentes:
                print(f"   OK: Marcas que coinciden con objetivo:")
                for marca_obj, marca_encontrada in marcas_coincidentes:
                    total_marca = df_compras[df_compras['marca_normalizada'] == marca_encontrada]['total'].sum()
                    print(f"      {marca_obj} <- {marca_encontrada}: ${total_marca:,.2f}")
            else:
                print(f"   ERROR: Ninguna marca coincide con las marcas objetivo")
                print(f"   Marcas objetivo: {marcas_objetivo}")
        
        # 6. Resumen de totales
        print(f"\n6. Resumen de totales...")
        total_compras = df_compras['total'].sum()
        print(f"   Total compras: ${total_compras:,.2f}")
        
        # Filtrar por marcas objetivo
        df_marcas_objetivo = pd.DataFrame()
        for marca_obj in marcas_objetivo:
            mask = df_compras['marca_normalizada'].str.contains(marca_obj.upper(), case=False, na=False)
            df_marcas_objetivo = pd.concat([df_marcas_objetivo, df_compras[mask]], ignore_index=True)
        
        df_marcas_objetivo = df_marcas_objetivo.drop_duplicates(subset=['id'] if 'id' in df_marcas_objetivo.columns else [])
        
        if not df_marcas_objetivo.empty:
            total_marcas_objetivo = df_marcas_objetivo['total'].sum()
            print(f"   Total marcas objetivo: ${total_marcas_objetivo:,.2f}")
            print(f"   Items de marcas objetivo: {len(df_marcas_objetivo)}")
        else:
            print(f"   ERROR: No hay compras de marcas objetivo")
        
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Diagnosticar factura en presupuesto por marcas')
    parser.add_argument('--factura', type=str, default='50701', help='Número de factura a diagnosticar')
    
    args = parser.parse_args()
    
    diagnosticar_factura(args.factura)
