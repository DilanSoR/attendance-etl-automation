# Automatización ETL de Asistencias

## Descripción

Este proyecto automatiza el procesamiento de archivos Excel de asistencias semanales para programas académicos.

El sistema extrae información desde diferentes formatos de Excel, identifica a los alumnos dentro de una base de datos PostgreSQL y genera scripts SQL para actualizar automáticamente:

- asistencias
- estatus de alumnos (`ACTIVO` / `INACTIVO`)
- bitácoras de seguimiento

El objetivo principal es reducir trabajo manual operativo, mejorar la consistencia de datos y agilizar la sincronización de asistencias.

---

# Funcionalidades

- Procesamiento de múltiples formatos de Excel
- Normalización de nombres y correos
- Identificación automática de alumnos
- Generación automática de scripts SQL
- Actualización de asistencias
- Cambio automático de estatus:
  - `ACTIVO`
  - `INACTIVO`
- Generación de reportes de errores
- Conexión segura mediante túnel SSH
- Procesamiento por grupos y múltiples hojas

---

# Tecnologías utilizadas

- Python
- pandas
- NumPy
- PostgreSQL
- psycopg2
- SSHTunnelForwarder
- OpenPyXL
- python-dotenv

---

# Estructura del proyecto
---
```txt
automatizacion-etl-asistencias/
│
├── connector.py          # Conexión PostgreSQL + túnel SSH
├── query.py              # Capa de consultas SQL
├── microsoft.py          # Procesador de archivos de asistencia
├── requirements.txt
├── .env
├── README.md
│
├── outputs/
│   ├── sql/
│   └── errores/
│
└── input/
    └── asistencias/
```
---
---
##Flujo del proceso:

```
Archivos Excel
      ↓
Extracción de datos
      ↓
Normalización de nombres y correos
      ↓
Identificación de alumnos
      ↓
Validación de asistencias
      ↓
Generación de scripts SQL
      ↓
Actualización de estatus
```
---

##Lógica de negocio

#Los alumnos son identificados mediante:

- nombre completo normalizado
- correo electrónico normalizado
- registros históricos
#Reglas de actualización
- Condición Estatus
- Tiene al menos una asistencia	ACTIVO
- No tiene asistencias en el periodo	INACTIVO

#Los alumnos con estatus:

- BAJA
- CONCLUIDO

no son modificados automáticamente.
---
##Variables de entorno

Crear un archivo .env:

```txt
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=

SSH_HOST=
SSH_PORT=
SSH_USER=
SSH_PASSWORD=
```
---
##Instalación
Clonar repositorio:

```txt
git clone [https://github.com/](https://github.com/DilanSoR/attendance-etl-automation.git)
```

#Instalar dependencias:
```txt
pip install -r requirements.txt
```
---
##Ejemplo de ejecución: 
```txt
python microsoft.py '.\inputs\asistencia.xlsx\'
--grupo 15 \
--hojas "CS" "IA" \
--inicio 2026-05-01 \
--fin 2026-05-07
```
---

##Salidas generadas
Scripts SQL:

```txt
-- 2. ASISTENCIA --
UPDATE asistencia_alumno
SET asistencia = TRUE
WHERE aprobado2_id = 1124 AND fecha = '2026-04-29';

-- 2. ESTATUS Y BITÁCORA --
UPDATE aprobado2
SET estatus = 'ACTIVO'
WHERE id = 1124 AND estatus NOT IN ('BAJA', 'CONCLUIDO');

INSERT
INTO bitacora_estatus
(aprobado2_id, estatus, observacion, fecha)
SELECT 1124, 'ACTIVO', 'Asistencia registrada', NOW()
FROM aprobado2
WHERE id = 1124 AND estatus NOT IN ('BAJA', 'CONCLUIDO');
```
---
##Reportes de registros sin match

Archivos Excel con registros no identificados.

- errores_microsoft_grupo_101.xlsx
---
#Problemas resueltos:

- Diferencias entre formatos de Excel
- Variaciones en nombres y acentos
- Correos faltantes o duplicados
- Automatización del control semanal
- Reducción de trabajo manual
- Sincronización de datos académicos
- Conexión segura a base de datos remota
---
#Mejoras futuras:

- Actualización directa a base de datos
- Dashboard de monitoreo
- Sistema de logs
- Pruebas unitarias
- Dockerización
- Orquestación con Airflow
- Métricas de calidad de datos
---
#Autor:
Eric Dilan Soriano Rosales
---
