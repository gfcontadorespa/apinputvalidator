"""
Módulo principal - Orquestador de la auditoría de proveedores Oracle EBS
Integra carga de datos, validación y generación de reportes
"""
import os
import sys
import logging
import tkinter as tk
from tkinter import filedialog

from config import DIRECTORIO_SCRIPT, ARCHIVO_HEADER_EJEMPLO, ARCHIVO_PAYSITE_EJEMPLO
from data_loader import cargar_datos_oracle
from parameters import cargar_parametros
from validators import AuditoriaValidator
from report_generator import ReportGenerator


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AuditoriaEBS:
    """Clase principal para ejecutar la auditoría completa"""
    
    def __init__(self):
        """Inicializa la auditoría"""
        self.archivo_header = None
        self.archivo_paysite = None
        self.parametros = None
        self.resultado = None
    
    def seleccionar_archivos_gui(self):
        """Permite al usuario seleccionar archivos mediante interfaz gráfica"""
        
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            
            print("\n▶ Selecciona los archivos de Oracle EBS...")
            print("  1. Archivo de Cabeceras (Header)")
            print("  2. Archivo de Sitios (PaySite)")
            
            self.archivo_header = filedialog.askopenfilename(
                title="1. Seleccionar Reporte de HEADER de Oracle (Cabeceras)",
                filetypes=[
                    ("Archivos CSV", "*.csv"),
                    ("Archivos de Texto", "*.txt"),
                    ("Todos los archivos", "*.*")
                ]
            )
            
            if not self.archivo_header:
                print("✗ Proceso cancelado: No seleccionaste el archivo de Encabezados.")
                return False
            
            self.archivo_paysite = filedialog.askopenfilename(
                title="2. Seleccionar Reporte de SITES de Oracle (Sitios)",
                filetypes=[
                    ("Archivos CSV", "*.csv"),
                    ("Archivos de Texto", "*.txt"),
                    ("Todos los archivos", "*.*")
                ]
            )
            
            if not self.archivo_paysite:
                print("✗ Proceso cancelado: No seleccionaste el archivo de Sitios.")
                return False
            
            root.destroy()
            return True
            
        except Exception as e:
            logger.error(f"Error en GUI: {str(e)}")
            return False
    
    def usar_archivos_defecto(self):
        """Usa los archivos por defecto de ExampleData"""
        
        if os.path.exists(ARCHIVO_HEADER_EJEMPLO) and os.path.exists(ARCHIVO_PAYSITE_EJEMPLO):
            self.archivo_header = ARCHIVO_HEADER_EJEMPLO
            self.archivo_paysite = ARCHIVO_PAYSITE_EJEMPLO
            print("✓ Usando archivos por defecto de ExampleData")
            return True
        
        return False
    
    def cargar_datos(self):
        """Carga los datos de Oracle"""
        
        print(f"\n▶ Cargando datos de Oracle EBS...")
        
        try:
            df_header, df_paysite = cargar_datos_oracle(
                self.archivo_header,
                self.archivo_paysite
            )
            
            print(f"✓ Datos cargados correctamente")
            return df_header, df_paysite
            
        except Exception as e:
            logger.error(f"Error al cargar datos: {str(e)}")
            return None, None
    
    def cargar_parametros_negocio(self):
        """Carga los parámetros de auditoría"""
        
        print(f"\n▶ Cargando parámetros de negocio...")
        
        try:
            self.parametros = cargar_parametros()
            print(f"✓ Parámetros cargados")
            return True
            
        except Exception as e:
            logger.error(f"Error al cargar parámetros: {str(e)}")
            return False
    
    def ejecutar_validacion(self, df_header, df_paysite):
        """Ejecuta las validaciones"""
        
        try:
            validator = AuditoriaValidator(df_header, df_paysite, self.parametros)
            excepciones, correctos = validator.ejecutar_auditoria()
            
            self.resultado = {
                'excepciones': excepciones,
                'correctos': correctos
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Error en validación: {str(e)}")
            return False
    
    def generar_reportes(self):
        """Genera los reportes finales"""
        
        try:
            generator = ReportGenerator()
            excel_file, html_file = generator.generar_reportes(
                self.resultado['excepciones'],
                self.resultado['correctos']
            )
            
            return excel_file, html_file
            
        except Exception as e:
            logger.error(f"Error al generar reportes: {str(e)}")
            return None, None
    
    def imprimir_resumen(self):
        """Imprime un resumen final"""
        
        if not self.resultado:
            return
        
        total_excepciones = len(self.resultado['excepciones'])
        total_correctos = len(self.resultado['correctos'])
        total_general = total_excepciones + total_correctos
        
        print("\n" + "="*60)
        print("RESUMEN FINAL DE AUDITORÍA")
        print("="*60)
        print(f"Total de registros auditados: {total_general}")
        print(f"Desviaciones encontradas: {total_excepciones}")
        print(f"Registros correctos: {total_correctos}")
        print(f"Tasa de conformidad: {(total_correctos/total_general)*100:.1f}%" if total_general > 0 else "N/A")
        print("="*60 + "\n")
    
    def ejecutar(self, archivo_header=None, archivo_paysite=None):
        """
        Ejecuta la auditoría completa
        
        Args:
            archivo_header: Ruta del archivo header (opcional)
            archivo_paysite: Ruta del archivo paysite (opcional)
            
        Returns:
            bool: True si la auditoría se completó exitosamente
        """
        
        print("\n╔════════════════════════════════════════════════════════════╗")
        print("║  AUDITORÍA DE PROVEEDORES ORACLE EBS - AP Input Validator  ║")
        print("╚════════════════════════════════════════════════════════════╝")
        
        # 1. Obtener archivos
        if archivo_header and archivo_paysite:
            self.archivo_header = archivo_header
            self.archivo_paysite = archivo_paysite
            print(f"✓ Archivos especificados por parámetro")
        else:
            # Intentar GUI si hay display
            if os.environ.get('DISPLAY') or sys.platform == 'win32' or sys.platform == 'darwin':
                if not self.seleccionar_archivos_gui():
                    # Fallback a defecto
                    if not self.usar_archivos_defecto():
                        print("✗ No se pudieron obtener archivos de entrada")
                        return False
            else:
                # Sin display, usar defecto
                if not self.usar_archivos_defecto():
                    print("✗ No se encontraron archivos por defecto")
                    return False
        
        # 2. Cargar parámetros
        if not self.cargar_parametros_negocio():
            return False
        
        # 3. Cargar datos
        df_header, df_paysite = self.cargar_datos()
        if df_header is None or df_paysite is None:
            return False
        
        # 4. Ejecutar validaciones
        if not self.ejecutar_validacion(df_header, df_paysite):
            return False
        
        # 5. Generar reportes
        excel_file, html_file = self.generar_reportes()
        if excel_file is None or html_file is None:
            return False
        
        # 6. Imprimir resumen
        self.imprimir_resumen()
        
        print(f"📊 Reportes generados:")
        print(f"  • Excel: {os.path.abspath(excel_file)}")
        print(f"  • HTML:  {os.path.abspath(html_file)}")
        print("\n✓ Auditoría completada exitosamente\n")
        
        return True


def main():
    """Punto de entrada principal"""
    
    # Obtener archivos de argumentos de línea de comandos si existen
    archivo_header = sys.argv[1] if len(sys.argv) > 1 else None
    archivo_paysite = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Ejecutar auditoría
    auditoria = AuditoriaEBS()
    success = auditoria.ejecutar(archivo_header, archivo_paysite)
    
    # Retornar código de salida
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
