"""
Módulo para cargar parámetros y reglas de validación desde Excel

IMPORTANTE:
  - Todos los parámetros de auditoría se configuran en el archivo Parámetros.xlsx.
  - Los valores hardcodeados en config.py son solo valores por defecto de respaldo.
  - Cualquier cambio en países, reglas, tipos de proveedor, etc. debe hacerse
    directamente en las hojas del archivo Parámetros.xlsx, NO en el código.
  - Si el archivo Excel no existe, se usarán los defaults de config.py con un aviso.
"""
import os
import pandas as pd
from config import (
    RUTA_PARAMETROS, MAPEO_PAISES_DEFAULT, MAPEO_REGLAS_DEFAULT,
    GEO_RULES_DEFAULT, FORMAT_RULES_DEFAULT
)


def _cargar_mapeo_paises():
    """
    Carga el mapeo de paises desde la hoja 'Geographic_Mapping' del Excel.

    Si la hoja no existe o falla, retorna el default de config.py como respaldo.

    Returns:
        dict: Diccionario {nombre_pais: codigo_ISO}
    """
    try:
        df = pd.read_excel(RUTA_PARAMETROS, sheet_name='Geographic_Mapping')
        mapeo = dict(zip(df['PAIS_DFF_HEADER'], df['CODIGO_ISO_ESPERADO']))
        print(f"  ✓ Mapeo de paises: {len(mapeo)} registros (desde Excel)")
        return mapeo
    except Exception as e:
        print(f"  ⚠ Geographic_Mapping no disponible: {e}")
        print(f"  → Usando mapeo de paises por defecto (config.py)")
        print(f"  → Para personalizar, edita la hoja 'Geographic_Mapping' en Parametros.xlsx")
        return MAPEO_PAISES_DEFAULT.copy()
    
    

def _cargar_reglas_tipos():
    """
    Carga las reglas por tipo de proveedor desde la hoja 'Hoja1' del Excel.

    Returns:
        dict: Diccionario {tipo_proveedor: {reglas}}
    """
    try:
        df = pd.read_excel(RUTA_PARAMETROS, sheet_name='Hoja1')
        reglas = {}
        for _, row in df.iterrows():
            vtype = row['VENDOR_TYPE_LOOKUP_CODE']
            if pd.isna(vtype):
                continue
            vkey = str(vtype).strip().lower()
            if vkey == 'employee':
                vkey = 'employees'
            reglas[vkey] = {
                'PAYMENT_PRIORITY': row.get('PAYMENT_PRIORITY'),
                'TERMS_ID': row.get('TERMS_ID'),
                'EXCLUDE_FREIGHT_FROM_DISCOUNT': row.get('EXCLUDE_FREIGHT_FROM_DISCOUNT'),
                'AUTO_CALCULATE_INTEREST_FLAG': row.get('AUTO_CALCULATE_INTEREST_FLAG'),
                'HEADER_END_DATE_ACTIVE': row.get('HEADER_END_DATE_ACTIVE')
            }
        print(f"  ✓ Reglas por tipo: {len(reglas)} registros (desde Excel)")
        return reglas
    except Exception as e:
        print(f"  ⚠ Hoja1 no disponible: {e}")
        print(f"  → Usando reglas por defecto (config.py)")
        print(f"  → Para personalizar, edita la hoja 'Hoja1' en Parametros.xlsx")
        return MAPEO_REGLAS_DEFAULT.copy()


def _cargar_reglas_geograficas():
    """
    Carga las reglas geográficas desde la hoja 'Geographic_Rules' del Excel.

    Returns:
        list: Lista de diccionarios con reglas geográficas
    """
    try:
        df = pd.read_excel(RUTA_PARAMETROS, sheet_name='Geographic_Rules')
        reglas = []
        for _, row in df.iterrows():
            priorities_str = str(row['ALLOWED_PRIORITIES']).split(',')
            priorities = []
            for p in priorities_str:
                p_clean = p.strip()
                if not p_clean:
                    continue
                try:
                    priorities.append(int(float(p_clean)))
                except ValueError:
                    pass
            reglas.append({
                'COUNTRY_ISO': str(row['COUNTRY_ISO']).strip().upper(),
                'SITE_CODE_PATTERN': str(row['SITE_CODE_PATTERN']).strip().upper(),
                'ALLOWED_PRIORITIES': priorities,
                'ATTRIBUTE6_ESPERADO': str(row['ATTRIBUTE6_ESPERADO']).strip().upper()
            })
        print(f"  ✓ Reglas geográficas: {len(reglas)} registros (desde Excel)")
        return reglas
    except Exception as e:
        print(f"  ⚠ Geographic_Rules no disponible: {e}")
        print(f"  → Usando reglas geográficas por defecto (config.py)")
        print(f"  → Para personalizar, edita la hoja 'Geographic_Rules' en Parámetros.xlsx")
        return list(GEO_RULES_DEFAULT)


def _cargar_reglas_formato():
    """
    Carga las reglas de formato de dirección desde la hoja 'Address_Format_Rules' del Excel.

    Returns:
        list: Lista de diccionarios con reglas de formato
    """
    try:
        df = pd.read_excel(RUTA_PARAMETROS, sheet_name='Address_Format_Rules')
        reglas = []
        for _, row in df.iterrows():
            reglas.append({
                'SITE_CODE': str(row['SITE_CODE']).strip().upper(),
                'COLUMN_NAME': str(row['COLUMN_NAME']).strip(),
                'REGEX_PATTERN': str(row['REGEX_PATTERN']).strip(),
                'REGLA_ESPERADA': str(row['REGLA_ESPERADA']).strip()
            })
        print(f"  ✓ Reglas de formato: {len(reglas)} registros (desde Excel)")
        return reglas
    except Exception as e:
        print(f"  ⚠ Address_Format_Rules no disponible: {e}")
        print(f"  → Usando reglas de formato por defecto (config.py)")
        print(f"  → Para personalizar, edita la hoja 'Address_Format_Rules' en Parámetros.xlsx")
        return list(FORMAT_RULES_DEFAULT)


def _cargar_terminos_pago():
    """
    Carga los términos de pago desde la hoja 'Terms_Definitions' del Excel.

    Returns:
        dict: Diccionario {terms_id: descripción}
    """
    try:
        df = pd.read_excel(RUTA_PARAMETROS, sheet_name='Terms_Definitions')
        mapeo = {}
        for _, row in df.iterrows():
            tid = row.get('TERMS_ID')
            desc = row.get('DESCRIPCION')
            if pd.notna(tid) and pd.notna(desc):
                try:
                    mapeo[int(float(tid))] = str(desc).strip()
                except ValueError:
                    mapeo[str(tid).strip()] = str(desc).strip()
        print(f"  ✓ Términos de pago: {len(mapeo)} registros (desde Excel)")
        return mapeo
    except Exception as e:
        print(f"  ⚠ Terms_Definitions no disponible: {e}")
        print(f"  → Para personalizar, edita la hoja 'Terms_Definitions' en Parámetros.xlsx")
        return {}


def cargar_parametros():
    """
    Carga todos los parámetros de auditoría desde Parámetros.xlsx.

    El archivo Excel es la FUENTE PRINCIPAL de configuración.
    Los valores hardcodeados en config.py son solo un RESPALDO
    que se usa cuando el Excel no existe o una hoja específica falla.

    Para agregar, modificar o eliminar parámetros:
      1. Abre el archivo Parámetros.xlsx
      2. Edita la hoja correspondiente (Geographic_Mapping, Hoja1, etc.)
      3. Guarda y ejecuta el script nuevamente
      ¡No es necesario modificar ningún archivo .py!

    Returns:
        dict: Diccionario con todos los parámetros cargados
    """

    # --- Si el Excel no existe, usar defaults con advertencia ---
    if not os.path.exists(RUTA_PARAMETROS):
        print(f"\n⚠ Archivo no encontrado: {RUTA_PARAMETROS}")
        print("  Usando valores por defecto hardcodeados en config.py...")
        print("  → Crea el archivo Parámetros.xlsx con las hojas correspondientes")
        print("    para personalizar la configuración sin tocar el código.\n")
        return {
            'mapeo_paises': MAPEO_PAISES_DEFAULT.copy(),
            'mapeo_reglas': MAPEO_REGLAS_DEFAULT.copy(),
            'geo_rules': list(GEO_RULES_DEFAULT),
            'format_rules': list(FORMAT_RULES_DEFAULT),
            'mapeo_terminos': {}
        }

    # --- Cargar desde Excel (cada hoja con su propio fallback) ---
    print("\n📋 Cargando parámetros desde Parámetros.xlsx...")
    print("  (Edita este archivo para cambiar la configuración)")

    parametros = {
        'mapeo_paises': _cargar_mapeo_paises(),
        'mapeo_reglas': _cargar_reglas_tipos(),
        'geo_rules': _cargar_reglas_geograficas(),
        'format_rules': _cargar_reglas_formato(),
        'mapeo_terminos': _cargar_terminos_pago()
    }

    print("  ✓ Parámetros cargados correctamente\n")
    return parametros
