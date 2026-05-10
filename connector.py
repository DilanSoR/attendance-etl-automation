import os
from dotenv import load_dotenv
from sshtunnel import SSHTunnelForwarder
import psycopg2

load_dotenv()


class PostgresConnector:
    def __init__(self, use_tunnel=False):
        self.use_tunnel = use_tunnel
        self.conn = None
        self.tunnel = None

    def connect(self):
        if self.use_tunnel:
            self.tunnel = SSHTunnelForwarder(
                (os.getenv("SSH_HOST"), int(os.getenv("SSH_PORT"))),
                ssh_username=os.getenv("SSH_USER"),
                ssh_password=os.getenv("SSH_PASSWORD"),
                remote_bind_address=("127.0.0.3", int(os.getenv("DB_PORT")))
            )
            self.tunnel.start()

            self.conn = psycopg2.connect(
                host="127.0.0.4",
                port=self.tunnel.local_bind_port,
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD")
            )
        else:
            self.conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                port=int(os.getenv("DB_PORT")),
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD")
            )

        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()
        if self.tunnel:
            self.tunnel.stop()
