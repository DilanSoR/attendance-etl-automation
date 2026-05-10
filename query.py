import pandas as pd
import connector


class Consulta:
    def __init__(self, use_tunnel=True):
        self.use_tunnel = use_tunnel

    def ejecutar(self, query: str) -> pd.DataFrame:
        db = connector.PostgresConnector(use_tunnel=self.use_tunnel)
        conn = db.connect()

        try:
            df = pd.read_sql(query, conn)
            return df
        finally:
            db.close()

    def aprobado2(self) -> pd.DataFrame:
        query = """
        SELECT
            id,
            nombre,
            apellido_paterno,
            apellido_materno,
            correo,
            correo2,
            correo_alt,
            correo_asignado,
            certificadora,
            curso, 
            grupo_id AS grupo_id_aprobados2
        FROM aprobado2
        WHERE desactivado = false;
        """
        return self.ejecutar(query)

    def historico_aprobado2(self) -> pd.DataFrame:
        query = """
        SELECT
            a.nombre|| ' ' || a.apellido_paterno|| ' ' ||a.apellido_materno as nombre_completo,
            a.apellido_paterno|| ' ' ||a.apellido_materno|| ' ' ||a.nombre as nombre_completo_alreves,
            h.nombre_completo as nombre_completo_archivo,
            h.grupo_id,
            a.correo,
            a.correo2,
            a.correo_alt,
            a.correo_asignado,
            h.correo as correo_archivo,
            a.id as id_aprobado,
            a.folio_seguimiento,
            a.estatus,
            a.curp,
            a.grupo_id AS grupo_id_aprobados2
        FROM aprobado2 a 
            left join historico_asistencias h on h.id_aprobado2 =a.id 
        WHERE a.desactivado = FALSE AND a.estatus NOT IN ('BAJA', 'CONCLUIDO');
        """
        return self.ejecutar(query)
