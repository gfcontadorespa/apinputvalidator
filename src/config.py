"""
Configuración central y constantes para auditoría de proveedores Oracle EBS
"""
import os

# Directorio base (raíz del proyecto, un nivel arriba de src/)
DIRECTORIO_SCRIPT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Rutas de configuración y parámetros
RUTA_PARAMETROS = os.path.join(DIRECTORIO_SCRIPT, 'Parámetros.xlsx')

# Directorio de datos de ejemplo
DIRECTORIO_EXAMPLE_DATA = os.path.join(DIRECTORIO_SCRIPT, 'ExampleData')
ARCHIVO_HEADER_EJEMPLO = os.path.join(DIRECTORIO_EXAMPLE_DATA, 'AP New or Updated Suppliers - Header View.csv')
ARCHIVO_PAYSITE_EJEMPLO = os.path.join(DIRECTORIO_EXAMPLE_DATA, 'AP New or Updated Suppliers - PaySite View.csv')

# Codificaciones soportadas para CSV
CODIFICACIONES_CSV = ['utf-16', 'utf-8', 'latin-1']

# Nombres de columnas esperadas
COLUMNAS_CLAVE = ['VENDOR_ID', 'VENDOR_NUMBER', 'VENDOR_SITE_CODE']

# Mapeo de países (país largo -> código ISO)
MAPEO_PAISES_DEFAULT = {
    'Republica de Panama': 'PA',
    'Canada': 'CA',
    'Spain': 'ES',
    'United States': 'US',
    'France': 'FR',
    'Germany': 'DE',
    'Chile': 'CL',
    'Sweden': 'SE',
    'Norway': 'NO',
    'Denmark': 'DK',
    'Finland': 'FI',
    'Netherlands': 'NL',
    'Italy': 'IT',
    'United Kingdom': 'GB',
    'Mexico': 'MX',
    'Brazil': 'BR',
    'Argentina': 'AR',
    'Colombia': 'CO',
    'Peru': 'PE',
    'Venezuela': 'VE',
    'Costa Rica': 'CR',
    'El Salvador': 'SV',
}

# Reglas por tipo de proveedor
MAPEO_REGLAS_DEFAULT = {
    'employees': {
        'PAYMENT_PRIORITY': 'Y', 'TERMS_ID': 'Y', 'EXCLUDE_FREIGHT_FROM_DISCOUNT': 'N', 
        'AUTO_CALCULATE_INTEREST_FLAG': 'N', 'HEADER_END_DATE_ACTIVE': 'N'
    },
    'claims': {
        'PAYMENT_PRIORITY': 'Y', 'TERMS_ID': 'Y', 'EXCLUDE_FREIGHT_FROM_DISCOUNT': 'N', 
        'AUTO_CALCULATE_INTEREST_FLAG': 'N', 'HEADER_END_DATE_ACTIVE': 'Y'
    },
    'trust': {
        'PAYMENT_PRIORITY': 'Y', 'TERMS_ID': 'Y', 'EXCLUDE_FREIGHT_FROM_DISCOUNT': 'N', 
        'AUTO_CALCULATE_INTEREST_FLAG': 'N', 'HEADER_END_DATE_ACTIVE': 'Y'
    },
    'miscellaneous services': {
        'PAYMENT_PRIORITY': 'Y', 'TERMS_ID': 'Y', 'EXCLUDE_FREIGHT_FROM_DISCOUNT': 'Y', 
        'AUTO_CALCULATE_INTEREST_FLAG': 'Y', 'HEADER_END_DATE_ACTIVE': 'N'
    }
}

# Reglas geográficas por defecto
GEO_RULES_DEFAULT = [
    {'COUNTRY_ISO': 'PA', 'SITE_CODE_PATTERN': 'ACH LOCAL*', 'ALLOWED_PRIORITIES': [99], 'ATTRIBUTE6_ESPERADO': 'OUR'},
    {'COUNTRY_ISO': 'PA', 'SITE_CODE_PATTERN': 'TRAMITE*', 'ALLOWED_PRIORITIES': [71, 73], 'ATTRIBUTE6_ESPERADO': 'OUR'},
    {'COUNTRY_ISO': 'US', 'SITE_CODE_PATTERN': 'ACH USA*', 'ALLOWED_PRIORITIES': [50], 'ATTRIBUTE6_ESPERADO': 'OUR'},
    {'COUNTRY_ISO': 'US', 'SITE_CODE_PATTERN': 'BANK TRANSFER*', 'ALLOWED_PRIORITIES': [50], 'ATTRIBUTE6_ESPERADO': 'BEN'},
    {'COUNTRY_ISO': 'DEFAULT', 'SITE_CODE_PATTERN': 'BANK TRANSFER*', 'ALLOWED_PRIORITIES': [50], 'ATTRIBUTE6_ESPERADO': 'BEN'}
]

# Reglas de formato de dirección por defecto
FORMAT_RULES_DEFAULT = [
    {'SITE_CODE': 'ACH LOCAL', 'COLUMN_NAME': 'ADDRESS_LINE2', 
     'REGEX_PATTERN': r'^RUTA Y TRANSITO #[0-9]{9}$', 
     'REGLA_ESPERADA': 'Debe cumplir exactamente: RUTA Y TRANSITO #[9 dígitos]'},
    {'SITE_CODE': 'ACH LOCAL', 'COLUMN_NAME': 'ADDRESS_LINE3', 
     'REGEX_PATTERN': r'^CTA#[a-zA-Z0-9\-]+ ABA#[0-9]{3}$', 
     'REGLA_ESPERADA': 'Debe cumplir exactamente: CTA#[Número] ABA#[3 dígitos]'}
]

# Columnas del reporte
COLUMNAS_REPORTE = [
    'VENDOR_NUMBER', 'VENDOR_NAME', 'VENDOR_SITE_CODE', 
    'CAMPO_AUDITADO', 'VALOR_ORACLE', 'REGLA_ESPERADA', 
    'TIPO_CONTROL', 'NIVEL_RIESGO', 'TIPO_ACCION'
]

# Nombres de archivos de salida
ARCHIVO_SALIDA_EXCEL = 'Reporte_Auditoria_EBS_Proveedores.xlsx'
ARCHIVO_SALIDA_HTML = 'Reporte_Auditoria_EBS_Proveedores.html'

# Niveles de riesgo
NIVEL_CRITICO = 'CRÍTICO'
NIVEL_ERROR = 'ERROR'
NIVEL_ADVERTENCIA = 'ADVERTENCIA'
NIVEL_OK = 'OK'

# Estados de sitio
SITE_STATUS_PUR = 'PUR'
SITE_STATUS_PAY = 'PAY'