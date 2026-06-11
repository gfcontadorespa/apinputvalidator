"""
Módulo de lógica de validación para auditoría de proveedores Oracle EBS
Contiene todas las reglas de negocio y validaciones cruzadas
"""
import re
import pandas as pd
from config import NIVEL_CRITICO, NIVEL_ERROR, NIVEL_ADVERTENCIA


class AuditoriaValidator:
    """Clase encargada de ejecutar todas las validaciones de auditoria"""
    
    def __init__(self, df_header, df_paysite, parametros):
        """
        Inicializa el validador
        
        Args:
            df_header: DataFrame con datos de cabeceras
            df_paysite: DataFrame con datos de sitios
            parametros: Dict con mapeos y reglas
        """
        self.df_header = df_header
        self.df_paysite = df_paysite
        self.mapeo_paises = parametros.get('mapeo_paises', {})
        self.mapeo_reglas = parametros.get('mapeo_reglas', {})
        self.geo_rules = parametros.get('geo_rules', [])
        self.format_rules = parametros.get('format_rules', [])
        self.mapeo_terminos = parametros.get('mapeo_terminos', {})
        
        # Pre-indexar reglas geograficas por pais (O(1) en vez de O(n))
        self.geo_rules_por_pais = {}
        for r in self.geo_rules:
            pais = r['COUNTRY_ISO']
            if pais not in self.geo_rules_por_pais:
                self.geo_rules_por_pais[pais] = []
            self.geo_rules_por_pais[pais].append(r)
        
        # Pre-indexar sitios por VENDOR_ID (evita filtrar DataFrame en cada iteracion)
        self.paysite_por_vendor = {
            vid: grupo for vid, grupo in self.df_paysite.groupby('VENDOR_ID')
        } if not self.df_paysite.empty else {}
        
        self.lista_excepciones = []
        self.lista_correctos = []
    
    def ejecutar_auditoria(self):
        """
        Ejecuta la auditoria completa
        
        Returns:
            tuple: (lista_excepciones, lista_correctos)
        """
        print("\n▶ Iniciando validaciones...")
        
        # Excluir sitios con INACTIVE_DATE ya vencida (no se auditan)
        hoy = pd.Timestamp.now().normalize()
        if 'INACTIVE_DATE' in self.df_paysite.columns:
            inactive = pd.to_datetime(self.df_paysite['INACTIVE_DATE'], errors='coerce')
            mask_activos = inactive.isna() | (inactive > hoy)
            sitios_excluidos = (~mask_activos).sum()
            self.df_paysite_activo = self.df_paysite[mask_activos].copy()
            if sitios_excluidos > 0:
                print(f"  ↻ Sitios excluidos (INACTIVE_DATE vencido): {sitios_excluidos}")
            # Actualizar índice con datos filtrados
            self.paysite_por_vendor = {
                vid: grupo for vid, grupo in self.df_paysite_activo.groupby('VENDOR_ID')
            } if not self.df_paysite_activo.empty else {}
        else:
            self.df_paysite_activo = self.df_paysite
        
        # Validación cruzada entre cabeceras y sitios
        # Nota: No se valida PaySite sin Header porque Oracle EBS mantiene
        # integridad referencial a nivel BD (FK). Un PaySite siempre tiene
        # su Header correspondiente. Si por alguna razón no existe (ej.
        # exportación parcial), se omite la validación de ese vendor.
        for vendor_id, sitios in self.df_paysite_activo.groupby('VENDOR_ID'):
            header_row = self.df_header[self.df_header['VENDOR_ID'] == vendor_id]
            
            if header_row.empty:
                continue
            
            # Extraer datos del header
            v_number = header_row['VENDOR_NUMBER'].values[0]
            v_name = header_row['VENDOR_NAME'].values[0]
            v_type = header_row['VENDOR_TYPE_LOOKUP_CODE'].values[0]
            enabled_flag = header_row['ENABLED_FLAG'].values[0]
            interest_flag = header_row['AUTO_CALCULATE_INTEREST_FLAG'].values[0]
            pais_dff_texto = header_row['PAIS_DFF_ATT1'].values[0]
            header_priority = pd.to_numeric(header_row['PAYMENT_PRIORITY'].values[0], errors='coerce')
            
            # Validaciones a nivel de cabecera
            self._validar_header(header_row, v_number, v_name, v_type, 
                                pais_dff_texto, header_priority, enabled_flag, 
                                interest_flag)
            
            # Validaciones a nivel de sitios
            self._validar_sitios(sitios, header_row, v_number, v_name, v_type,
                                pais_dff_texto, header_priority, enabled_flag)
        
        # Validar headers creados (LAST_ACTION_VENDOR = C) que no tengan sitios
        self._validar_headers_creados_sin_sitios()
        
        # Generar lista de correctos
        self._generar_lista_correctos()
        
        print(f"✓ Validaciones completadas")
        print(f"  Excepciones: {len(self.lista_excepciones)}")
        print(f"  Correctos: {len(self.lista_correctos)}")
        
        return self.lista_excepciones, self.lista_correctos
    
    def _validar_headers_creados_sin_sitios(self):
        """
        Valida que los headers creados (LAST_ACTION_VENDOR = C) tengan
        los sitios esperados segun su tipo de proveedor:
          - Employee: al menos 1 sitio (funciona como PUR y PAY)
          - Otros tipos: al menos 1 sitio PUR y 1 sitio PAY
        """
        if 'LAST_ACTION_VENDOR' not in self.df_header.columns:
            return
        
        headers_creados = self.df_header[self.df_header['LAST_ACTION_VENDOR'] == 'C']
        
        for _, header_row in headers_creados.iterrows():
            vendor_id = header_row['VENDOR_ID']
            v_type = str(header_row['VENDOR_TYPE_LOOKUP_CODE']).strip()
            v_type_lower = v_type.lower()
            
            sitios = self.paysite_por_vendor.get(vendor_id, pd.DataFrame())
            
            if sitios.empty:
                # Sin ningun sitio - aplica para todos los tipos
                self._agregar_excepcion({
                    'VENDOR_NUMBER': header_row['VENDOR_NUMBER'],
                    'VENDOR_NAME': header_row['VENDOR_NAME'],
                    'VENDOR_SITE_CODE': 'HEADER',
                    'CAMPO_AUDITADO': 'VENDOR_SITE_CODE (Integridad)',
                    'VALOR_ORACLE': 'Sin sitios asignados',
                    'REGLA_ESPERADA': f'Un proveedor {v_type} creado (LAST_ACTION_VENDOR=C) deberia tener al menos un sitio en PaySite',
                    'TIPO_CONTROL': 'Consistencia de Datos',
                    'NIVEL_RIESGO': NIVEL_ADVERTENCIA
                })
                continue
            
            # Employee: un solo sitio que funciona como PUR y PAY
            if v_type_lower in ['employee', 'employees']:
                continue  # Ya tiene al menos 1 sitio, es suficiente
            
            # Otros tipos: esperar al menos 1 PUR + 1 PAY
            tiene_pur = (sitios['SITE_STATUS'] == 'PUR').any()
            tiene_pay = (sitios['SITE_STATUS'] == 'PAY').any()
            
            if not tiene_pur:
                self._agregar_excepcion({
                    'VENDOR_NUMBER': header_row['VENDOR_NUMBER'],
                    'VENDOR_NAME': header_row['VENDOR_NAME'],
                    'VENDOR_SITE_CODE': 'HEADER',
                    'CAMPO_AUDITADO': 'SITE_STATUS (PUR)',
                    'VALOR_ORACLE': 'Sin sitio de compras',
                    'REGLA_ESPERADA': f'Un proveedor {v_type} creado (LAST_ACTION_VENDOR=C) deberia tener al menos un sitio PUR',
                    'TIPO_CONTROL': 'Consistencia de Datos',
                    'NIVEL_RIESGO': NIVEL_ADVERTENCIA
                })
            
            if not tiene_pay:
                self._agregar_excepcion({
                    'VENDOR_NUMBER': header_row['VENDOR_NUMBER'],
                    'VENDOR_NAME': header_row['VENDOR_NAME'],
                    'VENDOR_SITE_CODE': 'HEADER',
                    'CAMPO_AUDITADO': 'SITE_STATUS (PAY)',
                    'VALOR_ORACLE': 'Sin sitio de pagos',
                    'REGLA_ESPERADA': f'Un proveedor {v_type} creado (LAST_ACTION_VENDOR=C) deberia tener al menos un sitio PAY',
                    'TIPO_CONTROL': 'Consistencia de Datos',
                    'NIVEL_RIESGO': NIVEL_ADVERTENCIA
                })
    
    def _validar_header(self, header_row, v_number, v_name, v_type, 
                       pais_dff_texto, header_priority, enabled_flag, interest_flag):
        """Validaciones a nivel de cabecera"""
        
        # Validar tipo de proveedor no vacío
        if pd.isna(v_type) or str(v_type).strip() == '' or str(v_type).strip().lower() == 'nan':
            self._agregar_excepcion({
                'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': 'HEADER',
                'CAMPO_AUDITADO': 'VENDOR_TYPE_LOOKUP_CODE', 'VALOR_ORACLE': str(v_type),
                'REGLA_ESPERADA': 'El tipo de proveedor (VENDOR_TYPE_LOOKUP_CODE) no debe estar en blanco',
                'TIPO_CONTROL': 'Obligatoriedad', 'NIVEL_RIESGO': NIVEL_CRITICO
            })
        
        pais_dff_iso = self.mapeo_paises.get(pais_dff_texto, 'DESCONOCIDO')
        
        # Control geográfico de prioridad
        es_local_header = (pais_dff_texto == 'Republica de Panama' or pais_dff_iso == 'PA')
        if es_local_header:
            if header_priority not in [99, 71, 73]:
                self._agregar_excepcion({
                    'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': 'HEADER',
                    'CAMPO_AUDITADO': 'PAYMENT_PRIORITY', 'VALOR_ORACLE': str(header_priority),
                    'REGLA_ESPERADA': 'Para Panamá los proveedores locales deben tener prioridad 99, 71 o 73',
                    'TIPO_CONTROL': 'Paramétrico Geográfico (Header)', 'NIVEL_RIESGO': NIVEL_ERROR
                })
        else:
            if header_priority != 50:
                self._agregar_excepcion({
                    'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': 'HEADER',
                    'CAMPO_AUDITADO': 'PAYMENT_PRIORITY', 'VALOR_ORACLE': str(header_priority),
                    'REGLA_ESPERADA': 'Para proveedores extranjeros la prioridad debe ser 50',
                    'TIPO_CONTROL': 'Paramétrico Geográfico (Header)', 'NIVEL_RIESGO': NIVEL_ERROR
                })
        
        # Aplicar reglas generales por tipo de proveedor
        self._aplicar_reglas_vendor_type(header_row, v_number, v_name, v_type, 
                                        interest_flag)
    
    def _aplicar_reglas_vendor_type(self, header_row, v_number, v_name, v_type, interest_flag):
        """Aplica reglas según el tipo de proveedor"""
        
        vkey_buscar = str(v_type).strip().lower()
        regla = self.mapeo_reglas.get(vkey_buscar)
        
        if not regla:
            if vkey_buscar.endswith('s'):
                regla = self.mapeo_reglas.get(vkey_buscar[:-1])
            else:
                regla = self.mapeo_reglas.get(vkey_buscar + 's')
        
        if not regla:
            return
        
        # Validar AUTO_CALCULATE_INTEREST_FLAG
        ref_interest = regla.get('AUTO_CALCULATE_INTEREST_FLAG')
        if pd.notna(ref_interest):
            if interest_flag != ref_interest:
                riesgo = NIVEL_ADVERTENCIA if vkey_buscar == 'trust' else NIVEL_ERROR
                self._agregar_excepcion({
                    'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': 'HEADER',
                    'CAMPO_AUDITADO': 'AUTO_CALCULATE_INTEREST_FLAG', 'VALOR_ORACLE': str(interest_flag),
                    'REGLA_ESPERADA': f'Debe ser {ref_interest} para {v_type} según la matriz de parámetros',
                    'TIPO_CONTROL': 'Paramétrico (Invoice Mgt)', 'NIVEL_RIESGO': riesgo
                })
        
        # Validar EXCLUDE_FREIGHT_FROM_DISCOUNT
        ref_freight = regla.get('EXCLUDE_FREIGHT_FROM_DISCOUNT')
        if pd.notna(ref_freight):
            actual_freight = header_row['EXCLUDE_FREIGHT_FROM_DISCOUNT'].values[0]
            if actual_freight != ref_freight:
                self._agregar_excepcion({
                    'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': 'HEADER',
                    'CAMPO_AUDITADO': 'EXCLUDE_FREIGHT_FROM_DISCOUNT', 'VALOR_ORACLE': str(actual_freight),
                    'REGLA_ESPERADA': f'Debe ser {ref_freight} para {v_type} según la matriz de parámetros',
                    'TIPO_CONTROL': 'Paramétrico (Invoice Mgt)', 'NIVEL_RIESGO': NIVEL_ERROR
                })
        
        # Validar TERMS_ID requerido
        ref_terms = regla.get('TERMS_ID')
        if ref_terms == 'Y':
            actual_terms = header_row['TERMS_ID'].values[0]
            if pd.isna(actual_terms) or str(actual_terms).strip() == '' or str(actual_terms).strip().lower() == 'nan':
                self._agregar_excepcion({
                    'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': 'HEADER',
                    'CAMPO_AUDITADO': 'TERMS_ID', 'VALOR_ORACLE': str(actual_terms),
                    'REGLA_ESPERADA': f'Requerido (Y) para {v_type} según la matriz de parámetros',
                    'TIPO_CONTROL': 'Paramétrico (Invoice Mgt)', 'NIVEL_RIESGO': NIVEL_ERROR
                })
        
        # Validar PAYMENT_PRIORITY requerido
        ref_priority = regla.get('PAYMENT_PRIORITY')
        if ref_priority == 'Y':
            if pd.isna(header_row['PAYMENT_PRIORITY'].values[0]):
                self._agregar_excepcion({
                    'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': 'HEADER',
                    'CAMPO_AUDITADO': 'PAYMENT_PRIORITY', 'VALOR_ORACLE': 'N/A',
                    'REGLA_ESPERADA': f'Requerido (Y) para {v_type} según la matriz de parámetros',
                    'TIPO_CONTROL': 'Paramétrico (Invoice Mgt)', 'NIVEL_RIESGO': NIVEL_ERROR
                })
        
        # Validar HEADER_END_DATE_ACTIVE requerido
        ref_end_date = regla.get('HEADER_END_DATE_ACTIVE')
        if ref_end_date == 'Y':
            actual_end_date = header_row['HEADER_END_DATE_ACTIVE'].values[0]
            if pd.isna(actual_end_date) or str(actual_end_date).strip() == '':
                self._agregar_excepcion({
                    'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': 'HEADER',
                    'CAMPO_AUDITADO': 'HEADER_END_DATE_ACTIVE', 'VALOR_ORACLE': str(actual_end_date),
                    'REGLA_ESPERADA': f'Requerido (Y) para {v_type} según la matriz de parámetros',
                    'TIPO_CONTROL': 'Paramétrico (Invoice Mgt)', 'NIVEL_RIESGO': NIVEL_ERROR
                })
    
    def _validar_sitios(self, sitios, header_row, v_number, v_name, v_type,
                       pais_dff_texto, header_priority, enabled_flag):
        """Validaciones a nivel de sitios"""
        
        pais_dff_iso = self.mapeo_paises.get(pais_dff_texto, 'DESCONOCIDO')
        
        # Consistencia de países
        pais_pur_iso = sitios[sitios['SITE_STATUS'] == 'PUR']['COUNTRY'].values
        pais_pay_iso = sitios[sitios['SITE_STATUS'] == 'PAY']['COUNTRY'].values
        
        pais_pur_iso = pais_pur_iso[0] if len(pais_pur_iso) > 0 else None
        pais_pay_iso = pais_pay_iso[0] if len(pais_pay_iso) > 0 else None
        
        if v_type in ['Miscellaneous Services', 'Trust'] and pais_pur_iso:
            if pais_dff_iso != pais_pur_iso:
                self._agregar_excepcion({
                    'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': 'PUR Site',
                    'CAMPO_AUDITADO': 'COUNTRY vs PAIS_DFF', 
                    'VALOR_ORACLE': f'PUR={pais_pur_iso}, DFF_MATRIZ={pais_dff_iso}',
                    'REGLA_ESPERADA': 'El país del sitio de compras (PUR) debe coincidir con el DFF traducido',
                    'TIPO_CONTROL': 'Consistencia de Valores', 'NIVEL_RIESGO': NIVEL_ADVERTENCIA
                })
        
        elif v_type in ['Employees', 'Claims'] and pais_pay_iso:
            if pais_dff_iso != pais_pay_iso:
                self._agregar_excepcion({
                    'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': 'PAY Site',
                    'CAMPO_AUDITADO': 'COUNTRY vs PAIS_DFF', 
                    'VALOR_ORACLE': f'PAY={pais_pay_iso}, DFF_MATRIZ={pais_dff_iso}',
                    'REGLA_ESPERADA': 'El país del sitio de pagos (PAY) debe coincidir con el DFF traducido',
                    'TIPO_CONTROL': 'Consistencia de Valores', 'NIVEL_RIESGO': NIVEL_ADVERTENCIA
                })
        
        # Validaciones específicas de cada sitio
        for _, fila_sitio in sitios.iterrows():
            self._validar_sitio_individual(fila_sitio, header_row, v_number, v_name,
                                          header_priority, enabled_flag)
    
    def _validar_sitio_individual(self, fila_sitio, header_row, v_number, v_name,
                                 header_priority, enabled_flag):
        """Validación de un sitio individual"""
        
        s_code = fila_sitio['VENDOR_SITE_CODE']
        s_code_upper = str(s_code).strip().upper()
        s_country = fila_sitio['COUNTRY']
        s_priority = pd.to_numeric(fila_sitio['PAYMENT_PRIORITY'], errors='coerce')
        s_inactive_date = fila_sitio['INACTIVE_DATE']
        s_status = fila_sitio['SITE_STATUS']
        
        # Consistencia de términos de pago
        self._validar_consistencia_terminos(fila_sitio, header_row, s_code, v_number, v_name)
        
        # Consistencia de prioridad de pago
        self._validar_consistencia_prioridad(fila_sitio, header_row, s_code, s_priority,
                                            header_priority, v_number, v_name)
        
        # Validar inactive_date vs enabled_flag
        if enabled_flag == 'Y' and not pd.isna(s_inactive_date):
            self._agregar_excepcion({
                'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': s_code,
                'CAMPO_AUDITADO': 'INACTIVE_DATE vs ENABLED_FLAG',
                'VALOR_ORACLE': f'Inactivo el {s_inactive_date}',
                'REGLA_ESPERADA': 'Si el proveedor global está habilitado, advierte si el sitio individual tiene fecha de baja',
                'TIPO_CONTROL': 'Consistencia de Valores', 'NIVEL_RIESGO': NIVEL_ADVERTENCIA
            })
        
        # Validaciones específicas para sitios de pago (PAY)
        if s_status == 'PAY':
            self._validar_sitio_pago(fila_sitio, s_code, s_code_upper, s_country,
                                    s_priority, v_number, v_name)
        
        # Validaciones de formato (regex)
        self._validar_formato_campos(fila_sitio, s_code, s_code_upper, v_number, v_name)
    
    def _validar_consistencia_terminos(self, fila_sitio, header_row, s_code, v_number, v_name):
        """Valida consistencia de términos entre header y sitio"""
        
        h_terms = header_row['TERMS_ID'].values[0]
        s_terms = fila_sitio['TERMS_ID']
        
        if pd.notna(h_terms) and pd.notna(s_terms):
            try:
                h_terms_val = int(float(h_terms))
                s_terms_val = int(float(s_terms))
                if h_terms_val != s_terms_val:
                    h_desc = self.mapeo_terminos.get(h_terms_val, str(h_terms_val))
                    s_desc = self.mapeo_terminos.get(s_terms_val, str(s_terms_val))
                    self._agregar_excepcion({
                        'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': s_code,
                        'CAMPO_AUDITADO': 'TERMS_ID (Consistencia)',
                        'VALOR_ORACLE': f'Sitio={s_desc}',
                        'REGLA_ESPERADA': f'Debe coincidir con la cabecera ({h_desc})',
                        'TIPO_CONTROL': 'Consistencia de Valores', 'NIVEL_RIESGO': NIVEL_ERROR
                    })
            except (ValueError, TypeError):
                if str(h_terms).strip() != str(s_terms).strip():
                    self._agregar_excepcion({
                        'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': s_code,
                        'CAMPO_AUDITADO': 'TERMS_ID (Consistencia)',
                        'VALOR_ORACLE': f'Sitio={s_terms}',
                        'REGLA_ESPERADA': f'Debe coincidir con la cabecera ({h_terms})',
                        'TIPO_CONTROL': 'Consistencia de Valores', 'NIVEL_RIESGO': NIVEL_ERROR
                    })
    
    def _validar_consistencia_prioridad(self, fila_sitio, header_row, s_code, s_priority,
                                       header_priority, v_number, v_name):
        """Valida consistencia de prioridad entre header y sitio"""
        
        if pd.notna(header_priority) and pd.notna(s_priority):
            try:
                h_prio_val = int(float(header_priority))
                s_prio_val = int(float(s_priority))
                if h_prio_val != s_prio_val:
                    self._agregar_excepcion({
                        'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': s_code,
                        'CAMPO_AUDITADO': 'PAYMENT_PRIORITY (Consistencia)',
                        'VALOR_ORACLE': f'Sitio={s_prio_val}',
                        'REGLA_ESPERADA': f'Debe coincidir con la cabecera ({h_prio_val})',
                        'TIPO_CONTROL': 'Consistencia de Valores', 'NIVEL_RIESGO': NIVEL_ERROR
                    })
            except (ValueError, TypeError):
                pass
    
    def _validar_sitio_pago(self, fila_sitio, s_code, s_code_upper, s_country,
                           s_priority, v_number, v_name):
        """Validaciones específicas para sitios de pago (PAY)"""
        
        s_country_upper = str(s_country).strip().upper()
        attr6 = str(fila_sitio['ATTRIBUTE6']).strip()
        attr6_upper = attr6.upper()
        
        # Buscar reglas geográficas coincidentes (indice pre-construido O(1))
        reglas_pais = self.geo_rules_por_pais.get(s_country_upper, [])
        if not reglas_pais:
            reglas_pais = self.geo_rules_por_pais.get('DEFAULT', []) + \
                          self.geo_rules_por_pais.get('OTRO', [])
        
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
            # Validar prioridad permitida
            allowed_prio = regla_coincidente['ALLOWED_PRIORITIES']
            if allowed_prio and s_priority not in allowed_prio:
                prio_str = ", ".join(map(str, allowed_prio))
                self._agregar_excepcion({
                    'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': s_code,
                    'CAMPO_AUDITADO': 'PAYMENT_PRIORITY',
                    'VALOR_ORACLE': str(s_priority),
                    'REGLA_ESPERADA': f'Para {s_country}, la prioridad del sitio de pago debe ser {prio_str}',
                    'TIPO_CONTROL': 'Paramétrico Geográfico (Site)', 'NIVEL_RIESGO': NIVEL_ERROR
                })
            
            # Validar ATTRIBUTE6 (comisión bancaria)
            expected_attr6 = regla_coincidente['ATTRIBUTE6_ESPERADO']
            if expected_attr6:
                if pd.isna(fila_sitio['ATTRIBUTE6']) or attr6 == '' or attr6.lower() == 'nan':
                    self._agregar_excepcion({
                        'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': s_code,
                        'CAMPO_AUDITADO': 'ATTRIBUTE6',
                        'VALOR_ORACLE': str(fila_sitio['ATTRIBUTE6']),
                        'REGLA_ESPERADA': 'El campo de comisión bancaria (ATTRIBUTE6) no debe estar en blanco para sitios de pago (PAY)',
                        'TIPO_CONTROL': 'Obligatoriedad', 'NIVEL_RIESGO': NIVEL_ERROR
                    })
                elif attr6_upper != expected_attr6:
                    self._agregar_excepcion({
                        'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': s_code,
                        'CAMPO_AUDITADO': 'ATTRIBUTE6',
                        'VALOR_ORACLE': str(fila_sitio['ATTRIBUTE6']),
                        'REGLA_ESPERADA': f'Para el sitio {s_code} en {s_country}, la comisión bancaria (ATTRIBUTE6) debe ser {expected_attr6}',
                        'TIPO_CONTROL': 'Paramétrico Geográfico (Site)', 'NIVEL_RIESGO': NIVEL_ERROR
                    })
        else:
            # No coincide con ningún patrón
            patrones_permitidos = [r['SITE_CODE_PATTERN'] for r in reglas_pais]
            patrones_str = " o ".join(patrones_permitidos)
            self._agregar_excepcion({
                'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': s_code,
                'CAMPO_AUDITADO': 'VENDOR_SITE_CODE',
                'VALOR_ORACLE': s_code,
                'REGLA_ESPERADA': f'Para {s_country}, el sitio de pago debe coincidir con el patrón: {patrones_str}',
                'TIPO_CONTROL': 'Paramétrico Geográfico (Site)', 'NIVEL_RIESGO': NIVEL_ERROR
            })
    
    def _validar_formato_campos(self, fila_sitio, s_code, s_code_upper, v_number, v_name):
        """Valida formato de campos según regex"""
        
        for rule in self.format_rules:
            rule_site = rule['SITE_CODE']
            if s_code_upper.startswith(rule_site) or rule_site in s_code_upper:
                col_name = rule['COLUMN_NAME']
                val_oracle = str(fila_sitio[col_name]).strip()
                
                if val_oracle != 'nan' and val_oracle != '':
                    try:
                        if not re.match(rule['REGEX_PATTERN'], val_oracle):
                            self._agregar_excepcion({
                                'VENDOR_NUMBER': v_number, 'VENDOR_NAME': v_name, 'VENDOR_SITE_CODE': s_code,
                                'CAMPO_AUDITADO': f'{col_name} (Banca)',
                                'VALOR_ORACLE': val_oracle,
                                'REGLA_ESPERADA': rule['REGLA_ESPERADA'],
                                'TIPO_CONTROL': 'Formato Texto (Banking Retail)', 'NIVEL_RIESGO': NIVEL_ERROR
                            })
                    except re.error as e:
                        print(f"⚠ Patrón regex inválido: {rule['REGEX_PATTERN']} - {e}")
    
    def _generar_lista_correctos(self):
        """Genera la lista de registros que pasaron todas las validaciones"""
        
        # Identificar qué entidades fallaron
        failed_headers = set()
        failed_sites = set()
        
        for exc in self.lista_excepciones:
            v_num = str(exc.get('VENDOR_NUMBER', '')).strip()
            s_code = str(exc.get('VENDOR_SITE_CODE', '')).strip()
            campo = str(exc.get('CAMPO_AUDITADO', '')).strip()
            
            if s_code == 'HEADER':
                if campo.startswith('VENDOR_SITE_CODE'):
                    # Sin sitios asignados: todo el vendor falla
                    failed_headers.add(v_num)
                    failed_sites.add((v_num, 'ALL'))
                elif campo == 'SITE_STATUS (PUR)':
                    # Falta sitio PUR
                    failed_sites.add((v_num, 'PUR Site'))
                elif campo == 'SITE_STATUS (PAY)':
                    # Falta sitio PAY
                    failed_sites.add((v_num, 'PAY Site'))
                else:
                    # Otras validaciones de cabecera
                    failed_headers.add(v_num)
            elif s_code in ['PUR Site', 'PAY Site']:
                failed_sites.add((v_num, s_code))
            else:
                failed_sites.add((v_num, s_code))
        
        # Recorrer todos los registros activos para encontrar los correctos
        for vendor_id, sitios in self.df_paysite_activo.groupby('VENDOR_ID'):
            header_row = self.df_header[self.df_header['VENDOR_ID'] == vendor_id]
            if header_row.empty:
                continue
            
            v_number = str(header_row['VENDOR_NUMBER'].values[0]).strip()
            v_name = header_row['VENDOR_NAME'].values[0]
            
            # Verificar cabecera
            if v_number not in failed_headers:
                self.lista_correctos.append({
                    'VENDOR_NUMBER': v_number,
                    'VENDOR_NAME': v_name,
                    'VENDOR_SITE_CODE': 'HEADER',
                    'CAMPO_AUDITADO': 'TODOS',
                    'VALOR_ORACLE': '-',
                    'REGLA_ESPERADA': 'Cumple con todos los parámetros de cabecera',
                    'TIPO_CONTROL': 'Validación Correcta',
                    'NIVEL_RIESGO': 'OK'
                })
            
            # Verificar cada sitio
            for _, fila_sitio in sitios.iterrows():
                s_code = str(fila_sitio['VENDOR_SITE_CODE']).strip()
                s_status = fila_sitio['SITE_STATUS']
                
                sitio_fallo = (
                    (v_number, s_code) in failed_sites or
                    (v_number, 'ALL') in failed_sites or
                    (s_status == 'PUR' and (v_number, 'PUR Site') in failed_sites) or
                    (s_status == 'PAY' and (v_number, 'PAY Site') in failed_sites)
                )
                
                if not sitio_fallo:
                    self.lista_correctos.append({
                        'VENDOR_NUMBER': v_number,
                        'VENDOR_NAME': v_name,
                        'VENDOR_SITE_CODE': s_code,
                        'CAMPO_AUDITADO': 'TODOS',
                        'VALOR_ORACLE': '-',
                        'REGLA_ESPERADA': 'Cumple con todos los parámetros del sitio',
                        'TIPO_CONTROL': 'Validación Correcta',
                        'NIVEL_RIESGO': 'OK'
                    })
    
    def _agregar_excepcion(self, excepcion):
        """Agrega una excepción a la lista"""
        self.lista_excepciones.append(excepcion)