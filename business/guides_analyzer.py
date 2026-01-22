"""
Análisis de Guías - Procesamiento de datos de despachos
Analiza guías de despacho desde archivos Excel
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta


class GuidesAnalyzer:
    """Analizador de guías de despacho desde archivos Excel"""
    
    def __init__(self):
        # Festivos fijos en Colombia (mismo día todos los años)
        self.festivos_fijos = {
            (1, 1): "Año Nuevo",
            (5, 1): "Día del Trabajo",
            (7, 20): "Día de la Independencia",
            (8, 7): "Batalla de Boyacá",
            (12, 8): "Inmaculada Concepción",
            (12, 25): "Navidad"
        }
        
        # Festivos que dependen del año (necesitan cálculo específico por año)
        # Estos son aproximados y pueden variar según el calendario oficial
        self.festivos_por_ano = {
            2024: [
                date(2024, 1, 8),   # Reyes Magos
                date(2024, 3, 25),  # Día de San José
                date(2024, 3, 28),  # Jueves Santo
                date(2024, 3, 29),  # Viernes Santo
                date(2024, 5, 13),  # Ascensión del Señor
                date(2024, 6, 3),   # Corpus Christi
                date(2024, 6, 29),  # San Pedro y San Pablo
                date(2024, 8, 19),  # Asunción de la Virgen
                date(2024, 10, 14), # Día de la Raza
                date(2024, 11, 4),  # Todos los Santos
                date(2024, 11, 11), # Independencia de Cartagena
            ],
            2025: [
                date(2025, 1, 6),   # Reyes Magos
                date(2025, 3, 24),  # Día de San José
                date(2025, 4, 17),  # Jueves Santo
                date(2025, 4, 18),  # Viernes Santo
                date(2025, 5, 19),  # Ascensión del Señor
                date(2025, 6, 9),   # Corpus Christi
                date(2025, 6, 29),  # San Pedro y San Pablo
                date(2025, 8, 18),  # Asunción de la Virgen
                date(2025, 10, 13), # Día de la Raza
                date(2025, 11, 3),  # Todos los Santos
                date(2025, 11, 17), # Independencia de Cartagena
            ],
            2026: [
                date(2026, 1, 12),  # Reyes Magos
                date(2026, 3, 23),  # Día de San José
                date(2026, 4, 2),   # Jueves Santo
                date(2026, 4, 3),   # Viernes Santo
                date(2026, 5, 4),   # Ascensión del Señor
                date(2026, 5, 25),  # Corpus Christi
                date(2026, 6, 29),  # San Pedro y San Pablo
                date(2026, 8, 17),  # Asunción de la Virgen
                date(2026, 10, 12), # Día de la Raza
                date(2026, 11, 2),  # Todos los Santos
                date(2026, 11, 16), # Independencia de Cartagena
            ]
        }
    
    def obtener_festivos_ano(self, ano: int) -> List[date]:
        """
        Obtiene todos los festivos para un año específico
        
        Args:
            ano: Año para el cual obtener los festivos
            
        Returns:
            Lista de fechas festivas
        """
        festivos = []
        
        # Agregar festivos fijos
        for (mes, dia), nombre in self.festivos_fijos.items():
            festivos.append(date(ano, mes, dia))
        
        # Agregar festivos específicos del año si están disponibles
        if ano in self.festivos_por_ano:
            festivos.extend(self.festivos_por_ano[ano])
        
        return festivos
    
    def calcular_dias_laborables(self, fecha_inicio: pd.Timestamp, fecha_fin: pd.Timestamp) -> int:
        """
        Calcula días laborables entre dos fechas excluyendo domingos y festivos
        Cuenta desde el día siguiente a la creación hasta el día de entrega (inclusivo)
        
        Args:
            fecha_inicio: Fecha de creación de la guía
            fecha_fin: Fecha de entrega
            
        Returns:
            Número de días laborables
        """
        if pd.isna(fecha_inicio) or pd.isna(fecha_fin):
            return 0
        
        # Convertir a date si es necesario
        if isinstance(fecha_inicio, pd.Timestamp):
            fecha_inicio = fecha_inicio.date()
        if isinstance(fecha_fin, pd.Timestamp):
            fecha_fin = fecha_fin.date()
        
        if fecha_inicio >= fecha_fin:
            # Si la entrega es el mismo día o antes que la creación, es 0 días
            return 0
        
        # Obtener festivos para todos los años relevantes en el rango
        ano_inicio = fecha_inicio.year
        ano_fin = fecha_fin.year
        anos_involucrados = set(range(ano_inicio, ano_fin + 1))
        
        # Crear conjunto de festivos para búsqueda rápida
        festivos_set = set()
        for ano in anos_involucrados:
            festivos_set.update(self.obtener_festivos_ano(ano))
        
        # Contar días laborables desde el día siguiente a la creación hasta la entrega (inclusivo)
        # Ejemplo: Creada lunes, entregada miércoles = martes (1 día) + miércoles (1 día) = 2 días
        dias_laborables = 0
        fecha_actual = fecha_inicio + timedelta(days=1)  # Empezar desde el día siguiente
        
        while fecha_actual <= fecha_fin:
            # Verificar si no es domingo (0 = lunes, 6 = domingo en weekday())
            dia_semana = fecha_actual.weekday()
            
            # Verificar si no es festivo
            es_festivo = fecha_actual in festivos_set
            
            # Contar solo si no es domingo ni festivo
            if dia_semana != 6 and not es_festivo:
                dias_laborables += 1
            
            fecha_actual += timedelta(days=1)
        
        return dias_laborables
    
    def clasificar_tiempo_acido(self, dias_laborables: int) -> str:
        """
        Clasifica el tiempo ácido según días laborables
        Clasificación flexible considerando que en logística no todo es 100% perfecto
        
        Args:
            dias_laborables: Número de días laborables
            
        Returns:
            "En tiempo", "Validar", o "Fuera de tiempo"
        """
        if dias_laborables <= 2:
            # 0-2 días laborables = aceptable, en tiempo
            # Ejemplo: Creada lunes, entregada miércoles (2 días) = OK
            return "En tiempo"
        elif dias_laborables <= 4:
            # 3-4 días laborables = necesita validación
            return "Validar"
        else:
            # 5+ días laborables = fuera de tiempo
            return "Fuera de tiempo"
    
    def calcular_tiempo_acido_automatico(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula automáticamente el "Tiempo ácido" basándose en fechas de creación y entrega
        
        Args:
            df: DataFrame con los datos de guías
            
        Returns:
            DataFrame con columna "Tiempo acido" calculada
        """
        df_resultado = df.copy()
        
        # Buscar columnas de fecha
        columna_creacion = None
        columna_entrega = None
        columna_tiempo_acido = None
        
        for col in df.columns:
            col_lower = str(col).lower().strip()
            # Buscar columna de creación de guía (más flexible)
            if 'creacion' in col_lower or ('fecha' in col_lower and 'creacion' in col_lower):
                if columna_creacion is None or 'guia' in col_lower:
                    columna_creacion = col
            # Buscar columna de entrega (más flexible)
            elif 'entrega' in col_lower or ('dia' in col_lower and 'entrega' in col_lower):
                if columna_entrega is None:
                    columna_entrega = col
            # Buscar columna de fecha de entrega
            elif 'fecha' in col_lower and ('entrega' in col_lower or 'entregado' in col_lower):
                if columna_entrega is None:
                    columna_entrega = col
            # Buscar columna de tiempo ácido existente
            elif 'tiempo' in col_lower and 'acido' in col_lower:
                columna_tiempo_acido = col
        
        # Si no encontramos las columnas necesarias, retornar sin cambios
        if columna_creacion is None or columna_entrega is None:
            return df_resultado
        
        # Convertir fechas a datetime
        df_resultado[columna_creacion] = pd.to_datetime(df_resultado[columna_creacion], errors='coerce')
        df_resultado[columna_entrega] = pd.to_datetime(df_resultado[columna_entrega], errors='coerce')
        
        # Calcular días laborables y clasificar
        def calcular_y_clasificar(row):
            if pd.isna(row[columna_creacion]) or pd.isna(row[columna_entrega]):
                return "Sin fecha de entrega"
            
            dias_lab = self.calcular_dias_laborables(row[columna_creacion], row[columna_entrega])
            return self.clasificar_tiempo_acido(dias_lab)
        
        # Si ya existe la columna, la reemplazamos, si no, la creamos
        if columna_tiempo_acido:
            df_resultado[columna_tiempo_acido] = df_resultado.apply(calcular_y_clasificar, axis=1)
        else:
            df_resultado["Tiempo acido"] = df_resultado.apply(calcular_y_clasificar, axis=1)
        
        return df_resultado
    
    def cargar_excel(self, file, hoja: str, calcular_tiempo_acido: bool = True) -> Optional[pd.DataFrame]:
        """
        Carga un archivo Excel y devuelve la hoja seleccionada
        
        Args:
            file: Archivo Excel subido via Streamlit
            hoja: Nombre de la hoja a cargar
            calcular_tiempo_acido: Si True, calcula automáticamente el tiempo ácido
            
        Returns:
            DataFrame con los datos o None si hay error
        """
        try:
            df = pd.read_excel(file, sheet_name=hoja)
            
            # Calcular tiempo ácido automáticamente si se solicita
            if calcular_tiempo_acido:
                df = self.calcular_tiempo_acido_automatico(df)
            
            return df
        except Exception as e:
            raise Exception(f"Error cargando Excel: {str(e)}")
    
    def obtener_hojas_excel(self, file) -> List[str]:
        """
        Obtiene la lista de hojas disponibles en el archivo Excel
        
        Args:
            file: Archivo Excel subido via Streamlit
            
        Returns:
            Lista con nombres de las hojas
        """
        try:
            excel_file = pd.ExcelFile(file)
            return excel_file.sheet_names
        except Exception as e:
            raise Exception(f"Error leyendo hojas del Excel: {str(e)}")
    
    def analizar_guias_por_tiempo_acido(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analiza la cantidad de guías por categoría en "Tiempo ácido"
        
        Args:
            df: DataFrame con los datos de guías
            
        Returns:
            Diccionario con categorías y cantidades
        """
        try:
            # Normalizar nombre de columna (puede tener espacios o mayúsculas)
            columna_tiempo = None
            for col in df.columns:
                if 'tiempo' in col.lower() and 'acido' in col.lower():
                    columna_tiempo = col
                    break
            
            if columna_tiempo is None:
                return {"error": "No se encontró la columna 'Tiempo acido'"}
            
            # Contar por categoría
            conteo = df[columna_tiempo].value_counts().to_dict()
            
            # Asegurar que existan las 3 categorías
            categorias = {
                "En tiempo": conteo.get("En tiempo", 0),
                "Validar": conteo.get("Validar", 0),
                "Fuera de tiempo": conteo.get("Fuera de tiempo", 0)
            }
            
            return {
                "categorias": list(categorias.keys()),
                "cantidades": list(categorias.values()),
                "total": sum(categorias.values())
            }
        except Exception as e:
            return {"error": f"Error analizando tiempo ácido: {str(e)}"}
    
    def analizar_ciudades_unidades(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analiza ciudades con más unidades despachadas
        
        Args:
            df: DataFrame con los datos de guías
            
        Returns:
            Diccionario con ciudades y total de unidades
        """
        try:
            # Buscar columnas relevantes
            columna_ciudad = None
            columna_unidades = None
            
            for col in df.columns:
                if 'ciudad' in col.lower():
                    columna_ciudad = col
                elif 'unidades' in col.lower():
                    columna_unidades = col
            
            if columna_ciudad is None or columna_unidades is None:
                return {"error": "No se encontraron las columnas 'Ciudad' o 'Unidades'"}
            
            # Agrupar por ciudad y sumar unidades
            df_ciudades = df.groupby(columna_ciudad)[columna_unidades].sum().reset_index()
            df_ciudades = df_ciudades.sort_values(columna_unidades, ascending=False).head(10)
            
            return {
                "ciudades": df_ciudades[columna_ciudad].tolist(),
                "unidades": df_ciudades[columna_unidades].tolist()
            }
        except Exception as e:
            return {"error": f"Error analizando ciudades: {str(e)}"}
    
    def analizar_transportadoras_efectividad(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calcula ranking de transportadoras según efectividad (%)
        
        Args:
            df: DataFrame con los datos de guías
            
        Returns:
            Diccionario con transportadoras y efectividad
        """
        try:
            # Buscar columnas relevantes
            columna_transportadora = None
            columna_estado = None
            columna_tiempo_acido = None
            
            for col in df.columns:
                if 'transportadora' in col.lower():
                    columna_transportadora = col
                elif 'estado' in col.lower():
                    columna_estado = col
                elif 'tiempo' in col.lower() and 'acido' in col.lower():
                    columna_tiempo_acido = col
            
            if columna_transportadora is None:
                return {"error": "No se encontró la columna 'Transportadora'"}
            
            # Calcular efectividad: % de guías "En tiempo" por transportadora
            resultados = []
            
            for transportadora in df[columna_transportadora].unique():
                df_transp = df[df[columna_transportadora] == transportadora]
                total = len(df_transp)
                
                if total == 0:
                    continue
                
                # Contar las que están "En tiempo"
                if columna_tiempo_acido:
                    en_tiempo = len(df_transp[df_transp[columna_tiempo_acido] == "En tiempo"])
                    efectividad = (en_tiempo / total * 100) if total > 0 else 0
                else:
                    # Si no hay columna de tiempo ácido, usar estado "ENTREGADO"
                    if columna_estado:
                        entregadas = len(df_transp[df_transp[columna_estado] == "ENTREGADO"])
                        efectividad = (entregadas / total * 100) if total > 0 else 0
                    else:
                        efectividad = 0
                
                resultados.append({
                    "transportadora": transportadora,
                    "efectividad": round(efectividad, 1),
                    "total": total
                })
            
            # Ordenar por efectividad descendente
            resultados = sorted(resultados, key=lambda x: x["efectividad"], reverse=True)
            
            return {
                "transportadoras": [r["transportadora"] for r in resultados],
                "efectividad": [r["efectividad"] for r in resultados]
            }
        except Exception as e:
            return {"error": f"Error analizando transportadoras: {str(e)}"}
    
    def analizar_ciudades_fuera_tiempo(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analiza ciudades con guías fuera de tiempo
        
        Args:
            df: DataFrame con los datos de guías
            
        Returns:
            Diccionario con ciudades y cantidad de guías fuera de tiempo
        """
        try:
            # Buscar columnas relevantes
            columna_ciudad = None
            columna_tiempo_acido = None
            
            for col in df.columns:
                if 'ciudad' in col.lower():
                    columna_ciudad = col
                elif 'tiempo' in col.lower() and 'acido' in col.lower():
                    columna_tiempo_acido = col
            
            if columna_ciudad is None or columna_tiempo_acido is None:
                return {"error": "No se encontraron las columnas necesarias"}
            
            # Filtrar solo las que están "Fuera de tiempo"
            df_fuera_tiempo = df[df[columna_tiempo_acido] == "Fuera de tiempo"]
            
            # Agrupar por ciudad y contar
            conteo = df_fuera_tiempo.groupby(columna_ciudad).size().reset_index(name='cantidad')
            conteo = conteo.sort_values('cantidad', ascending=False)
            
            return {
                "ciudades": conteo[columna_ciudad].tolist(),
                "cantidades": conteo['cantidad'].tolist()
            }
        except Exception as e:
            return {"error": f"Error analizando ciudades fuera de tiempo: {str(e)}"}
    
    def analizar_transportadoras_tiempo_acido(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analiza el desglose de "Tiempo ácido" por cada transportadora
        
        Args:
            df: DataFrame con los datos de guías
            
        Returns:
            Diccionario con transportadoras y distribución de tiempo ácido
        """
        try:
            # Buscar columnas relevantes
            columna_transportadora = None
            columna_tiempo_acido = None
            
            for col in df.columns:
                if 'transportadora' in col.lower():
                    columna_transportadora = col
                elif 'tiempo' in col.lower() and 'acido' in col.lower():
                    columna_tiempo_acido = col
            
            if columna_transportadora is None or columna_tiempo_acido is None:
                return {"error": "No se encontraron las columnas 'Transportadora' o 'Tiempo acido'"}
            
            # Agrupar por transportadora y tiempo ácido
            resultados = []
            
            for transportadora in df[columna_transportadora].unique():
                df_transp = df[df[columna_transportadora] == transportadora]
                
                # Contar por categoría
                conteo = df_transp[columna_tiempo_acido].value_counts().to_dict()
                
                total = len(df_transp)
                en_tiempo = conteo.get("En tiempo", 0)
                validar = conteo.get("Validar", 0)
                fuera_tiempo = conteo.get("Fuera de tiempo", 0)
                
                # Calcular porcentajes
                porcentaje_en_tiempo = (en_tiempo / total * 100) if total > 0 else 0
                
                resultados.append({
                    "transportadora": transportadora,
                    "total": total,
                    "en_tiempo": en_tiempo,
                    "validar": validar,
                    "fuera_tiempo": fuera_tiempo,
                    "porcentaje_en_tiempo": round(porcentaje_en_tiempo, 1)
                })
            
            # Ordenar por porcentaje "En tiempo" descendente
            resultados = sorted(resultados, key=lambda x: x["porcentaje_en_tiempo"], reverse=True)
            
            return {
                "transportadoras": [r["transportadora"] for r in resultados],
                "en_tiempo": [r["en_tiempo"] for r in resultados],
                "validar": [r["validar"] for r in resultados],
                "fuera_tiempo": [r["fuera_tiempo"] for r in resultados],
                "totales": [r["total"] for r in resultados],
                "porcentajes_en_tiempo": [r["porcentaje_en_tiempo"] for r in resultados]
            }
        except Exception as e:
            return {"error": f"Error analizando transportadoras por tiempo ácido: {str(e)}"}
    
    def procesar_analisis_completo(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Procesa todos los análisis y devuelve los resultados
        
        Args:
            df: DataFrame con los datos de guías
            
        Returns:
            Diccionario con todos los análisis
        """
        return {
            "tiempo_acido": self.analizar_guias_por_tiempo_acido(df),
            "ciudades_unidades": self.analizar_ciudades_unidades(df),
            "transportadoras": self.analizar_transportadoras_efectividad(df),
            "ciudades_fuera_tiempo": self.analizar_ciudades_fuera_tiempo(df),
            "transportadoras_tiempo_acido": self.analizar_transportadoras_tiempo_acido(df)
        }

