# Estructura Modular - AP Input Validator

## Visión General

El código original monolítico (`revisor.py ~1500 líneas) ha sido refactorizado en **módulos independientes** para mejor mantenibilidad, testabilidad y facilitar correcciones sin comprometer el código completo.

## 📁 Estructura de Módulos

```
apinputvalidator/
├── config.py                      # ⚙️  Configuración y constantes
├── data_loader.py                 # 📂 Carga de archivos CSV
├── parameters.py                  # 🔧 Carga de parámetros Excel
├── validators.py                  # ✅ Lógica de validación
├── report_generator.py            # 📊 Generación de reportes
├── main.py                        # 🎬 Orquestador principal
├── revisor.py                     # 🔀 Wrapper compatible (entrada)
├── Parámetros.xlsx               # 📋 Parámetros de negocio
└── ExampleData/                   # 📁 Datos de ejemplo
    ├── AP New or Updated Suppliers - Header View.csv
    └── AP New or Updated Suppliers - PaySite View.csv
```

## 🔧 Módulos Detallados

### 1️⃣ **config.py** (~90 líneas)
**Responsabilidad:** Configuración centralizada
- Rutas de directorios (base, parámetros, datos de ejemplo)
- Codificaciones soportadas
- Mapeos de países y reglas por defecto
- Constantes de niveles de riesgo
- Nombres de archivos de salida

**Constantes principales:**
- `DIRECTORIO_SCRIPT` - Carpeta raíz del proyecto
- `RUTA_PARAMETROS` - Ruta a Parámetros.xlsx
- `ARCHIVO_HEADER_EJEMPLO` - Archivo de ejemplo (header)
- `ARCHIVO_PAYSITE_EJEMPLO` - Archivo de ejemplo (paysite)
- `ARCHIVO_SALIDA_EXCEL` - Nombre del reporte Excel
- `ARCHIVO_SALIDA_HTML` - Nombre del reporte HTML

**Uso:**
```python
from config import DIRECTORIO_SCRIPT, MAPEO_PAISES_DEFAULT, NIVEL_ERROR
from config import ARCHIVO_HEADER_EJEMPLO, RUTA_PARAMETROS
```

---

### 2️⃣ **data_loader.py** (~80 líneas)
**Responsabilidad:** Carga y preparación de datos
- `cargar_csv_con_autodetect()` - Detecta encoding automáticamente
- `remover_prefijo_comun()` - Normaliza nombres de columnas
- `cargar_datos_oracle()` - Carga ambos archivos con validación

**Uso:**
```python
from data_loader import cargar_datos_oracle

df_header, df_paysite = cargar_datos_oracle(archivo_header, archivo_paysite)
```

---

### 3️⃣ **parameters.py** (~120 líneas)
**Responsabilidad:** Carga y gestión de parámetros
- `cargar_parametros()` - Lee desde Excel con fallbacks
- Mapeos de países
- Reglas por tipo de proveedor
- Reglas geográficas
- Reglas de formato

**Uso:**
```python
from parameters import cargar_parametros

parametros = cargar_parametros()
```

---

### 4️⃣ **validators.py** (~700 líneas) ⭐ **Módulo Principal**
**Responsabilidad:** Lógica de validación

**Clase:** `AuditoriaValidator`

**Métodos públicos:**
- `ejecutar_auditoria()` - Ejecuta todas las validaciones
- `validar_header()` - Validaciones de cabecera
- `validar_sitios()` - Validaciones de sitios
- `validar_sitio_individual()` - Validación de sitio específico

**Métodos privados (validaciones específicas):**
- `_validar_consistencia_terminos()` - Términos de pago
- `_validar_consistencia_prioridad()` - Prioridades
- `_validar_sitio_pago()` - Sitios de pago con reglas geográficas
- `_validar_formato_campos()` - Validación regex
- `_generar_lista_correctos()` - Registros sin errores

**Uso:**
```python
from validators import AuditoriaValidator

validator = AuditoriaValidator(df_header, df_paysite, parametros)
excepciones, correctos = validator.ejecutar_auditoria()
```

---

### 5️⃣ **report_generator.py** (~300 líneas)
**Responsabilidad:** Generación de reportes

**Clase:** `ReportGenerator`

**Métodos:**
- `generar_reportes()` - Genera Excel y HTML
- `_generar_excel()` - Crea archivo Excel con 2 hojas
- `_generar_html()` - Crea HTML autocontenido con estilos premium
- `_generar_filas_excepciones()` - HTML con escapado de caracteres
- `_generar_filas_correctos()` - HTML de registros OK
- `_generar_template_html()` - Template HTML completo

**Uso:**
```python
from report_generator import ReportGenerator

generator = ReportGenerator()
excel_file, html_file = generator.generar_reportes(excepciones, correctos)
```

---

### 6️⃣ **main.py** (~250 líneas) 🎬
**Responsabilidad:** Orquestación y flujo principal

**Clase:** `AuditoriaEBS`

**Flujo:**
1. Selección de archivos (GUI o defecto)
2. Carga de parámetros
3. Carga de datos
4. Ejecución de validaciones
5. Generación de reportes
6. Resumen final

**Métodos:**
- `ejecutar()` - Orquesta todo el proceso
- `seleccionar_archivos_gui()` - Interfaz gráfica
- `usar_archivos_defecto()` - Fallback a ExampleData
- `cargar_datos()` - Delegación
- `ejecutar_validacion()` - Delegación
- `generar_reportes()` - Delegación

**Uso:**
```python
from main import AuditoriaEBS

auditoria = AuditoriaEBS()
auditoria.ejecutar()  # O con archivos específicos
auditoria.ejecutar(archivo_header, archivo_paysite)
```

---

### 7️⃣ **revisor.py** 🔀
**Responsabilidad:** Compatibilidad hacia atrás

- Wrapper que delega a `main.py`
- Mantiene firmas de funciones antiguas
- Soporta llamadas por línea de comandos

**Uso (compatible con código anterior):**
```bash
python revisor.py archivo_header.csv archivo_paysite.csv
python revisor.py  # GUI interactivo
```

---

## 🚀 Cómo Usar

### Opción 1: Ejecutar directamente (recomendado)
```bash
python main.py
```

### Opción 2: Compatibilidad hacia atrás
```bash
python revisor.py
```

### Opción 3: Con archivos específicos
```bash
python revisor.py "ExampleData/AP New or Updated Suppliers - Header View.csv" \
                   "ExampleData/AP New or Updated Suppliers - PaySite View.csv"
```

---

## ✅ Ventajas de la Modularización

| Aspecto | Antes | Después |
|---------|-------|--------|
| **Líneas por archivo** | 1500 | 90-700 |
| **Testabilidad** | Difícil | Fácil (cada módulo testeable) |
| **Mantenibilidad** | Compleja | Clara (responsabilidad única) |
| **Correcciones** | Riesgosas | Seguras (módulos independientes) |
| **Reutilización** | Monolítico | Modular (`import validators`) |
| **Debugging** | Global | Localizado por módulo |

---

## 🔧 Modificar Configuración

### Cambiar rutas de archivos
**Archivo:** `config.py`
```python
# Parámetros de negocio
RUTA_PARAMETROS = os.path.join(DIRECTORIO_SCRIPT, 'Parámetros.xlsx')

# Archivos de ejemplo (para testing)
ARCHIVO_HEADER_EJEMPLO = os.path.join(DIRECTORIO_EXAMPLE_DATA, 'AP New or Updated Suppliers - Header View.csv')
ARCHIVO_PAYSITE_EJEMPLO = os.path.join(DIRECTORIO_EXAMPLE_DATA, 'AP New or Updated Suppliers - PaySite View.csv')

# Nombres de salida
ARCHIVO_SALIDA_EXCEL = 'Reporte_Auditoria_EBS_Proveedores.xlsx'
ARCHIVO_SALIDA_HTML = 'Reporte_Auditoria_EBS_Proveedores.html'
```
**⚠️ IMPORTANTE:** Cualquier cambio en rutas debe hacerse en `config.py`, no en otros módulos.

### Cambiar mapeo de países
**Archivo:** `config.py`
```python
MAPEO_PAISES_DEFAULT = {
    'Mi Pais': 'XX',  # Agregar nuevo país
    # ...
}
```

### Agregar nueva regla de validación
**Archivo:** `validators.py`
```python
def _nueva_validacion(self):
    """Nueva validación personalizada"""
    # Lógica aquí
    self._agregar_excepcion({...})
```

### Cambiar formato de reporte HTML
**Archivo:** `report_generator.py`
```python
def _generar_template_html(self, ...):
    # Modificar HTML/CSS aquí
    return html_modificado
```

---

## 📋 Flujo de Ejecución

```
revisor.py o main.py
    ↓
AuditoriaEBS.ejecutar()
    ├─→ cargar_parametros()         [parameters.py]
    ├─→ cargar_datos_oracle()       [data_loader.py]
    ├─→ AuditoriaValidator.ejecutar_auditoria()  [validators.py]
    │   ├─→ _validar_header()
    │   ├─→ _validar_sitios()
    │   └─→ _generar_lista_correctos()
    └─→ ReportGenerator.generar_reportes()  [report_generator.py]
        ├─→ _generar_excel()
        └─→ _generar_html()
```

---

## 🐛 Errores Comunes y Soluciones

| Error | Módulo | Solución |
|-------|--------|----------|
| `FileNotFoundError: Parámetros.xlsx` | parameters.py | Verificar ruta en config.py |
| `UnicodeDecodeError` | data_loader.py | Agregar encoding a CODIFICACIONES_CSV |
| `KeyError` en validaciones | validators.py | Verificar nombres de columnas |
| HTML sin estilos | report_generator.py | Verificar template CSS |

---

## 📊 Estadísticas

- **Líneas totales de código:** ~1500
- **Número de módulos:** 7
- **Clases principales:** 2 (AuditoriaValidator, ReportGenerator)
- **Funciones totales:** 25+
- **Métodos privados (helpers):** 20+

---

## ✨ Mejoras Futuras

- [ ] Agregar tests unitarios con pytest
- [ ] Logging en archivo (log.txt)
- [ ] Caché de parámetros para mejor performance
- [ ] API REST para integración
- [ ] Dashboard web interactivo
- [ ] Soporte para múltiples idiomas

---

**Última actualización:** 2026-06-10  
**Versión:** 2.0 (Modular)
