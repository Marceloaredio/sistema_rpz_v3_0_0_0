from controller.utils import CustomLogger
from typing import List, Tuple, Optional
from model.drivers.general_driver import GeneralDriver
import json
import sqlite3


class UserDriver(GeneralDriver):

    def __init__(self, logger: CustomLogger, db_path: str):

        GeneralDriver.__init__(self, logger=logger, db_path=db_path)
        self.create_table()

    def create_table(self):
        self.logger.print("Executando create table")

        # Nova estrutura com is_admin em vez de roles
        query = '''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        is_admin INTEGER DEFAULT 0 CHECK (is_admin in (0, 1)),
                        authorized_routes TEXT DEFAULT '[]'
                    )
        '''

        self.exec_query(query, log_success=False)
        
        # Migração automática das colunas
        self._migrate_to_is_admin_system()
        
        # Limpar setores automáticos de usuários existentes
        self.clean_automatic_sectors_from_users()

        self.logger.print("Create table executado com sucesso.")

    def _migrate_to_is_admin_system(self):
        """Migra da estrutura role para is_admin"""
        try:
            # Verificar se as colunas já existem usando uma query direta
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar quais colunas existem
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns] if columns else []
            
            self.logger.print(f"Colunas existentes na tabela users: {column_names}")
            
            # Se a coluna role ainda existe, fazer migração completa
            if 'role' in column_names:
                self.logger.print("Removendo coluna role e migrando para estrutura nova...")
                
                # 1. Criar tabela temporária com estrutura correta
                cursor.execute('''
                    CREATE TABLE users_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        is_admin INTEGER DEFAULT 0 CHECK (is_admin in (0, 1)),
                        authorized_routes TEXT DEFAULT '[]'
                    )
                ''')
                
                # 2. Copiar dados da tabela antiga para a nova, convertendo role para is_admin
                if 'is_admin' in column_names:
                    # Se is_admin já existe, usar ele
                    cursor.execute('''
                        INSERT INTO users_new (id, name, email, password, is_admin, authorized_routes)
                        SELECT id, name, email, password, is_admin, 
                               COALESCE(authorized_routes, '[]') 
                        FROM users
                    ''')
                else:
                    # Se is_admin não existe, converter baseado no role
                    cursor.execute('''
                        INSERT INTO users_new (id, name, email, password, is_admin, authorized_routes)
                        SELECT id, name, email, password, 
                               CASE WHEN role = 'administrador' THEN 1 ELSE 0 END,
                               '[]'
                        FROM users
                    ''')
                
                # 3. Remover tabela antiga
                cursor.execute('DROP TABLE users')
                
                # 4. Renomear tabela nova
                cursor.execute('ALTER TABLE users_new RENAME TO users')
                
                conn.commit()
                self.logger.print("Migração completa concluída - coluna role removida.")
                
            elif 'is_admin' not in column_names:
                # Adicionar is_admin se não existir
                self.logger.print("Adicionando coluna is_admin...")
                cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
                conn.commit()
                self.logger.print("Coluna is_admin adicionada.")
            
            # Verificar se authorized_routes existe
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if 'authorized_routes' not in column_names:
                self.logger.print("Adicionando coluna authorized_routes...")
                cursor.execute("ALTER TABLE users ADD COLUMN authorized_routes TEXT DEFAULT '[]'")
                conn.commit()
                self.logger.print("Coluna authorized_routes adicionada.")
                
            conn.close()
            
            # Verificar estrutura final
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(users)")
            final_columns = cursor.fetchall()
            final_column_names = [col[1] for col in final_columns]
            conn.close()
            
            self.logger.print(f"Estrutura final da tabela users: {final_column_names}")
                
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            self.logger.register_log("Erro ao migrar tabela users para sistema is_admin", str(e))

    def create_user(self, name: str, email: str, password: str, is_admin: bool = False, authorized_routes: str = '[]'):
        self.logger.print(f"Adicionando usuário: name: {name}, "
                          f"user: {email}, pass: {password}, is_admin: {is_admin}.")

        # Garantir que "Comum" sempre esteja presente nos setores autorizados
        try:
            authorized_sectors = json.loads(authorized_routes) if authorized_routes else []
            if "Comum" not in authorized_sectors:
                authorized_sectors.append("Comum")
            authorized_routes = json.dumps(authorized_sectors)
        except (json.JSONDecodeError, TypeError):
            authorized_routes = '["Comum"]'

        # Usar sempre a estrutura nova sem coluna role
        query = """
            INSERT INTO users (name, email, password, is_admin, authorized_routes)
            VALUES (?, ?, ?, ?, ?)
        """
        params = (name, email, password, int(is_admin), authorized_routes)

        try:
            row_count = self.exec_query(query=query, params=params)
            self.logger.print(f"Linhas afetadas: {row_count}")
            return row_count
            
        except Exception as e:
            self.logger.register_log(f"Erro ao criar usuário {email}", str(e))
            return 0

    def delete_user(self, where_columns: list, where_values: tuple) -> int:
        """
        Deleta o registro de um usuário no banco de dados com base nos parâmetros fornecidos.

        :param where_columns: Lista de colunas usadas para filtrar a exclusão.
        :type where_columns: list
        :param where_values: Valores correspondentes às colunas de filtro.
        :type where_values: tuple
        :return: None
        :rtype: None
        """
        self.logger.register_log(f"Deletando usuário da tabela com dado(s) '{where_values}' "
                                 f"na(s) coluna(s) '{where_columns}'.")

        where_clause = " AND ".join([f"{col}=?" for col in where_columns])

        query = f"DELETE FROM users WHERE {where_clause}"

        delete_data = ", ".join([f"{where_columns[i]}: {where_values[i]}" for i in range(len(where_values))])

        # Executa a query usando o método `exec_query`
        row_count = self.exec_query(query=query,
                                    params=where_values)

        self.logger.print(f"{row_count} linhas afetadas ao excluir o usuário com os dados {delete_data}.")

        return row_count

    def update_user(self,
                    set_columns: list,
                    set_values: tuple,
                    where_columns: list,
                    where_values: tuple) -> int:
        """
        Atualiza informações de um usuário no banco de dados.
        Se a atualização for bem-sucedida, a operação será confirmada.

        :param set_columns: Lista de colunas a serem atualizadas.
        :type set_columns: list
        :param set_values: Valores correspondentes às colunas a serem atualizadas.
        :type set_values: tuple
        :param where_columns: Lista de colunas usadas para encontrar o usuário.
        :type where_columns: list
        :param where_values: Valores correspondentes às colunas de busca.
        :type where_values: tuple
        :return: None.
        :rtype: None
        """

        if not set_columns or not set_values or len(set_columns) != len(set_values):
            raise ValueError(
                "Os parâmetros 'set_columns' e 'set_values' devem ter o mesmo tamanho e não podem ser vazios.")

        if not where_columns or not where_values or len(where_columns) != len(where_values):
            raise ValueError(
                "Os parâmetros 'where_columns' e 'where_values' devem ter o mesmo tamanho e não podem ser vazios.")

        # Construção dinâmica das cláusulas SET e WHERE
        set_clause = ", ".join([f"{col}=?" for col in set_columns])
        where_clause = " AND ".join([f"{col}=?" for col in where_columns])

        # Construção final da query
        query = f"UPDATE users SET {set_clause} WHERE {where_clause}"

        # Executa a query usando o método `exec_query`
        row_count = self.exec_query(query=query,
                                    params=set_values + where_values,
                                    fetchone=False,
                                    log_success=True)

        return row_count

    def retrieve_user(self, where_columns: List[str], where_values: Tuple) -> Optional[Tuple]:
        """
        Consulta um usuário no banco de dados. Se existir, retorna os dados completos do usuário.
        Se não existir, retorna None.

        :param where_columns: Lista de colunas para filtrar a busca. Exemplo: ['email', 'id_telegram']
        :type where_columns: list
        :param where_values: Valores correspondentes às colunas em 'where_columns'.
        Exemplo: ['example@example.com', 12345]
        :type where_values: tuple
        :return: Dados do usuário encontrados na tabela ou None caso não exista.
        :rtype: tuple or None
        """

        self.logger.print(f"Consultando no BD por usuário com dado(s) {where_values} na(s) coluna(s) {where_columns}.")

        if not where_columns or not where_values or len(where_columns) != len(where_values):
            raise ValueError(
                "Os parâmetros 'where_columns' e 'where_values' devem ter o mesmo tamanho e não podem ser vazios.")

        conditions = " AND ".join([f"{col}=?" for col in where_columns])
        query = f"SELECT name, email, password, is_admin, authorized_routes FROM users WHERE {conditions}"

        user_data = ''

        for i in range(len(where_values)):
            user_data = user_data + f'{where_columns[i]}: {where_values[i]}, '.strip(', ')

        user = self.exec_query(query=query,
                               params=where_values,
                               fetchone=True,
                               log_success=False)

        return user

    def retrieve_all_users(self) -> list:
        """
        Retorna uma lista contendo todos os dados de todos os usuários.

        :return: Uma lista contendo todos os dados de todos os usuários.
        :rtype: list(tuple)
        """

        self.logger.print("Consultando todos usuários da tabela.")

        # Executando a consulta para obter todos os dados dos usuários
        query = "SELECT name, email, password, is_admin, authorized_routes FROM users"

        # Executando a query usando o método `exec_query`
        users = self.exec_query(query=query,
                                fetchone=False,
                                log_success=False)

        return users

    def user_has_route_access(self, user_email: str, route_endpoint: str) -> bool:
        """
        Verifica se um usuário tem acesso a uma rota específica
        
        :param user_email: Email do usuário
        :param route_endpoint: Endpoint da rota (ex: 'public.main_page')
        :return: True se o usuário tem acesso, False caso contrário
        """
        
        user = self.retrieve_user(['email'], (user_email,))
        # Retorna o usuário com as colunas name, email, password, is_admin, authorized_routes
        # user = (name, email, password, is_admin, authorized_routes)
        
        if not user or len(user) < 5:
            return False
        
        # Se o usuário é admin, tem acesso a tudo
        if user[3]:  # índice 3 é is_admin
            return True
            
        try:
            authorized_routes = json.loads(user[4])  # índice 4 é authorized_routes. Converte a string para uma lista.
            return route_endpoint in authorized_routes
        except (json.JSONDecodeError, IndexError):
            return False

    def user_has_sector_access(self, user_email: str, sector_name: str) -> bool:
        """
        Verifica se um usuário tem acesso a um setor específico
        
        :param user_email: Email do usuário
        :param sector_name: Nome do setor (ex: 'Configurações', 'Jornada')
        :return: True se o usuário tem acesso, False caso contrário
        """
        
        user = self.retrieve_user(['email'], (user_email,))
        # Retorna o usuário com as colunas name, email, password, is_admin, authorized_routes
        # user = (name, email, password, is_admin, authorized_routes)
        
        if not user or len(user) < 5:
            return False
        
        # Se o usuário é admin, tem acesso a tudo
        if user[3]:  # índice 3 é is_admin
            return True
            
        try:
            # O campo authorized_routes agora armazena setores ao invés de rotas individuais
            authorized_sectors = json.loads(user[4])  # índice 4 é authorized_routes (que agora contém setores)
            return sector_name in authorized_sectors
        except (json.JSONDecodeError, IndexError):
            return False

    def update_user_routes(self, user_email: str, authorized_routes: list) -> int:
        """
        Atualiza as rotas autorizadas de um usuário
        
        :param user_email: Email do usuário
        :param authorized_routes: Lista de rotas autorizadas
        :return: Número de linhas afetadas
        """
        
        routes_json = json.dumps(authorized_routes) # converte a lista de rotas autorizadas para uma string
        
        return self.update_user(
            set_columns=['authorized_routes'],
            set_values=(routes_json,),
            where_columns=['email'],
            where_values=(user_email,)
        )

    def update_user_sectors(self, user_email: str, authorized_sectors: list) -> int:
        """
        Atualiza os setores autorizados de um usuário
        Sempre garante que "Comum" esteja presente na lista
        
        :param user_email: Email do usuário  
        :param authorized_sectors: Lista de setores autorizados
        :return: Número de linhas afetadas
        """
        
        # Garantir que "Comum" sempre esteja presente
        if "Comum" not in authorized_sectors:
            authorized_sectors.append("Comum")
        
        sectors_json = json.dumps(authorized_sectors)
        
        return self.update_user(
            set_columns=['authorized_routes'],
            set_values=(sectors_json,),
            where_columns=['email'],
            where_values=(user_email,)
        )

    def get_user_routes(self, user_email: str) -> list:
        """
        Obtém as rotas autorizadas de um usuário
        
        :param user_email: Email do usuário
        :return: Lista de rotas autorizadas
        """
        
        user = self.retrieve_user(['email'], (user_email,))
        if not user or len(user) < 5:
            return []
            
        try:
            return json.loads(user[4])  # índice 4 é authorized_routes
        except (json.JSONDecodeError, IndexError):
            return []

    def get_user_sectors(self, user_email: str) -> list:
        """
        Obtém os setores autorizados de um usuário
        
        :param user_email: Email do usuário
        :return: Lista de setores autorizados
        """
        
        user = self.retrieve_user(['email'], (user_email,))
        if not user or len(user) < 5:
            return []
            
        try:
            # O campo authorized_routes agora armazena setores
            return json.loads(user[4])  # índice 4 é authorized_routes (que agora contém setores)
        except (json.JSONDecodeError, IndexError):
            return []

    def is_user_admin(self, user_email: str) -> bool:
        """
        Verifica se um usuário é administrador
        
        :param user_email: Email do usuário
        :return: True se o usuário é admin, False caso contrário
        """
        user = self.retrieve_user(['email'], (user_email,))
        if not user or len(user) < 4:
            return False
        
        return bool(user[3])  # índice 3 é is_admin

    def clean_automatic_sectors_from_users(self):
        """
        Remove apenas o setor "Público" dos usuários existentes e garante que "Comum" esteja presente
        """
        try:
            # Buscar todos os usuários
            all_users = self.retrieve_all_users()
            
            if not all_users:
                return
            
            for user_data in all_users:
                # user_data = (name, email, password, is_admin, authorized_routes)
                if len(user_data) >= 5:
                    user_email = user_data[1]
                    authorized_routes_str = user_data[4]
                    
                    try:
                        authorized_sectors = json.loads(authorized_routes_str) if authorized_routes_str else []
                        
                        # Remover apenas "Público" e garantir que "Comum" esteja presente
                        filtered_sectors = [sector for sector in authorized_sectors if sector != 'Público']
                        
                        if "Comum" not in filtered_sectors:
                            filtered_sectors.append("Comum")
                        
                        # Se houve mudança, atualizar o usuário
                        if filtered_sectors != authorized_sectors:
                            self.logger.print(f"Atualizando setores do usuário {user_email} - garantindo 'Comum'")
                            self.update_user_sectors(user_email, filtered_sectors)
                            
                    except (json.JSONDecodeError, TypeError):
                        # Se houver erro, garantir que pelo menos "Comum" exista
                        self.logger.print(f"Corrigindo setores do usuário {user_email} - garantindo 'Comum'")
                        self.update_user_sectors(user_email, ["Comum"])
                        
        except Exception as e:
            self.logger.register_log("Erro ao atualizar setores automáticos", str(e))
