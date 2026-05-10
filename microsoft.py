import pandas as pd
import numpy as np
import argparse
from query import Consulta


def normalizar_texto(texto):
    if pd.isna(texto):
        return ""
    return str(texto).strip().upper().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")


def procesar_hoja_estilo_microsoft(archivo, hoja, df_historico, fecha_inicio, fecha_fin):
    print(f"\n--- Procesando Hoja: {hoja} ---")
    try:
        # Cargamos la hoja sin procesar fechas automáticamente para evitar saltos
        df = pd.read_excel(archivo, sheet_name=hoja)

        # Convertimos fechas de entrada a objetos date para comparar
        f_ini_dt = pd.to_datetime(fecha_inicio).date()
        f_fin_dt = pd.to_datetime(fecha_fin).date()

        columnas_validas = []

        # Identificar columnas de fecha
        for col in df.columns:
            try:
                # Forzamos conversión a string y quitamos la hora si existe
                # Esto evita que el objeto datetime ruede al día siguiente
                col_str = str(col).split(' ')[0]

                # Convertimos a fecha para validar rango
                fecha_dt = pd.to_datetime(col_str)
                fecha_col = fecha_dt.date()

                if f_ini_dt <= fecha_col <= f_fin_dt:
                    # Guardamos el nombre real de la columna y el string de fecha fijo
                    # Usamos .strftime directamente aquí para que no cambie después
                    fecha_sql_fija = fecha_col.strftime('%Y-%m-%d')
                    columnas_validas.append((col, fecha_sql_fija))
                    print(
                        f"   [OK] Columna detectada: {col} -> {fecha_sql_fija}")
            except:
                continue

        if not columnas_validas:
            print(
                f"   [!] No se detectaron fechas en el rango {f_ini_dt} a {f_fin_dt}")
            return [], set(), set(), []

        # Mapeo de columnas de texto (Nombre y Correo)
        # Buscamos las columnas reales aunque tengan espacios o mayúsculas
        mapeo_cols = {str(c).strip().lower(): c for c in df.columns}
        col_nombre_real = mapeo_cols.get("nombre completo")
        col_correo_real = mapeo_cols.get("correo electronico")

        if not col_nombre_real:
            print(
                f"   [!] ERROR: No existe la columna 'Nombre Completo' en la hoja {hoja}")
            return [], set(), set(), []

        # Normalización para Match
        df["nombre_norm"] = df[col_nombre_real].apply(normalizar_texto)
        if col_correo_real:
            df["correo_norm"] = df[col_correo_real].fillna(
                "").astype(str).str.strip().str.lower()
        else:
            df["correo_norm"] = ""

        sql_scripts = []
        ids_con_presencia = set()
        ids_totales_procesados = set()
        errores_hoja = []

        for _, row in df.iterrows():
            idx = None
            # Intento 1: Por Nombre
            match = df_historico[df_historico['nombre_archivo_norm']
                                 == row['nombre_norm']]

            # Intento 2: Por Correo
            if (match is None or match.empty) and row['correo_norm']:
                match = df_historico[df_historico['correo_archivo_norm']
                                     == row['correo_norm']]

            if match is not None and not match.empty:
                idx = int(match.iloc[0]['id_aprobado'])
            else:
                if pd.notna(row[col_nombre_real]):
                    errores_hoja.append({
                        "nombre": row[col_nombre_real],
                        "correo": row[col_correo_real] if col_correo_real else "N/A",
                        "hoja": hoja
                    })
                continue

            ids_totales_procesados.add(idx)

            # Generar SQL con la fecha fija que guardamos en 'columnas_validas'
            for col_original, f_sql in columnas_validas:
                valor = str(row[col_original]).strip().upper()
                es_presente = valor in ['1', '1.0', 'TRUE', 'X']
                asistencia_val = "TRUE" if es_presente else "FALSE"

                if es_presente:
                    ids_con_presencia.add(idx)

                # AQUÍ USAMOS f_sql QUE YA ES UN STRING SEGURO
                sql_scripts.append(
                    f"UPDATE asistencia_alumno SET asistencia = {asistencia_val} WHERE aprobado2_id = {idx} AND fecha = '{f_sql}';"
                )

        return sql_scripts, ids_con_presencia, ids_totales_procesados, errores_hoja

    except Exception as e:
        print(f"   [!] Error crítico en hoja {hoja}: {e}")
        return [], set(), set(), []


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--grupo", type=int, required=True)
    parser.add_argument("--hojas", nargs='+', required=True)
    parser.add_argument("--inicio", required=True)
    parser.add_argument("--fin", required=True)
    args = parser.parse_args()

    # 1. Obtener Histórico
    consulta = Consulta(use_tunnel=True)
    df_h = consulta.historico_aprobado2()
    df_h = df_h[df_h['grupo_id'] == args.grupo].copy()
    df_h['nombre_archivo_norm'] = df_h['nombre_completo_archivo'].apply(
        normalizar_texto)
    df_h['correo_archivo_norm'] = df_h['correo_archivo'].fillna(
        "").astype(str).str.strip().str.lower()

    todos_los_errores = []

    # 2. Procesar cada hoja solicitada
    for hoja in args.hojas:
        scripts, presencia, procesados, errs = procesar_hoja_estilo_microsoft(
            args.input, hoja, df_h, args.inicio, args.fin
        )

        todos_los_errores.extend(errs)

        if scripts:
            nombre_sql = f"./outputs/scripts_microsoft_{hoja.replace(' ', '_').lower()}.sql"
            with open(nombre_sql, "w", encoding="utf-8") as f:
                f.write(
                    f"-- SQL MICROSOFT | HOJA: {hoja} | GRUPO {args.grupo} | RANGO {args.inicio}/{args.fin}\n\n")

                f.write("-- 1. ASISTENCIAS --\n")
                f.write("\n".join(scripts) + "\n\n")

                f.write("-- 2. ESTATUS Y BITÁCORA --\n")
                ids_para_inactivar = procesados - presencia

                # ACTIVOS
                for idx in sorted(list(presencia)):
                    f.write(
                        f"UPDATE aprobado2 SET estatus = 'ACTIVO' WHERE id = {idx} AND estatus NOT IN ('BAJA', 'CONCLUIDO');\n")
                    f.write(f"INSERT INTO bitacora_estatus (aprobado2_id, estatus, observacion, fecha) "
                            f"SELECT {idx}, 'ACTIVO', 'Asistencia registrada', NOW() "
                            f"FROM aprobado2 WHERE id = {idx} AND estatus NOT IN ('BAJA', 'CONCLUIDO');\n")

                # INACTIVOS
                f.write("\n-- INACTIVOS (SIN ASISTENCIA EN EL PERIODO) --\n")
                for idx in sorted(list(ids_para_inactivar)):
                    f.write(
                        f"UPDATE aprobado2 SET estatus = 'INACTIVO' WHERE id = {idx} AND estatus NOT IN ('BAJA', 'CONCLUIDO');\n")
                    f.write(f"INSERT INTO bitacora_estatus (aprobado2_id, estatus, observacion, fecha) "
                            f"SELECT {idx}, 'INACTIVO', 'Inasistencia registrada', NOW() "
                            f"FROM aprobado2 WHERE id = {idx} AND estatus NOT IN ('BAJA', 'CONCLUIDO');\n")

            print(f">>> Éxito: {nombre_sql} generado.")

    # 3. Reporte de errores
    if todos_los_errores:
        df_err = pd.DataFrame(todos_los_errores)
        err_out = f"./outputs/errores_microsoft_grupo_{args.grupo}.xlsx"
        df_err.to_excel(err_out, index=False)
        print(
            f"\n[!] Match incompleto: {len(todos_los_errores)} registros. Ver: {err_out}")
    else:
        print("\n[OK] Match perfecto en todas las hojas.")
