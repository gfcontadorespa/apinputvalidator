"""
revisor.py - Punto de entrada compatible hacia atrás (Wrapper de main.py)

Este archivo mantiene compatibilidad con scripts anteriores que lo llamaban directamente.
La lógica principal ahora está modularizada en:
  - config.py - Configuración y constantes
  - data_loader.py - Carga de datos CSV
  - parameters.py - Parámetros de auditoría
  - validators.py - Lógica de validación
  - report_generator.py - Generación de reportes
  - main.py - Orquestador principal
"""
import sys
from main import AuditoriaEBS


def ejecutar_auditoria_ebs(archivo_header, archivo_paysite):
    """
    Función compatible hacia atrás que ejecuta la auditoría
    
    Args:
        archivo_header: Ruta del archivo de cabeceras
        archivo_paysite: Ruta del archivo de sitios
    """
    auditoria = AuditoriaEBS()
    auditoria.ejecutar(archivo_header, archivo_paysite)


if __name__ == "__main__":
    # Mantener compatibilidad con llamadas anteriores
    if len(sys.argv) >= 3:
        archivo_header = sys.argv[1]
        archivo_paysite = sys.argv[2]
        ejecutar_auditoria_ebs(archivo_header, archivo_paysite)
    else:
        # Si no hay argumentos, usar main.py directamente
        from main import main
        main()
