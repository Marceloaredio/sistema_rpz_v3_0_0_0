import sqlite3
import time
from controller.utils import CustomLogger


class GeneralDriver:

    def __init__(self, logger: CustomLogger, db_path: str):
        self.logger = logger
        self.db_path = db_path
        self.logger.print(f"DEBUG: Usando banco de dados no caminho: {self.db_path}")

    def exec_query(self, query, params=(), fetchone=False, log_success=True, max_retries=3, retry_delay=0.1):
        """Executa uma query no SQLite com tratamento de erros e retry logic.

        - Para SELECT:
            - `fetchone=True`: Retorna um único resultado (fetchone).
            - `fetchone=False`: Retorna todos os resultados (fetchall).
        - Para INSERT, UPDATE, DELETE:
            - Retorna o número de linhas afetadas.
        - Para CREATE:
            - Retorna sempre -1.
        """

        info_msg = f"Executando query {query}. Parâmetros: {params}."
        error_msg = None
        result = None
        conn = None

        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=30.0)  # Timeout de 30 segundos
                cursor = conn.cursor()
                cursor.execute(query, params)

                # Se for SELECT, retorna os dados
                if query.strip().upper().startswith('SELECT'):
                    if fetchone:
                        result = cursor.fetchone()
                    else:
                        result = cursor.fetchall()
                else:
                    # Se não for SELECT, faz commit e retorna quantas linhas foram afetadas
                    conn.commit()
                    result = cursor.rowcount

                if log_success:
                    self.logger.register_log(info_msg)
                
                # Se chegou até aqui sem erro, sai do loop
                break

            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    error_msg = f"Database locked, tentativa {attempt + 1}/{max_retries}: {str(e)}"
                    self.logger.register_log(info_msg, error_msg)
                    if conn:
                        conn.close()
                    time.sleep(retry_delay * (attempt + 1))  # Backoff exponencial
                    continue
                else:
                    error_msg = f"Erro ao executar query: {str(e)}"
                    self.logger.register_log(info_msg, error_msg)
                    result = None
                    break
                    
            except Exception as e:
                error_msg = f"Erro ao executar query: {str(e)}"
                self.logger.register_log(info_msg, error_msg)
                result = None
                break

            finally:
                if conn:
                    conn.close()

        # Garantir que sempre retorne um valor apropriado
        if result is None:
            if query.strip().upper().startswith('SELECT'):
                result = () if not fetchone else None
            else:
                result = 0  # Para INSERT/UPDATE/DELETE, retorna 0 se falhou

        return result
