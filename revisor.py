import pandas as pd
import re
import os
import tkinter as tk
from tkinter import filedialog

# Obtener directorio base del script para manejar rutas relativas de manera dinamica
DIRECTORIO_SCRIPT = os.path.dirname(os.path.abspath(__file__))
RUTA_PARAMETROS = os.path.join(DIRECTORIO_SCRIPT, 'Parámetros.xlsx')

def cargar_csv_con_autodetect(ruta_archivo, sep='\t'):
    """
    Carga un archivo CSV probando diferentes codificaciones para evitar errores
    de lectura comunes con las exportaciones de Oracle (UTF-16LE, UTF-8, Latin-1).
    """
    for enc in ['utf-16', 'utf-8', 'latin-1']:
        try:
            df = pd.read_csv(ruta_archivo, sep=sep, encoding=enc)
            if df.shape[1] > 1:
                return df
        except Exception:
            continue
    return pd.read_csv(ruta_archivo, sep=sep)

def generar_reporte_html(lista_excepciones, nombre_salida):
    """
    Genera un informe HTML autocontenido y con diseno premium con
    las desviaciones detectadas para facilitar su lectura en navegadores.
    """
    from datetime import datetime
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    filas = []
    for exc in lista_excepciones:
        riesgo = str(exc.get('NIVEL_RIESGO', '')).upper()
        if riesgo == 'CRÍTICO':
            badge_class = 'badge-critico'
        elif riesgo == 'ERROR':
            badge_class = 'badge-error'
        else:
            badge_class = 'badge-advertencia'
            
        fila = f"""
            <tr>
                <td><strong>{exc.get('VENDOR_NUMBER', '')}</strong></td>
                <td>{exc.get('VENDOR_NAME', '')}</td>
                <td><span class="site-code">{exc.get('VENDOR_SITE_CODE', '')}</span></td>
                <td><code>{exc.get('CAMPO_AUDITADO', '')}</code></td>
                <td><span class="value-oracle">{exc.get('VALOR_ORACLE', '')}</span></td>
                <td>{exc.get('REGLA_ESPERADA', '')}</td>
                <td>{exc.get('TIPO_CONTROL', '')}</td>
                <td><span class="badge {{badge_class}}">{riesgo}</span></td>
            </tr>"""
        filas.append(fila)
        
    filas_html = "\n".join(filas)
    
    html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de Auditoria de Proveedores - Oracle EBS</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f8fafc;
            color: #1e293b;
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 1300px;
            margin: 0 auto;
            background: #ffffff;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
            border: 1px solid #f1f5f9;
        }}
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #f1f5f9;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        h1 {{
            color: #0f172a;
            font-size: 26px;
            font-weight: 700;
            margin: 0;
        }}
        .summary-badge {{
            background-color: #f1f5f9;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
            color: #475569;
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 35px;
        }}
        .meta-card {{
            background: #f8fafc;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #f1f5f9;
        }}
        .meta-card-title {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            margin-bottom: 6px;
            font-weight: 600;
        }}
        .meta-card-value {{
            font-size: 20px;
            font-weight: 700;
            color: #0f172a;
        }}
        .table-responsive {{
            overflow-x: auto;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 13px;
        }}
        th {{
            background-color: #f1f5f9;
            color: #475569;
            font-weight: 600;
            padding: 14px 16px;
            border-bottom: 2px solid #e2e8f0;
        }}
        td {{
            padding: 14px 16px;
            border-bottom: 1px solid #f1f5f9;
            line-height: 1.5;
        }}
        tr:last-child td {{
            border-bottom: none;
        }}
        tr:hover {{
            background-color: #f8fafc;
        }}
        .site-code {{
            background-color: #f1f5f9;
            color: #334155;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 11px;
            font-weight: 500;
        }}
        code {{
            background-color: #fef2f2;
            color: #b91c1c;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 11px;
        }}
        .value-oracle {{
            color: #475569;
            font-style: italic;
        }}
        .badge {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 4px 8px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 11px;
            letter-spacing: 0.02em;
        }}
        .badge-critico {{
            background-color: #fef2f2;
            color: #991b1b;
            border: 1px solid #fee2e2;
        }}
        .badge-error {{
            background-color: #fff7ed;
            color: #c2410c;
            border: 1px solid #ffedd5;
        }}
        .badge-advertencia {{
            background-color: #fef3c7;
            color: #b45309;
            border: 1px solid #fde68a;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Auditoría de Proveedores Oracle EBS</h1>
            <div class="summary-badge">Reporte de Desviaciones</div>
        </header>
        
        <div class="meta-grid">
            <div class="meta-card">
                <div class="meta-card-title">Fecha de Auditoría</div>
                <div class="meta-card-value">{fecha_actual}</div>
            </div>
            <div class="meta-card">
                <div class="meta-card-title">Desviaciones Detectadas</div>
                <div class="meta-card-value" style="color: #ef4444;">{len(lista_excepciones)}</div>
            </div>
        </div>
        
        <div class="table-responsive">
            <table>
                <thead>
                    <tr>
                        <th>Proveedor No.</th>
                        <th>Nombre Proveedor</th>
                        <th>Sitio</th>
                        <th>Campo Auditado</th>
                        <th>Valor en Oracle</th>
                        <th>Regla Esperada</th>
                        <th>Tipo Control</th>
                        <th>Nivel Riesgo</th>
                    </tr>
                </thead>
                <tbody>
                    {filas_html}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""
    with open(nombre_salida, 'w', encoding='utf-8') as f:
        f.write(html_template)

def ejecutar_auditoria_ebs(archivo_header, archivo_paysite):
    """
    Carga las reglas de negocio de Parametros.xlsx, lee los datos de Oracle
    y genera un informe de auditoria con las desviaciones encontradas.
    """
    print("\nIniciando validacion de datos Oracle EBS...")
    
    if not os.path.exists(RUTA_PARAMETROS):
        print(f"Error: No se encontro el archivo de parametros en: {RUTA_PARAMETROS}")
        return
        
    print(f"Cargando parametros desde: {os.path.basename(RUTA_PARAMETROS)}")
    
    # 1. Carga de mapeo de paises (conversión de texto largo a codigo ISO)
    try:
        df_param_paises = pd.read_excel(RUTA_PARAMETROS, sheet_name='Geographic_Mapping')
        mapeo_paises = dict(zip(df_param_paises['PAIS_DFF_HEADER'], df_param_paises['CODIGO_ISO_ESPERADO']))
        print(f"Mapeo de paises cargado: {len(mapeo_paises)} registros.")
    except Exception as e:
        print(f"Advertencia al leer Geographic_Mapping: {e}")
        mapeo_paises = {
            'Republica de Panama': 'PA',
            'Canada': 'CA',
            'Spain': 'ES',
            'United States': 'US',
            'France': 'FR',
            'Germany': 'DE',
            'Chile': 'CL',
            'Sweden': 'SE'
        }

    # 2. Carga de reglas generales por tipo de proveedor (Hoja1)
    mapeo_reglas = {}
    try:
        df_rules = pd.read_excel(RUTA_PARAMETROS, sheet_name='Hoja1')
        for _, row in df_rules.iterrows():
            vtype = row['VENDOR_TYPE_LOOKUP_CODE']
            if pd.isna(vtype):
                continue
            vkey = str(vtype).strip().lower()
            if vkey == 'employee':
                vkey = 'employees'
            mapeo_reglas[vkey] = {
                'PAYMENT_PRIORITY': row.get('PAYMENT_PRIORITY'),
                'TERMS_ID': row.get('TERMS_ID'),
                'EXCLUDE_FREIGHT_FROM_DISCOUNT': row.get('EXCLUDE_FREIGHT_FROM_DISCOUNT'),
                'AUTO_CALCULATE_INTEREST_FLAG': row.get('AUTO_CALCULATE_INTEREST_FLAG')
            }
        print(f"Reglas de tipo de proveedor cargadas: {len(mapeo_reglas)} registros.")
    except Exception as e:
        print(f"Advertencia al leer Hoja1: {e}")
        mapeo_reglas = {
            'employees': {
                'PAYMENT_PRIORITY': 'Y', 'TERMS_ID': 'Y', 'EXCLUDE_FREIGHT_FROM_DISCOUNT': 'N', 'AUTO_CALCULATE_INTEREST_FLAG': 'N'
            },
            'claims': {
                'PAYMENT_PRIORITY': 'Y', 'TERMS_ID': 'Y', 'EXCLUDE_FREIGHT_FROM_DISCOUNT': 'N', 'AUTO_CALCULATE_INTEREST_FLAG': 'N'
            },
            'trust': {
                'PAYMENT_PRIORITY': 'Y', 'TERMS_ID': 'Y', 'EXCLUDE_FREIGHT_FROM_DISCOUNT': 'N', 'AUTO_CALCULATE_INTEREST_FLAG': 'N'
            },
            'miscellaneous services': {
                'PAYMENT_PRIORITY': 'Y', 'TERMS_ID': 'Y', 'EXCLUDE_FREIGHT_FROM_DISCOUNT': 'Y', 'AUTO_CALCULATE_INTEREST_FLAG': 'Y'
            }
        }

    # 3. Carga de reglas geograficas de sitios de pago (Geographic_Rules)
    geo_rules = []
    try:
        df_geo_rules = pd.read_excel(RUTA_PARAMETROS, sheet_name='Geographic_Rules')
        for _, row in df_geo_rules.iterrows():
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
            geo_rules.append({
                'COUNTRY_ISO': str(row['COUNTRY_ISO']).strip().upper(),
                'SITE_CODE_PATTERN': str(row['SITE_CODE_PATTERN']).strip().upper(),
                'ALLOWED_PRIORITIES': priorities,
                'ATTRIBUTE6_ESPERADO': str(row['ATTRIBUTE6_ESPERADO']).strip().upper()
            })
        print(f"Reglas geograficas cargadas: {len(geo_rules)} registros.")
    except Exception as e:
        print(f"Advertencia al leer Geographic_Rules: {e}")
        geo_rules = [
            {'COUNTRY_ISO': 'PA', 'SITE_CODE_PATTERN': 'ACH LOCAL*', 'ALLOWED_PRIORITIES': [99], 'ATTRIBUTE6_ESPERADO': 'OUR'},
            {'COUNTRY_ISO': 'PA', 'SITE_CODE_PATTERN': 'TRAMITE*', 'ALLOWED_PRIORITIES': [71, 73], 'ATTRIBUTE6_ESPERADO': 'OUR'},
            {'COUNTRY_ISO': 'US', 'SITE_CODE_PATTERN': 'ACH USA*', 'ALLOWED_PRIORITIES': [50], 'ATTRIBUTE6_ESPERADO': 'OUR'},
            {'COUNTRY_ISO': 'US', 'SITE_CODE_PATTERN': 'BANK TRANSFER*', 'ALLOWED_PRIORITIES': [50], 'ATTRIBUTE6_ESPERADO': 'BEN'},
            {'COUNTRY_ISO': 'DEFAULT', 'SITE_CODE_PATTERN': 'BANK TRANSFER*', 'ALLOWED_PRIORITIES': [50], 'ATTRIBUTE6_ESPERADO': 'BEN'}
        ]

    # 4. Carga de reglas de formato de direccion para bancos (Address_Format_Rules)
    format_rules = []
    try:
        df_format_rules = pd.read_excel(RUTA_PARAMETROS, sheet_name='Address_Format_Rules')
        for _, row in df_format_rules.iterrows():
            format_rules.append({
                'SITE_CODE': str(row['SITE_CODE']).strip().upper(),
                'COLUMN_NAME': str(row['COLUMN_NAME']).strip(),
                'REGEX_PATTERN': str(row['REGEX_PATTERN']).strip(),
                'REGLA_ESPERADA': str(row['REGLA_ESPERADA']).strip()
            })
        print(f"Reglas de formato bancario cargadas: {len(format_rules)} registros.")
    except Exception as e:
        print(f"Advertencia al leer Address_Format_Rules: {e}")
        format_rules = [
            {'SITE_CODE': 'ACH LOCAL', 'COLUMN_NAME': 'ADDRESS_LINE2', 'REGEX_PATTERN': r'^RUTA Y TRANSITO #[0-9]{9}$', 'REGLA_ESPERADA': 'Debe cumplir exactamente: RUTA Y TRANSITO #[9 dígitos]'},
            {'SITE_CODE': 'ACH LOCAL', 'COLUMN_NAME': 'ADDRESS_LINE3', 'REGEX_PATTERN': r'^CTA#[a-zA-Z0-9\-]+ ABA#[0-9]{3}$', 'REGLA_ESPERADA': 'Debe cumplir exactamente: CTA#[Número] ABA#[3 dígitos]'}
        ]

    # 5. Carga de Definiciones de Términos de Pago (Terms_Definitions)
    mapeo_terminos = {}
    try:
        df_terms_def = pd.read_excel(RUTA_PARAMETROS, sheet_name='Terms_Definitions')
        for _, row in df_terms_def.iterrows():
            tid = row.get('TERMS_ID')
            desc = row.get('DESCRIPCION')
            if pd.notna(tid) and pd.notna(desc):
                try:
                    mapeo_terminos[int(float(tid))] = str(desc).strip()
                except ValueError:
                    mapeo_terminos[str(tid).strip()] = str(desc).strip()
        print(f"Definiciones de terminos de pago cargadas: {len(mapeo_terminos)} registros.")
    except Exception:
        print("Aviso: No se cargo la pestaña opcional 'Terms_Definitions' o su formato es invalido.")

    # Carga de los archivos CSV exportados de Oracle
    try:
        df_header = cargar_csv_con_autodetect(archivo_header)
        df_paysite = cargar_csv_con_autodetect(archivo_paysite)
        print("Reportes de Oracle cargados correctamente.")
        print(f"Cabeceras: {os.path.basename(archivo_header)} ({len(df_header)} registros)")
        print(f"Sitios: {os.path.basename(archivo_paysite)} ({len(df_paysite)} registros)")
    except Exception as e:
        print(f"Error critico al cargar los reportes de Oracle: {e}")
        return

    lista_excepciones = []

    # Validacion cruzada entre cabeceras y sitios
    for vendor_id, sitios in df_paysite.groupby('VENDOR_ID'):
        header_row = df_header[df_header['VENDOR_ID'] == vendor_id]
        
        if header_row.empty:
            lista_excepciones.append({
                'VENDOR_NUMBER': sitios['VENDOR_NUMBER'].iloc[0],
                'VENDOR_NAME': sitios['VENDOR_NAME'].iloc[0],
                'VENDOR_SITE_CODE': 'GLOBAL',
                'CAMPO_AUDITADO': 'VENDOR_ID',
                'VALOR_ORACLE': str(vendor_id),
                'REGLA_ESPERADA': 'El sitio debe tener un registro padre en el Header',
                'TIPO_CONTROL': 'Integridad de Datos',
                'NIVEL_RIESGO': 'CRÍTICO'
            })
            continue

        v_number = header_row['VENDOR_NUMBER'].values[0]
        v_name = header_row['VENDOR_NAME'].values[0]
        v_type = header_row['VENDOR_TYPE_LOOKUP_CODE'].values[0]
        enabled_flag = header_row['ENABLED_FLAG'].values[0]
        interest_flag = header_row['AUTO_CALCULATE_INTEREST_FLAG'].values[0]
        pais_dff_texto = header_row['PAIS_DFF_ATT1'].values[0]
        header_priority = pd.to_numeric(header_row['PAYMENT_PRIORITY'].values[0], errors='coerce')
        
        # Validar que el tipo de proveedor no este vacio
        if pd.isna(v_type) or str(v_type).strip() == '' or str(v_type).strip().lower() == 'nan':
            lista_excepciones.append({
                'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': 'HEADER',
                'CAMPO_AUDITADO': 'VENDOR_TYPE_LOOKUP_CODE', 'VALOR_ORACLE': str(v_type),
                'REGLA_ESPERADA': 'El tipo de proveedor (VENDOR_TYPE_LOOKUP_CODE) no debe estar en blanco',
                'TIPO_CONTROL': 'Obligatoriedad', 'NIVEL_RIESGO': 'CRÍTICO'
            })

        pais_dff_iso = mapeo_paises.get(pais_dff_texto, 'DESCONOCIDO')

        # Control geografico de prioridad en cabecera
        es_local_header = (pais_dff_texto == 'Republica de Panama' or pais_dff_iso == 'PA')
        if es_local_header:
            if header_priority not in [99, 71, 73]:
                lista_excepciones.append({
                    'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': 'HEADER',
                    'CAMPO_AUDITADO': 'PAYMENT_PRIORITY', 'VALOR_ORACLE': str(header_priority),
                    'REGLA_ESPERADA': 'Para Panamá los proveedores locales deben tener prioridad 99, 71 o 73',
                    'TIPO_CONTROL': 'Paramétrico Geográfico (Header)', 'NIVEL_RIESGO': 'ERROR'
                })
        else:
            if header_priority != 50:
                lista_excepciones.append({
                    'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': 'HEADER',
                    'CAMPO_AUDITADO': 'PAYMENT_PRIORITY', 'VALOR_ORACLE': str(header_priority),
                    'REGLA_ESPERADA': 'Para proveedores extranjeros la prioridad debe ser 50',
                    'TIPO_CONTROL': 'Paramétrico Geográfico (Header)', 'NIVEL_RIESGO': 'ERROR'
                })

        # Aplicacion de reglas generales por tipo de proveedor
        vkey_buscar = str(v_type).strip().lower()
        regla = mapeo_reglas.get(vkey_buscar)
        
        if not regla:
            if vkey_buscar.endswith('s'):
                regla = mapeo_reglas.get(vkey_buscar[:-1])
            else:
                regla = mapeo_reglas.get(vkey_buscar + 's')

        if regla:
            ref_interest = regla.get('AUTO_CALCULATE_INTEREST_FLAG')
            if pd.notna(ref_interest):
                if interest_flag != ref_interest:
                    riesgo = 'ADVERTENCIA' if vkey_buscar == 'trust' else 'ERROR'
                    lista_excepciones.append({
                        'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': 'HEADER',
                        'CAMPO_AUDITADO': 'AUTO_CALCULATE_INTEREST_FLAG', 'VALOR_ORACLE': str(interest_flag),
                        'REGLA_ESPERADA': f'Debe ser {ref_interest} para {v_type} según la matriz de parámetros',
                        'TIPO_CONTROL': 'Paramétrico (Invoice Mgt)', 'NIVEL_RIESGO': riesgo
                    })

            ref_freight = regla.get('EXCLUDE_FREIGHT_FROM_DISCOUNT')
            if pd.notna(ref_freight):
                actual_freight = header_row['EXCLUDE_FREIGHT_FROM_DISCOUNT'].values[0]
                if actual_freight != ref_freight:
                    lista_excepciones.append({
                        'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': 'HEADER',
                        'CAMPO_AUDITADO': 'EXCLUDE_FREIGHT_FROM_DISCOUNT', 'VALOR_ORACLE': str(actual_freight),
                        'REGLA_ESPERADA': f'Debe ser {ref_freight} para {v_type} según la matriz de parámetros',
                        'TIPO_CONTROL': 'Paramétrico (Invoice Mgt)', 'NIVEL_RIESGO': 'ERROR'
                    })

            ref_terms = regla.get('TERMS_ID')
            if ref_terms == 'Y':
                actual_terms = header_row['TERMS_ID'].values[0]
                if pd.isna(actual_terms) or str(actual_terms).strip() == '' or str(actual_terms).strip().lower() == 'nan':
                    lista_excepciones.append({
                        'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': 'HEADER',
                        'CAMPO_AUDITADO': 'TERMS_ID', 'VALOR_ORACLE': str(actual_terms),
                        'REGLA_ESPERADA': f'Requerido (Y) para {v_type} según la matriz de parámetros',
                        'TIPO_CONTROL': 'Paramétrico (Invoice Mgt)', 'NIVEL_RIESGO': 'ERROR'
                    })

            ref_priority = regla.get('PAYMENT_PRIORITY')
            if ref_priority == 'Y':
                if pd.isna(header_priority) or str(header_priority).strip() == '' or str(header_priority).strip().lower() == 'nan':
                    lista_excepciones.append({
                        'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': 'HEADER',
                        'CAMPO_AUDITADO': 'PAYMENT_PRIORITY', 'VALOR_ORACLE': str(header_priority),
                        'REGLA_ESPERADA': f'Requerido (Y) para {v_type} según la matriz de parámetros',
                        'TIPO_CONTROL': 'Paramétrico (Invoice Mgt)', 'NIVEL_RIESGO': 'ERROR'
                    })

        # Consistencia de paises
        pais_pur_iso = sitios[sitios['SITE_STATUS'] == 'PUR']['COUNTRY'].values
        pais_pay_iso = sitios[sitios['SITE_STATUS'] == 'PAY']['COUNTRY'].values
        
        pais_pur_iso = pais_pur_iso[0] if len(pais_pur_iso) > 0 else None
        pais_pay_iso = pais_pay_iso[0] if len(pais_pay_iso) > 0 else None

        if v_type in ['Miscellaneous Services', 'Trust'] and pais_pur_iso:
            if pais_dff_iso != pais_pur_iso:
                lista_excepciones.append({
                    'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': 'PUR Site',
                    'CAMPO_AUDITADO': 'COUNTRY vs PAIS_DFF', 'VALOR_ORACLE': f'PUR={pais_pur_iso}, DFF_MATRIZ={pais_dff_iso}',
                    'REGLA_ESPERADA': 'El país del sitio de compras (PUR) debe coincidir con el DFF traducido',
                    'TIPO_CONTROL': 'Consistencia de Valores', 'NIVEL_RIESGO': 'ERROR'
                })
        
        elif v_type in ['Employees', 'Claims'] and pais_pay_iso:
            if pais_dff_iso != pais_pay_iso:
                lista_excepciones.append({
                    'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': 'PAY Site',
                    'CAMPO_AUDITADO': 'COUNTRY vs PAIS_DFF', 'VALOR_ORACLE': f'PAY={pais_pay_iso}, DFF_MATRIZ={pais_dff_iso}',
                    'REGLA_ESPERADA': 'El país del sitio de pagos (PAY) debe coincidir con el DFF traducido',
                    'TIPO_CONTROL': 'Consistencia de Valores', 'NIVEL_RIESGO': 'ERROR'
                })

        # Validaciones especificas a nivel de sitios
        for _, fila_sitio in sitios.iterrows():
            s_code = fila_sitio['VENDOR_SITE_CODE']
            s_code_upper = str(s_code).strip().upper()
            s_country = fila_sitio['COUNTRY']
            s_priority = pd.to_numeric(fila_sitio['PAYMENT_PRIORITY'], errors='coerce')
            s_inactive_date = fila_sitio['INACTIVE_DATE']
            addr2 = str(fila_sitio['ADDRESS_LINE2']).strip()
            addr3 = str(fila_sitio['ADDRESS_LINE3']).strip()

            # Control de Consistencia: Términos de Pago (Header vs Sitio)
            h_terms = header_row['TERMS_ID'].values[0]
            s_terms = fila_sitio['TERMS_ID']
            if pd.notna(h_terms) and pd.notna(s_terms):
                try:
                    h_terms_val = int(float(h_terms))
                    s_terms_val = int(float(s_terms))
                    if h_terms_val != s_terms_val:
                        h_desc = mapeo_terminos.get(h_terms_val, str(h_terms_val))
                        s_desc = mapeo_terminos.get(s_terms_val, str(s_terms_val))
                        lista_excepciones.append({
                            'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': s_code,
                            'CAMPO_AUDITADO': 'TERMS_ID (Consistencia)', 
                            'VALOR_ORACLE': f'Sitio={s_desc}',
                            'REGLA_ESPERADA': f'Debe coincidir con la cabecera ({h_desc})',
                            'TIPO_CONTROL': 'Consistencia de Valores', 'NIVEL_RIESGO': 'ERROR'
                        })
                except Exception:
                    if str(h_terms).strip() != str(s_terms).strip():
                        h_desc = mapeo_terminos.get(str(h_terms).strip(), str(h_terms))
                        s_desc = mapeo_terminos.get(str(s_terms).strip(), str(s_terms))
                        lista_excepciones.append({
                            'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': s_code,
                            'CAMPO_AUDITADO': 'TERMS_ID (Consistencia)', 
                            'VALOR_ORACLE': f'Sitio={s_desc}',
                            'REGLA_ESPERADA': f'Debe coincidir con la cabecera ({h_desc})',
                            'TIPO_CONTROL': 'Consistencia de Valores', 'NIVEL_RIESGO': 'ERROR'
                        })

            # Control de Consistencia: Prioridad de Pago (Header vs Sitio)
            if pd.notna(header_priority) and pd.notna(s_priority):
                try:
                    h_prio_val = int(float(header_priority))
                    s_prio_val = int(float(s_priority))
                    if h_prio_val != s_prio_val:
                        lista_excepciones.append({
                            'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': s_code,
                            'CAMPO_AUDITADO': 'PAYMENT_PRIORITY (Consistencia)', 
                            'VALOR_ORACLE': f'Sitio={s_prio_val}',
                            'REGLA_ESPERADA': f'Debe coincidir con la cabecera ({h_prio_val})',
                            'TIPO_CONTROL': 'Consistencia de Valores', 'NIVEL_RIESGO': 'ERROR'
                        })
                except Exception:
                    if str(header_priority).strip() != str(s_priority).strip():
                        lista_excepciones.append({
                            'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': s_code,
                            'CAMPO_AUDITADO': 'PAYMENT_PRIORITY (Consistencia)', 
                            'VALOR_ORACLE': f'Sitio={s_priority}',
                            'REGLA_ESPERADA': f'Debe coincidir con la cabecera ({header_priority})',
                            'TIPO_CONTROL': 'Consistencia de Valores', 'NIVEL_RIESGO': 'ERROR'
                        })

            if enabled_flag == 'Y' and not pd.isna(s_inactive_date):
                lista_excepciones.append({
                    'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': s_code,
                    'CAMPO_AUDITADO': 'INACTIVE_DATE vs ENABLED_FLAG', 'VALOR_ORACLE': f'Inactivo el {s_inactive_date}',
                    'REGLA_ESPERADA': 'Si el proveedor global está habilitado, advierte si el sitio individual tiene fecha de baja',
                    'TIPO_CONTROL': 'Consistencia de Valores', 'NIVEL_RIESGO': 'ADVERTENCIA'
                })
            
            # Para los sitios de compras (PUR), la comision bancaria (ATTRIBUTE6) no es obligatoria y se ignora.
            # Solo los sitios de pago (PAY) requieren validar la prioridad y comision (OUR/BEN).
            s_status = fila_sitio['SITE_STATUS']
            if s_status == 'PAY':
                s_code_upper = str(s_code).strip().upper()
                s_country_upper = str(s_country).strip().upper()
                attr6 = str(fila_sitio['ATTRIBUTE6']).strip()
                attr6_upper = attr6.upper()

                reglas_pais = [r for r in geo_rules if r['COUNTRY_ISO'] == s_country_upper]
                if not reglas_pais:
                    reglas_pais = [r for r in geo_rules if r['COUNTRY_ISO'] in ['DEFAULT', 'OTRO']]

                regla_coincidente = None
                for r in reglas_pais:
                    patron = r['SITE_CODE_PATTERN']
                    if patron.endswith('*'):
                        patron_clean = patron[:-1]
                        if s_code_upper.startswith(patron_clean):
                            regla_coincidente = r
                            break
                    else:
                        if patron in s_code_upper:
                            regla_coincidente = r
                            break

                if regla_coincidente:
                    allowed_prio = regla_coincidente['ALLOWED_PRIORITIES']
                    if allowed_prio:
                        if s_priority not in allowed_prio:
                            prio_str = ", ".join(map(str, allowed_prio))
                            lista_excepciones.append({
                                'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': s_code,
                                'CAMPO_AUDITADO': 'PAYMENT_PRIORITY', 'VALOR_ORACLE': str(s_priority),
                                'REGLA_ESPERADA': f'Para {s_country}, la prioridad del sitio de pago debe ser {prio_str}',
                                'TIPO_CONTROL': 'Paramétrico Geográfico (Site)', 'NIVEL_RIESGO': 'ERROR'
                            })

                    expected_attr6 = regla_coincidente['ATTRIBUTE6_ESPERADO']
                    if expected_attr6:
                        if pd.isna(fila_sitio['ATTRIBUTE6']) or attr6 == '' or attr6.lower() == 'nan':
                            lista_excepciones.append({
                                'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': s_code,
                                'CAMPO_AUDITADO': 'ATTRIBUTE6', 'VALOR_ORACLE': str(fila_sitio['ATTRIBUTE6']),
                                'REGLA_ESPERADA': 'El campo de comisión bancaria (ATTRIBUTE6) no debe estar en blanco para sitios de pago (PAY)',
                                'TIPO_CONTROL': 'Obligatoriedad', 'NIVEL_RIESGO': 'ERROR'
                            })
                        elif attr6_upper != expected_attr6:
                            lista_excepciones.append({
                                'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': s_code,
                                'CAMPO_AUDITADO': 'ATTRIBUTE6', 'VALOR_ORACLE': str(fila_sitio['ATTRIBUTE6']),
                                'REGLA_ESPERADA': f'Para el sitio {s_code} en {s_country}, la comisión bancaria (ATTRIBUTE6) debe ser {expected_attr6}',
                                'TIPO_CONTROL': 'Paramétrico Geográfico (Site)', 'NIVEL_RIESGO': 'ERROR'
                            })
                else:
                    patrones_permitidos = [r['SITE_CODE_PATTERN'] for r in reglas_pais]
                    patrones_str = " o ".join(patrones_permitidos)
                    lista_excepciones.append({
                        'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': s_code,
                        'CAMPO_AUDITADO': 'VENDOR_SITE_CODE', 'VALOR_ORACLE': s_code,
                        'REGLA_ESPERADA': f'Para {s_country}, el sitio de pago debe coincidir con el patrón: {patrones_str}',
                        'TIPO_CONTROL': 'Paramétrico Geográfico (Site)', 'NIVEL_RIESGO': 'ERROR'
                    })

            for rule in format_rules:
                rule_site = rule['SITE_CODE']
                if s_code_upper.startswith(rule_site) or rule_site in s_code_upper:
                    col_name = rule['COLUMN_NAME']
                    val_oracle = str(fila_sitio[col_name]).strip()
                    if val_oracle != 'nan' and val_oracle != '':
                        if not re.match(rule['REGEX_PATTERN'], val_oracle):
                            lista_excepciones.append({
                                'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': s_code,
                                'CAMPO_AUDITADO': f'{col_name} (Banca)', 'VALOR_ORACLE': val_oracle,
                                'REGLA_ESPERADA': rule['REGLA_ESPERADA'],
                                'TIPO_CONTROL': 'Formato Texto (Banking Retail)', 'NIVEL_RIESGO': 'ERROR'
                            })

    # Escritura del archivo de resultados
    df_resultado = pd.DataFrame(lista_excepciones)
    
    if not df_resultado.empty:
        nombre_salida_excel = 'Reporte_Auditoria_EBS_Proveedores.xlsx'
        nombre_salida_html = 'Reporte_Auditoria_EBS_Proveedores.html'
        
        # Generar reporte Excel
        df_resultado.to_excel(nombre_salida_excel, index=False)
        
        # Generar reporte HTML
        generar_reporte_html(lista_excepciones, nombre_salida_html)
        
        print("\nProceso finalizado.")
        print(f"Se detectaron {len(df_resultado)} desviaciones o alertas en los datos.")
        print(f"Reporte Excel generado en: {os.path.abspath(nombre_salida_excel)}")
        print(f"Reporte HTML generado en: {os.path.abspath(nombre_salida_html)}")
    else:
        print("\nProceso finalizado.")
        print("No se encontraron desviaciones en los datos analizados.")

if __name__ == "__main__":
    import sys
    
    archivo_def_header = 'ExampleData/AP New or Updated Suppliers - Header View.csv'
    archivo_def_site = 'ExampleData/AP New or Updated Suppliers - PaySite View.csv'

    if len(sys.argv) >= 3:
        archivo_header_seleccionado = sys.argv[1]
        archivo_site_seleccionado = sys.argv[2]
        ejecutar_auditoria_ebs(archivo_header_seleccionado, archivo_site_seleccionado)
    else:
        if not os.environ.get('DISPLAY') and os.path.exists(archivo_def_header) and os.path.exists(archivo_def_site):
            print("Detectado entorno sin interfaz grafica. Cargando archivos por defecto de ExampleData...")
            ejecutar_auditoria_ebs(archivo_def_header, archivo_def_site)
        else:
            try:
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)

                print("Interactua con las ventanas emergentes para seleccionar reportes...")

                archivo_header_seleccionado = filedialog.askopenfilename(
                    title="1. Seleccionar Reporte de HEADER de Oracle (Cabeceras)",
                    filetypes=[("Archivos CSV", "*.csv"), ("Archivos de Texto", "*.txt"), ("Todos los archivos", "*.*")]
                )

                if not archivo_header_seleccionado:
                    print("Proceso cancelado: No seleccionaste el archivo de Encabezados.")
                else:
                    archivo_site_seleccionado = filedialog.askopenfilename(
                        title="2. Seleccionar Reporte de SITES de Oracle (Sitios)",
                        filetypes=[("Archivos CSV", "*.csv"), ("Archivos de Texto", "*.txt"), ("Todos los archivos", "*.*")]
                    )
                    
                    if not archivo_site_seleccionado:
                        print("Proceso cancelado: No seleccionaste el archivo de Sitios.")
                    else:
                        ejecutar_auditoria_ebs(archivo_header_seleccionado, archivo_site_seleccionado)
            except Exception as e:
                if os.path.exists(archivo_def_header) and os.path.exists(archivo_def_site):
                    print(f"Fallo de interfaz grafica ({e}). Cargando archivos por defecto...")
                    ejecutar_auditoria_ebs(archivo_def_header, archivo_def_site)
                else:
                    print(f"Error y no se encontraron archivos por defecto: {e}")