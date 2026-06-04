# Especificación Funcional: Motor de Validación de Datos Maestros de Proveedores

Este documento detalla el diseño funcional y las reglas lógicas para el desarrollo de un validador automatizado de datos maestros de proveedores en Oracle EBS. Su propósito es auditar de forma masiva y automática que los registros cumplan con las directrices de negocio antes de ser procesados o aprobados.

---

## 1. Entradas del Sistema (Inputs)

El sistema requiere tres fuentes de información para ejecutarse:

1. **Archivo de Cabeceras (Header View):** Un reporte exportado de Oracle (formato tabular CSV o TXT) que contiene la información general del proveedor (Número de proveedor, nombre, tipo, estado global, prioridad global y país de origen configurado en un campo adicional DFF).
2. **Archivo de Sitios de Pago (PaySite View):** Un reporte exportado de Oracle (formato tabular CSV o TXT) que contiene la información a nivel de sucursales o sitios individuales (Estado del sitio, país del sitio, prioridad del sitio, fechas de inactividad, líneas de dirección y el código de comisión bancaria ATTRIBUTE6).
3. **Matriz de Reglas (Parámetros.xlsx):** Un archivo Excel gestionado por el negocio que sirve como base de conocimiento para las validaciones. Contiene cinco pestañas:
   * **Hoja1 (Reglas por tipo):** Parámetros obligatorios (intereses, fletes, prioridades) según el tipo de proveedor (Empleado, Fideicomiso, etc.).
   * **Geographic_Mapping (Traducción):** Relación para convertir los nombres largos de países en Oracle a códigos ISO de 2 letras.
   * **Geographic_Rules (Reglas por país):** Reglas geográficas específicas que asocian el país del sitio con los nombres permitidos, prioridades permitidas y la comisión esperada (ATTRIBUTE6).
   * **Address_Format_Rules (Formatos de Cuenta):** Expresiones regulares (regex) para validar que los datos bancarios ingresados en las líneas de dirección coincidan con los formatos exigidos por los bancos locales.
   * **Terms_Definitions (Definiciones de Términos):** Opcional. Catálogo que mapea los identificadores numéricos de plazos de pago (`TERMS_ID`) con sus descripciones amigables (ej: `10087` -> `Immediate`) para que los reportes de auditoría muestren nombres legibles en lugar de números ID.

---

## 2. Controles Lógicos a Ejecutar

El motor debe iterar sobre cada registro y realizar los siguientes controles sin codificar reglas fijas (todo debe ser dinámico, consumido desde la Matriz de Reglas):

### Control 1: Integridad y Relación de Datos
* **Descripción:** Comprobar que cada registro del archivo de sitios tenga su correspondiente registro padre en el archivo de cabeceras mediante el identificador único del proveedor (`VENDOR_ID`).
* **Severidad si falla:** CRÍTICO.

### Control 2: Obligatoriedad de Campos Clave
* **Descripción:** Verificar que campos obligatorios a nivel de cabecera como el "Tipo de Proveedor" (`VENDOR_TYPE_LOOKUP_CODE`) y a nivel de sitios de pago (`PAY`) como la "Comisión Bancaria" (`ATTRIBUTE6`) no se encuentren vacíos o en blanco.
  * *Nota importante:* Para los sitios de compras (`PUR`), el campo de comisión bancaria (`ATTRIBUTE6`, es decir, `OUR` o `BEN`) no es obligatorio y se debe ignorar en la validación.
* **Severidad si falla:** CRÍTICO (para tipo de proveedor) / ERROR (para comisión bancaria en sitios PAY).

### Control 3: Validación de Reglas Paramétricas (Hoja1)
* **Descripción:** Para cada proveedor, identificar su tipo de proveedor en la matriz y validar que coincidan exactamente sus parámetros de:
  * Bandera de cálculo automático de intereses.
  * Bandera de exclusión de fletes de descuentos.
  * Obligatoriedad de Términos de Pago (si la matriz indica 'Y', el campo en el reporte no puede estar vacío).
  * Obligatoriedad de Prioridad de Pago.
* **Severidad si falla:** ERROR (o ADVERTENCIA en casos específicos como intereses en fideicomisos).

### Control 4: Consistencia Geográfica entre Cabecera y Sitios
* **Descripción:** Traducir el país del DFF de cabecera a código ISO. 
  * Para proveedores de tipo Servicios o Fideicomisos, el país declarado en sus sitios de compras (PUR) debe ser idéntico al país ISO de su cabecera.
  * Para proveedores de tipo Empleados o Reclamos, el país declarado en sus sitios de pagos (PAY) debe ser idéntico al país ISO de su cabecera.
* **Severidad si falla:** ERROR.

### Control 5: Consistencia de Estado Activo e Inactividad
* **Descripción:** Si un proveedor global se encuentra habilitado (`ENABLED_FLAG` = 'Y'), emitir una alerta si alguno de sus sitios individuales tiene configurada una fecha de baja o inactividad (`INACTIVE_DATE`).
* **Severidad si falla:** ADVERTENCIA.

### Control 6: Control Geográfico de Canales de Pago (Sitios PAY)
* **Descripción:** Para los sitios de tipo pago (PAY), buscar las reglas de su país en la pestaña `Geographic_Rules`. El nombre del sitio debe cumplir con alguno de los patrones permitidos (ej: empezar con "ACH LOCAL" para Panamá, o "BANK TRANSFER" para el extranjero). Si coincide con el patrón:
  * La prioridad del sitio de pagos en Oracle debe estar en la lista de prioridades permitidas del Excel (ej: 99, 71 o 73).
  * La comisión bancaria (`ATTRIBUTE6`) debe coincidir exactamente con la esperada (ej: 'OUR' o 'BEN').
* **Severidad si falla:** ERROR.

### Control 7: Validación de Formato de Cuentas Bancarias
* **Descripción:** Para sitios que contengan datos bancarios en sus líneas de dirección (ej: "ACH LOCAL"), buscar en `Address_Format_Rules` qué columna y qué expresión regular (regex) le aplica. Validar que el texto ingresado en Oracle cumpla estrictamente con dicho formato (ej: contener exactamente "CTA#..." y "ABA#...").
* **Severidad si falla:** ERROR.

### Control 8: Consistencia de Términos y Prioridades de Pago (Header vs Sitios)
* **Descripción:** Para cada sitio de un proveedor, comparar que su término de pago (`TERMS_ID`) y prioridad de pago (`PAYMENT_PRIORITY`) coincidan exactamente con lo configurado a nivel global en la cabecera (Header). Esto previene que se alteren las condiciones de cobro del sitio sin sincronizar con la cabecera general. 
  * Si la pestaña `Terms_Definitions` existe en la matriz, los códigos numéricos de plazos se traducen a nombres descriptivos antes de reportarse.
* **Severidad si falla:** ERROR.

---

## 3. Salidas Esperadas (Outputs)

Cuando el motor finaliza la validación, debe generar dos reportes que consoliden todas las excepciones (desviaciones) encontradas:

1. **Reporte en Excel (`Reporte_Auditoria_EBS_Proveedores.xlsx`):** Una lista tabular estructurada para análisis masivo, que contiene las columnas:
   * Número de Proveedor
   * Nombre del Proveedor
   * Código de Sitio (o 'HEADER' si la falla ocurrió a nivel global)
   * Campo Auditado (nombre del campo que falló)
   * Valor en Oracle (el valor incorrecto encontrado)
   * Regla Esperada (el valor o condición exigido por la matriz)
   * Tipo de Control (ej: Obligatoriedad, Consistencia, Formato)
   * Nivel de Riesgo (Crítico, Error, Advertencia)
2. **Reporte en HTML (`Reporte_Auditoria_EBS_Proveedores.html`):** Un informe interactivo y estético con diseño profesional, tipografía Inter, tarjetas con métricas de resumen (fecha de ejecución y total de excepciones), y una tabla responsiva con insignias coloreadas para facilitar una lectura rápida y la toma de decisiones por los analistas.
