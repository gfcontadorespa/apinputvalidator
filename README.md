# Motor de Auditoría y Validación - Oracle EBS Proveedores

Este proyecto proporciona un motor de validación dinámico en Python para auditar la integridad y el cumplimiento de las políticas de datos maestros de los proveedores y sus sitios de pago antes de ser integrados o procesados en Oracle EBS.

El motor valida consistencias geográficas, obligatoriedad de campos de control, formatos bancarios, y prioridades de pago en base a reglas dinámicas parametrizables.

---

## 🛠️ Requisitos e Instalación

Este script es completamente portátil y puede ejecutarse en cualquier sistema (Windows, Mac o Linux).

### 1. Instalación de Dependencias
Abre tu consola o terminal y ejecuta el siguiente comando para instalar las librerías necesarias:
```bash
pip install pandas openpyxl
```

### 2. Estructura de Archivos Recomendada
Para que el script funcione de forma portátil sin cambiar el código, mantén esta estructura en la misma carpeta:
```text
📁 Carpeta_Proyecto/
├── 📄 revisor.py             # Script de validación (este archivo)
├── 📊 Parámetros.xlsx         # Matriz de reglas y parámetros
└── 📁 ExampleData/           # Opcional: Carpeta con reportes de prueba
```

---

## 📥 Archivos de Entrada (Oracle EBS Reports)

El motor procesa dos reportes delimitados por tabuladores exportados desde Oracle (generalmente codificados en `UTF-16LE` o `UTF-8`):

1. **Reporte de Cabeceras (Header)**: Contiene información general del proveedor (`VENDOR_ID`, `VENDOR_TYPE_LOOKUP_CODE`, `PAYMENT_PRIORITY`, `EXCLUDE_FREIGHT_FROM_DISCOUNT`, `PAIS_DFF_ATT1`, etc.).
2. **Reporte de Sitios (PaySite)**: Contiene información específica de las ubicaciones y canales de pago (`SITE_STATUS`, `VENDOR_SITE_CODE`, `COUNTRY`, `PAYMENT_PRIORITY`, `ATTRIBUTE6` (Comisión Bancaria), `ADDRESS_LINE2`, `ADDRESS_LINE3`, etc.).

---

## ⚙️ Configuración del Negocio (Matriz de Parámetros)

El archivo de configuración principal es **`Parámetros.xlsx`**. Contiene **4 pestañas** que definen de forma dinámica el comportamiento del motor de validación:

### 1. Pestaña `Hoja1` (Reglas por Tipo de Proveedor)
Define políticas globales para cada tipo de proveedor (`VENDOR_TYPE_LOOKUP_CODE`):
* **`PAYMENT_PRIORITY`** (Y/N): Si está en **`Y`**, la prioridad es obligatoria en cabecera.
* **`TERMS_ID`** (Y/N): Si está en **`Y`**, los términos de pago son obligatorios.
* **`EXCLUDE_FREIGHT_FROM_DISCOUNT`** (Y/N): Define el valor exacto esperado para exclusión de fletes.
* **`AUTO_CALCULATE_INTEREST_FLAG`** (Y/N): Define el valor exacto esperado para cálculo de intereses.

### 2. Pestaña `Geographic_Mapping` (Mapeo de Países)
Traduce nombres de países libres de Oracle a códigos ISO de 2 caracteres:
* **`PAIS_DFF_HEADER`**: Nombre del país como viene en la cabecera (ej. *Sweden, Republica de Panama*).
* **`CODIGO_ISO_ESPERADO`**: Código ISO de 2 caracteres (ej. *SE, PA*).

### 3. Pestaña `Geographic_Rules` (Reglas de Sitios por País)
Define las políticas de prioridad de pago y canal bancario por país para sitios de pago (`PAY`):
* **`COUNTRY_ISO`**: Código de país del sitio (ej. *PA, US, DEFAULT*).
* **`SITE_CODE_PATTERN`**: Patrón que debe tener el sitio (soporta comodines como `ACH LOCAL*`, `BANK TRANSFER*`).
* **`ALLOWED_PRIORITIES`**: Prioridades permitidas separadas por coma (ej. *99,71,73* o *50*).
* **`ATTRIBUTE6_ESPERADO`**: Comisión bancaria esperada (ej. *OUR* o *BEN*).

### 4. Pestaña `Address_Format_Rules` (Validaciones de Cuenta/Dirección)
Valida expresiones regulares para campos de dirección bancaria según el nombre del sitio:
* **`SITE_CODE`**: Sitio al que aplica la regla (ej. *ACH LOCAL*).
* **`COLUMN_NAME`**: Nombre de la columna de dirección a evaluar (ej. *ADDRESS_LINE2*).
* **`REGEX_PATTERN`**: Expresión regular que debe cumplir (ej. *`^RUTA Y TRANSITO #[0-9]{9}$`*).
* **`REGLA_ESPERADA`**: Mensaje explicativo del formato esperado.

---

## 🔍 Reglas de Validación Ejecutadas

El script realiza la auditoría dividida en las siguientes fases:

### 1. Carga Inteligente de Archivos (Autodetect)
El script intenta decodificar los reportes utilizando automáticamente `utf-16` (formato estándar de exportación de Oracle), `utf-8` o `latin-1` para evitar caídas de ejecución.

### 2. Integridad de Datos
* Comprueba que cada registro del archivo de **Sitios (PaySite)** tenga un registro padre correspondiente en el archivo de **Cabeceras (Header)** asociado por el `VENDOR_ID`.

### 3. Controles Paramétricos desde la Matriz (`Hoja1`)
A nivel de cabecera (`Header`), se validan dinámicamente las reglas configuradas en el Excel de parámetros para cada tipo de proveedor:
* **Intereses**: Comprueba que `AUTO_CALCULATE_INTEREST_FLAG` coincida con el valor parametrizado.
* **Fletes**: Comprueba que `EXCLUDE_FREIGHT_FROM_DISCOUNT` coincida con el valor parametrizado.
* **Obligatoriedad de Plazos**: Si `TERMS_ID` es `'Y'`, alerta si el campo está vacío.
* **Obligatoriedad de Prioridad**: Si `PAYMENT_PRIORITY` es `'Y'`, alerta si la prioridad de cabecera está vacía.

### 4. Obligatoriedad de Campos Críticos
* Valida de manera obligatoria que el tipo de proveedor (**`VENDOR_TYPE_LOOKUP_CODE`**) no esté en blanco en la cabecera del registro (Severidad: **`CRÍTICO`**).

### 5. Consistencia de País
* Para proveedores de tipo `Miscellaneous Services` o `Trust`, comprueba que el país del sitio de compras (`PUR Site`) coincida con el país traducido (`PAIS_DFF_ATT1`) de la cabecera.
* Para proveedores de tipo `Employees` o `Claims`, realiza la misma validación sobre el sitio de pagos (`PAY Site`).

### 6. Controles Geográficos y de Canales (Sitios de Pago `PAY`)
Se auditan de forma estricta el nombre del sitio (`VENDOR_SITE_CODE`), su prioridad y su comisión bancaria (`ATTRIBUTE6`) según el país:

* **Panamá (Locales)**:
  * El sitio de pago debe comenzar con **`ACH LOCAL`**.
  * La prioridad de pago debe ser **`99`**, **`71`** o **`73`**.
  * La comisión bancaria (`ATTRIBUTE6`) debe ser exactamente **`OUR`** (y no puede quedar en blanco).
* **Estados Unidos (US)**:
  * El sitio de pago debe llamarse o contener **`ACH USA`** o **`BANK TRANSFER`**.
  * La prioridad de pago debe ser exactamente **`50`**.
  * Si el sitio es `ACH USA`, la comisión bancaria debe ser **`OUR`**. Si es `BANK TRANSFER`, debe ser **`BEN`**.
* **Resto del Mundo (Extranjeros no EE.UU.)**:
  * El sitio de pago debe contener **`BANK TRANSFER`**.
  * La prioridad de pago debe ser exactamente **`50`**.
  * La comisión bancaria (`ATTRIBUTE6`) debe ser **`BEN`** (y no puede quedar en blanco).

### 7. Formato y Expresiones Regulares bancarias
Para sitios locales que utilicen el canal **`ACH LOCAL`**, se valida que la información bancaria ingresada en las direcciones de Oracle cumpla con los estándares correctos:
* **`ADDRESS_LINE2`**: Debe cumplir exactamente con el formato `RUTA Y TRANSITO #[9 dígitos]` (ej. *RUTA Y TRANSITO #123456789*).
* **`ADDRESS_LINE3`**: Debe cumplir exactamente con el formato `CTA#[Número] ABA#[3 dígitos]` (ej. *CTA#12345678 ABA#012*).

### 8. Conflicto de Fechas de Inactividad
* Si un proveedor global está habilitado (`ENABLED_FLAG == 'Y'`), el sistema emite una advertencia si su sitio individual ya posee una fecha de baja (`INACTIVE_DATE`).

---

## 🚀 Cómo Ejecutar el Auditor

### Opción A: Interfaz Gráfica (Doble clic / Ejecución Local)
Si ejecutas el script directamente (ej. abriendo [revisor.py](file:///Users/joslu/Documents/Github%20Repositories/OraValidation/revisor.py) o haciendo doble clic):
1. Se abrirá una primera ventana emergente para que selecciones el **Reporte de Cabeceras (Header)**.
2. Se abrirá una segunda ventana para seleccionar el **Reporte de Sitios (PaySite)**.
3. El script correrá la validación y generará el resultado.

### Opción B: Ejecución por Consola / Automatizada (CLI)
Puedes pasar las rutas de los archivos como argumentos en tu consola:
```bash
python revisor.py "ruta/al/Header.csv" "ruta/al/PaySite.csv"
```

### Opción C: Ejecución en Entorno No Interactivo / Headless
Si el script no detecta interfaz gráfica y estás en la carpeta del repositorio, cargará de forma automática los archivos de prueba ubicados en la carpeta `ExampleData/`.

---

## 📊 Reporte de Resultados

Al finalizar, si se encuentran inconsistencias, el script generará automáticamente un archivo llamado **`Reporte_Auditoria_EBS_Proveedores.xlsx`** en la misma carpeta. El reporte detalla:

* **VENDOR_NUMBER** y **VENDOR_NAME**: Identificación del proveedor.
* **VENDOR_SITE_CODE**: Nombre del sitio evaluado (`HEADER` para controles globales).
* **CAMPO_AUDITADO**: El campo específico que generó la alerta.
* **VALOR_ORACLE**: El valor incorrecto o vacío que tiene Oracle actualmente.
* **REGLA_ESPERADA**: La explicación en texto de cómo debería estar configurado ese campo.
* **TIPO_CONTROL**: Clasificación de la regla (Integridad, Formato, Obligatoriedad, Paramétrico).
* **NIVEL_RIESGO**: Gravedad del hallazgo (**`CRÍTICO`**, **`ERROR`** o **`ADVERTENCIA`**).

Si los datos están 100% correctos y limpios, no se creará el reporte y la consola confirmará que los datos están alineados.
