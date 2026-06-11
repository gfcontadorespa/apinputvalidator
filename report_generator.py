"""
Módulo para generación de reportes (Excel y HTML)
"""
import html
import pandas as pd
from datetime import datetime
from config import COLUMNAS_REPORTE, ARCHIVO_SALIDA_EXCEL, ARCHIVO_SALIDA_HTML
from config import NIVEL_CRITICO, NIVEL_ERROR, NIVEL_ADVERTENCIA, NIVEL_OK


class ReportGenerator:
    """Generador de reportes en Excel y HTML"""
    
    def __init__(self):
        """Inicializa el generador de reportes"""
        self.columnas_reporte = COLUMNAS_REPORTE
    
    def generar_reportes(self, lista_excepciones, lista_correctos, 
                        nombre_excel=ARCHIVO_SALIDA_EXCEL, 
                        nombre_html=ARCHIVO_SALIDA_HTML):
        """
        Genera reportes en Excel y HTML
        
        Args:
            lista_excepciones: Lista de excepciones encontradas
            lista_correctos: Lista de registros validados correctamente
            nombre_excel: Nombre del archivo Excel de salida
            nombre_html: Nombre del archivo HTML de salida
            
        Returns:
            tuple: (ruta_excel, ruta_html) o (None, None) si hay error
        """
        print("\n▶ Generando reportes...")
        
        try:
            # Generar Excel
            self._generar_excel(lista_excepciones, lista_correctos, nombre_excel)
            print(f"✓ Excel generado: {nombre_excel}")
            
            # Generar HTML
            self._generar_html(lista_excepciones, lista_correctos, nombre_html)
            print(f"✓ HTML generado: {nombre_html}")
            
            return nombre_excel, nombre_html
            
        except Exception as e:
            print(f"✗ Error al generar reportes: {str(e)}")
            return None, None
    
    def _generar_excel(self, lista_excepciones, lista_correctos, nombre_salida):
        """Genera reporte en Excel con múltiples hojas"""
        
        # Crear DataFrames
        if not lista_excepciones:
            df_excepciones = pd.DataFrame(columns=self.columnas_reporte)
        else:
            df_excepciones = pd.DataFrame(lista_excepciones)
        
        if not lista_correctos:
            df_correctos = pd.DataFrame(columns=self.columnas_reporte)
        else:
            df_correctos = pd.DataFrame(lista_correctos)
        
        # Escribir Excel
        try:
            with pd.ExcelWriter(nombre_salida, engine='openpyxl') as writer:
                df_excepciones.to_excel(writer, sheet_name='Desviaciones', index=False)
                df_correctos.to_excel(writer, sheet_name='Validados_Ok', index=False)
        except Exception as e:
            print(f"⚠ Openpyxl falló, usando xlsxwriter: {e}")
            with pd.ExcelWriter(nombre_salida, engine='xlsxwriter') as writer:
                df_excepciones.to_excel(writer, sheet_name='Desviaciones', index=False)
                df_correctos.to_excel(writer, sheet_name='Validados_Ok', index=False)
    
    def _generar_html(self, lista_excepciones, lista_correctos, nombre_salida):
        """Genera reporte HTML autocontenido con diseño premium"""
        
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Generar filas HTML para excepciones
        filas_ex_html = self._generar_filas_excepciones(lista_excepciones)
        
        # Generar filas HTML para correctos
        filas_ok_html = self._generar_filas_correctos(lista_correctos)
        
        # Template HTML
        html_content = self._generar_template_html(
            fecha_actual, filas_ex_html, filas_ok_html,
            len(lista_excepciones), len(lista_correctos)
        )
        
        # Escribir archivo
        with open(nombre_salida, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generar_filas_excepciones(self, lista_excepciones):
        """Genera filas HTML para excepciones con escapado de caracteres"""
        
        if not lista_excepciones:
            return '<tr><td colspan="8" style="text-align: center; color: #64748b; padding: 30px;">No se detectaron desviaciones o alertas en los datos.</td></tr>'
        
        filas = []
        for exc in lista_excepciones:
            riesgo = str(exc.get('NIVEL_RIESGO', '')).upper()
            
            if riesgo == NIVEL_CRITICO:
                badge_class = 'badge-critico'
            elif riesgo == NIVEL_ERROR:
                badge_class = 'badge-error'
            else:
                badge_class = 'badge-advertencia'
            
            fila = f"""
            <tr>
                <td><strong>{html.escape(str(exc.get('VENDOR_NUMBER', '')))}</strong></td>
                <td>{html.escape(str(exc.get('VENDOR_NAME', '')))}</td>
                <td><span class="site-code">{html.escape(str(exc.get('VENDOR_SITE_CODE', '')))}</span></td>
                <td><code>{html.escape(str(exc.get('CAMPO_AUDITADO', '')))}</code></td>
                <td><span class="value-oracle">{html.escape(str(exc.get('VALOR_ORACLE', '')))}</span></td>
                <td>{html.escape(str(exc.get('REGLA_ESPERADA', '')))}</td>
                <td>{html.escape(str(exc.get('TIPO_CONTROL', '')))}</td>
                <td><span class="badge {badge_class}">{riesgo}</span></td>
            </tr>"""
            filas.append(fila)
        
        return "\n".join(filas)
    
    def _generar_filas_correctos(self, lista_correctos):
        """Genera filas HTML para registros correctos con escapado de caracteres"""
        
        if not lista_correctos:
            return '<tr><td colspan="8" style="text-align: center; color: #64748b; padding: 30px;">No hay registros validados correctamente.</td></tr>'
        
        filas = []
        for ok in lista_correctos:
            fila = f"""
            <tr>
                <td><strong>{html.escape(str(ok.get('VENDOR_NUMBER', '')))}</strong></td>
                <td>{html.escape(str(ok.get('VENDOR_NAME', '')))}</td>
                <td><span class="site-code">{html.escape(str(ok.get('VENDOR_SITE_CODE', '')))}</span></td>
                <td><code>{html.escape(str(ok.get('CAMPO_AUDITADO', '')))}</code></td>
                <td><span class="value-oracle">{html.escape(str(ok.get('VALOR_ORACLE', '')))}</span></td>
                <td>{html.escape(str(ok.get('REGLA_ESPERADA', '')))}</td>
                <td>{html.escape(str(ok.get('TIPO_CONTROL', '')))}</td>
                <td><span class="badge badge-ok">OK</span></td>
            </tr>"""
            filas.append(fila)
        
        return "\n".join(filas)
    
    def _generar_template_html(self, fecha_actual, filas_ex_html, filas_ok_html,
                              total_excepciones, total_correctos):
        """Genera el template HTML completo"""
        
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de Auditoría de Proveedores - Oracle EBS</title>
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
        
        /* Tabs Styling */
        .tabs-header {{
            display: flex;
            gap: 12px;
            margin-bottom: 24px;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 12px;
        }}
        .tab-btn {{
            background: none;
            border: none;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 600;
            color: #64748b;
            cursor: pointer;
            border-radius: 6px;
            transition: all 0.2s ease;
            outline: none;
        }}
        .tab-btn:hover {{
            color: #0f172a;
            background-color: #f1f5f9;
        }}
        .tab-btn.active {{
            color: #2563eb;
            background-color: #eff6ff;
            box-shadow: 0 1px 2px rgba(37, 99, 235, 0.05);
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
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
        .badge-ok {{
            background-color: #f0fdf4;
            color: #166534;
            border: 1px solid #dcfce7;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Auditoría de Proveedores Oracle EBS</h1>
            <div class="summary-badge">Resultado de Validación</div>
        </header>
        
        <div class="meta-grid">
            <div class="meta-card">
                <div class="meta-card-title">Fecha de Auditoría</div>
                <div class="meta-card-value">{fecha_actual}</div>
            </div>
            <div class="meta-card">
                <div class="meta-card-title">Desviaciones Detectadas</div>
                <div class="meta-card-value" style="color: #ef4444;">{total_excepciones}</div>
            </div>
            <div class="meta-card">
                <div class="meta-card-title">Registros Correctos</div>
                <div class="meta-card-value" style="color: #10b981;">{total_correctos}</div>
            </div>
        </div>
        
        <div class="tabs-header">
            <button class="tab-btn active" onclick="switchTab('excepciones')">Desviaciones y Alertas ({total_excepciones})</button>
            <button class="tab-btn" onclick="switchTab('correctos')">Registros Correctos ({total_correctos})</button>
        </div>
        
        <div id="excepciones" class="tab-content active">
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
                        {filas_ex_html}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div id="correctos" class="tab-content">
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
                        {filas_ok_html}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        function switchTab(tabId) {{
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            
            document.getElementById(tabId).classList.add('active');
            event.currentTarget.classList.add('active');
        }}
    </script>
</body>
</html>
"""
