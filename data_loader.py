"""
Módulo para cargar y preparar datos de archivos CSV
"""
import pandas as pd
from config import CODIFICACIONES_CSV, COLUMNAS_CLAVE


def cargar_csv_con_autodetect(ruta_archivo, sep='\t'):
    """
    Carga un archivo CSV probando diferentes codificaciones para evitar errores
    de lectura comunes con las exportaciones de Oracle (UTF-16LE, UTF-8, Latin-1).
    
    Args:
        ruta_archivo (str): Ruta del archivo CSV
        sep (str): Separador del CSV (default: tab)
        
    Returns:
        pd.DataFrame: Dataframe cargado o None si hay error
        
    Raises:
        FileNotFoundError: Si el archivo no existe
        ValueError: Si no se puede leer el archivo
    """
    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(f"Archivo no encontrado: {ruta_archivo}")
    
    for enc in CODIFICACIONES_CSV:
        try:
            df = pd.read_csv(ruta_archivo, sep=sep, encoding=enc)
            if df.shape[1] > 1:
                return df
        except (UnicodeDecodeError, pd.errors.ParserError) as e:
            continue
        except Exception as e:
            continue
    
    # Última intención sin especificar encoding
    try:
        return pd.read_csv(ruta_archivo, sep=sep)
    except Exception as e:
        raise ValueError(f"No se pudo leer el archivo {ruta_archivo}: {str(e)}")


def remover_prefijo_comun(df):
    """
    Detecta si las columnas tienen un prefijo común (ej: HDR_ o SITE_)
    y lo elimina para que el resto del script funcione con nombres estandarizados.
    
    Args:
        df (pd.DataFrame): Dataframe con posible prefijo en columnas
        
    Returns:
        pd.DataFrame: Dataframe con columnas renombradas
    """
    prefix = ""
    for col in df.columns:
        for clave in COLUMNAS_CLAVE:
            if col.endswith(clave) and col != clave:
                prefix = col[:-len(clave)]
                break
        if prefix:
            break
            
    if prefix:
        df.columns = [
            col[len(prefix):] if col.startswith(prefix) else col 
            for col in df.columns
        ]
    return df


def cargar_datos_oracle(archivo_header, archivo_paysite):
    """
    Carga ambos archivos de Oracle (Header y PaySite) con validación.
    
    Args:
        archivo_header (str): Ruta del archivo de cabeceras
        archivo_paysite (str): Ruta del archivo de sitios
        
    Returns:
        tuple: (df_header, df_paysite) o (None, None) si hay error
        
    Raises:
        ValueError: Si hay problemas al leer los archivos
    """
    try:
        df_header = cargar_csv_con_autodetect(archivo_header)
        df_paysite = cargar_csv_con_autodetect(archivo_paysite)
        
        # Remover prefijos de columnas si existen
        df_header = remover_prefijo_comun(df_header)
        df_paysite = remover_prefijo_comun(df_paysite)
        
        print(f"✓ Cabeceras: {len(df_header)} registros")
        print(f"✓ Sitios: {len(df_paysite)} registros")
        
        return df_header, df_paysite
    except Exception as e:
        print(f"✗ Error al cargar datos Oracle: {str(e)}")
        raise


import os
