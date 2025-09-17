#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Driver para gerenciar classificações de blocos de fechamento
Sistema RPZ v3.0.0.0 - Fase 2: APIs de leitura/escrita

Autor: Sistema RPZ
Data: 2025-01-27
"""

import sqlite3
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import json

class ClosureBlockClassificationsDriver:
    """
    Driver para operações CRUD na tabela closure_block_classifications
    """
    
    def __init__(self, logger=None, db_path: str = None):
        self.logger = logger
        self.db_path = db_path
        self.table_name = 'closure_block_classifications'
        self.audit_table_name = 'closure_block_classifications_audit'
        
        # Valores válidos para classificação
        self.valid_classifications = ['VALIDO', 'CARGA_DESCARGA', 'GARAGEM', 'INVALIDO']
    
    def _log(self, message: str, level: str = 'info'):
        """Log interno"""
        if self.logger:
            if hasattr(self.logger, 'print'):
                self.logger.print(f"[{level.upper()}] {message}")
            else:
                print(f"[{level.upper()}] {message}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Obter conexão com o banco"""
        return sqlite3.connect(self.db_path)
    
    def validate_classification(self, classification: str) -> bool:
        """Validar se a classificação é válida"""
        return classification.upper() in self.valid_classifications
    
    def get_classification(self, motorist_id: int, data: str, truck_id: Optional[int] = None) -> Optional[Dict]:
        """
        Buscar classificação específica
        
        Args:
            motorist_id: ID do motorista
            data: Data no formato DD-MM-YYYY
            truck_id: ID do caminhão (opcional)
            
        Returns:
            Dict com os dados da classificação ou None se não encontrado
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if truck_id is not None:
                query = """
                    SELECT id, motorist_id, data, truck_id, classification, notes, 
                           created_at, updated_at, changed_by
                    FROM closure_block_classifications 
                    WHERE motorist_id = ? AND data = ? AND truck_id = ?
                """
                params = (motorist_id, data, truck_id)
            else:
                query = """
                    SELECT id, motorist_id, data, truck_id, classification, notes, 
                           created_at, updated_at, changed_by
                    FROM closure_block_classifications 
                    WHERE motorist_id = ? AND data = ? AND truck_id IS NULL
                """
                params = (motorist_id, data)
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            if result:
                return {
                    'id': result[0],
                    'motorist_id': result[1],
                    'data': result[2],
                    'truck_id': result[3],
                    'classification': result[4],
                    'notes': result[5],
                    'created_at': result[6],
                    'updated_at': result[7],
                    'changed_by': result[8]
                }
            
            return None
            
        except sqlite3.Error as e:
            self._log(f"Erro ao buscar classificação: {e}", 'error')
            return None
        finally:
            if conn:
                conn.close()
    
    def create_classification(self, motorist_id: int, data: str, classification: str, 
                            truck_id: Optional[int] = None, notes: Optional[str] = None, 
                            changed_by: str = 'Sistema') -> Dict[str, Any]:
        """
        Criar nova classificação
        
        Args:
            motorist_id: ID do motorista
            data: Data no formato DD-MM-YYYY
            classification: Classificação (VALIDO, CARGA_DESCARGA, GARAGEM, INVALIDO)
            truck_id: ID do caminhão (opcional)
            notes: Observações (opcional)
            changed_by: Usuário que fez a alteração
            
        Returns:
            Dict com resultado da operação
        """
        try:
            # Validar classificação
            if not self.validate_classification(classification):
                return {
                    'success': False,
                    'error': f'Classificação inválida: {classification}. Valores válidos: {self.valid_classifications}'
                }
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Verificar se já existe
            existing = self.get_classification(motorist_id, data, truck_id)
            if existing:
                return {
                    'success': False,
                    'error': 'Classificação já existe para este motorista/data/caminhão',
                    'existing': existing
                }
            
            # Inserir nova classificação
            query = """
                INSERT INTO closure_block_classifications 
                (motorist_id, data, truck_id, classification, notes, changed_by)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(query, (motorist_id, data, truck_id, classification.upper(), notes, changed_by))
            classification_id = cursor.lastrowid
            
            conn.commit()
            
            self._log(f"Classificação criada: ID {classification_id}, motorist_id {motorist_id}, data {data}, classification {classification}")
            
            return {
                'success': True,
                'id': classification_id,
                'message': 'Classificação criada com sucesso'
            }
            
        except sqlite3.Error as e:
            self._log(f"Erro ao criar classificação: {e}", 'error')
            if conn:
                conn.rollback()
            return {
                'success': False,
                'error': f'Erro no banco de dados: {str(e)}'
            }
        finally:
            if conn:
                conn.close()
    
    def update_classification(self, motorist_id: int, data: str, classification: str,
                            truck_id: Optional[int] = None, notes: Optional[str] = None,
                            changed_by: str = 'Sistema') -> Dict[str, Any]:
        """
        Atualizar classificação existente
        
        Args:
            motorist_id: ID do motorista
            data: Data no formato DD-MM-YYYY
            classification: Nova classificação
            truck_id: ID do caminhão (opcional)
            notes: Observações (opcional)
            changed_by: Usuário que fez a alteração
            
        Returns:
            Dict com resultado da operação
        """
        try:
            # Validar classificação
            if not self.validate_classification(classification):
                return {
                    'success': False,
                    'error': f'Classificação inválida: {classification}. Valores válidos: {self.valid_classifications}'
                }
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Verificar se existe
            existing = self.get_classification(motorist_id, data, truck_id)
            if not existing:
                return {
                    'success': False,
                    'error': 'Classificação não encontrada para atualização'
                }
            
            # Atualizar classificação
            if truck_id is not None:
                query = """
                    UPDATE closure_block_classifications 
                    SET classification = ?, notes = ?, changed_by = ?
                    WHERE motorist_id = ? AND data = ? AND truck_id = ?
                """
                params = (classification.upper(), notes, changed_by, motorist_id, data, truck_id)
            else:
                query = """
                    UPDATE closure_block_classifications 
                    SET classification = ?, notes = ?, changed_by = ?
                    WHERE motorist_id = ? AND data = ? AND truck_id IS NULL
                """
                params = (classification.upper(), notes, changed_by, motorist_id, data)
            
            cursor.execute(query, params)
            rows_affected = cursor.rowcount
            
            conn.commit()
            
            self._log(f"Classificação atualizada: motorist_id {motorist_id}, data {data}, nova classification {classification}")
            
            return {
                'success': True,
                'rows_affected': rows_affected,
                'message': 'Classificação atualizada com sucesso'
            }
            
        except sqlite3.Error as e:
            self._log(f"Erro ao atualizar classificação: {e}", 'error')
            if conn:
                conn.rollback()
            return {
                'success': False,
                'error': f'Erro no banco de dados: {str(e)}'
            }
        finally:
            if conn:
                conn.close()
    
    def upsert_classification(self, motorist_id: int, data: str, classification: str,
                            truck_id: Optional[int] = None, notes: Optional[str] = None,
                            changed_by: str = 'Sistema') -> Dict[str, Any]:
        """
        Criar ou atualizar classificação (upsert)
        
        Args:
            motorist_id: ID do motorista
            data: Data no formato DD-MM-YYYY
            classification: Classificação
            truck_id: ID do caminhão (opcional)
            notes: Observações (opcional)
            changed_by: Usuário que fez a alteração
            
        Returns:
            Dict com resultado da operação
        """
        # Verificar se já existe
        existing = self.get_classification(motorist_id, data, truck_id)
        
        if existing:
            return self.update_classification(motorist_id, data, classification, truck_id, notes, changed_by)
        else:
            return self.create_classification(motorist_id, data, classification, truck_id, notes, changed_by)
    
    def get_classification_history(self, motorist_id: int, data: str, 
                                 truck_id: Optional[int] = None) -> List[Dict]:
        """
        Buscar histórico de mudanças de uma classificação
        
        Args:
            motorist_id: ID do motorista
            data: Data no formato DD-MM-YYYY
            truck_id: ID do caminhão (opcional)
            
        Returns:
            Lista com histórico de mudanças
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if truck_id is not None:
                query = """
                    SELECT id, classification_id, motorist_id, data, truck_id,
                           prev_classification, new_classification, prev_notes, new_notes,
                           changed_by, changed_at, change_reason
                    FROM closure_block_classifications_audit 
                    WHERE motorist_id = ? AND data = ? AND truck_id = ?
                    ORDER BY changed_at DESC
                """
                params = (motorist_id, data, truck_id)
            else:
                query = """
                    SELECT id, classification_id, motorist_id, data, truck_id,
                           prev_classification, new_classification, prev_notes, new_notes,
                           changed_by, changed_at, change_reason
                    FROM closure_block_classifications_audit 
                    WHERE motorist_id = ? AND data = ? AND truck_id IS NULL
                    ORDER BY changed_at DESC
                """
                params = (motorist_id, data)
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            history = []
            for result in results:
                history.append({
                    'id': result[0],
                    'classification_id': result[1],
                    'motorist_id': result[2],
                    'data': result[3],
                    'truck_id': result[4],
                    'prev_classification': result[5],
                    'new_classification': result[6],
                    'prev_notes': result[7],
                    'new_notes': result[8],
                    'changed_by': result[9],
                    'changed_at': result[10],
                    'change_reason': result[11]
                })
            
            return history
            
        except sqlite3.Error as e:
            self._log(f"Erro ao buscar histórico: {e}", 'error')
            return []
        finally:
            if conn:
                conn.close()
    
    def get_motorist_classifications(self, motorist_id: int, 
                                   start_date: Optional[str] = None,
                                   end_date: Optional[str] = None) -> List[Dict]:
        """
        Buscar todas as classificações de um motorista em um período
        
        Args:
            motorist_id: ID do motorista
            start_date: Data inicial (DD-MM-YYYY)
            end_date: Data final (DD-MM-YYYY)
            
        Returns:
            Lista com classificações do motorista
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT id, motorist_id, data, truck_id, classification, notes, 
                       created_at, updated_at, changed_by
                FROM closure_block_classifications 
                WHERE motorist_id = ?
            """
            params = [motorist_id]
            
            if start_date:
                query += " AND data >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND data <= ?"
                params.append(end_date)
            
            query += " ORDER BY data DESC"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            classifications = []
            for result in results:
                classifications.append({
                    'id': result[0],
                    'motorist_id': result[1],
                    'data': result[2],
                    'truck_id': result[3],
                    'classification': result[4],
                    'notes': result[5],
                    'created_at': result[6],
                    'updated_at': result[7],
                    'changed_by': result[8]
                })
            
            return classifications
            
        except sqlite3.Error as e:
            self._log(f"Erro ao buscar classificações do motorista: {e}", 'error')
            return []
        finally:
            if conn:
                conn.close()
    
    def delete_classification(self, motorist_id: int, data: str, 
                            truck_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Deletar classificação
        
        Args:
            motorist_id: ID do motorista
            data: Data no formato DD-MM-YYYY
            truck_id: ID do caminhão (opcional)
            
        Returns:
            Dict com resultado da operação
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if truck_id is not None:
                query = "DELETE FROM closure_block_classifications WHERE motorist_id = ? AND data = ? AND truck_id = ?"
                params = (motorist_id, data, truck_id)
            else:
                query = "DELETE FROM closure_block_classifications WHERE motorist_id = ? AND data = ? AND truck_id IS NULL"
                params = (motorist_id, data)
            
            cursor.execute(query, params)
            rows_affected = cursor.rowcount
            
            conn.commit()
            
            self._log(f"Classificação deletada: motorist_id {motorist_id}, data {data}, rows_affected {rows_affected}")
            
            return {
                'success': True,
                'rows_affected': rows_affected,
                'message': 'Classificação deletada com sucesso'
            }
            
        except sqlite3.Error as e:
            self._log(f"Erro ao deletar classificação: {e}", 'error')
            if conn:
                conn.rollback()
            return {
                'success': False,
                'error': f'Erro no banco de dados: {str(e)}'
            }
        finally:
            if conn:
                conn.close()
