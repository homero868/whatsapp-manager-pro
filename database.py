import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager
import logging
from typing import List, Dict, Any, Optional
from config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.config = Config.get_db_config()
        
    @contextmanager
    def get_connection(self):
        """Context manager para conexiones a la base de datos"""
        conn = None
        try:
            conn = mysql.connector.connect(**self.config)
            yield conn
        except Error as e:
            logger.error(f"Error de base de datos: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn and conn.is_connected():
                conn.close()
    
    def execute_query(self, query: str, params: tuple = None, fetch_one: bool = False) -> Any:
        """Ejecutar una consulta SELECT"""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            result = cursor.fetchone() if fetch_one else cursor.fetchall()
            cursor.close()
            return result
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Ejecutar una consulta INSERT, UPDATE o DELETE"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows
    
    def execute_insert(self, query: str, params: tuple = None) -> int:
        """Ejecutar una consulta INSERT y devolver el ID generado"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            last_id = cursor.lastrowid
            cursor.close()
            return last_id
    
    def execute_many(self, query: str, data: List[tuple]) -> int:
        """Ejecutar múltiples consultas"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, data)
            conn.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows
    
    def test_connection(self) -> bool:
        """Probar la conexión a la base de datos"""
        try:
            with self.get_connection() as conn:
                return conn.is_connected()
        except:
            return False

class UserModel:
    def __init__(self):
        self.db = DatabaseManager()
    
    def authenticate(self, username: str, password_hash: str) -> Optional[Dict]:
        """Autenticar usuario"""
        query = """
            SELECT id, username, email, is_active 
            FROM users 
            WHERE username = %s AND password_hash = %s AND is_active = TRUE
        """
        user = self.db.execute_query(query, (username, password_hash), fetch_one=True)
        
        if user:
            # Actualizar último login
            update_query = "UPDATE users SET last_login = NOW() WHERE id = %s"
            self.db.execute_update(update_query, (user['id'],))
        
        return user
    
    def create_user(self, username: str, password_hash: str, email: str = None) -> int:
        """Crear nuevo usuario"""
        query = "INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)"
        return self.db.execute_insert(query, (username, password_hash, email))
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Obtener usuario por nombre de usuario"""
        query = "SELECT * FROM users WHERE username = %s"
        return self.db.execute_query(query, (username,), fetch_one=True)
    
    def update_last_login(self, user_id: int) -> bool:
        """Actualizar último login"""
        query = "UPDATE users SET last_login = NOW() WHERE id = %s"
        return self.db.execute_update(query, (user_id,)) > 0

class ContactModel:
    def __init__(self):
        self.db = DatabaseManager()
    
    def create_contacts(self, contacts: List[Dict], user_id: int) -> int:
        """Crear múltiples contactos"""
        query = """
            INSERT INTO contacts (phone_number, name, email, company, extra_data, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                email = VALUES(email),
                company = VALUES(company),
                extra_data = VALUES(extra_data),
                updated_at = NOW()
        """
        
        data = []
        for contact in contacts:
            data.append((
                contact.get('phone_number'),
                contact.get('name'),
                contact.get('email'),
                contact.get('company'),
                contact.get('extra_data'),
                user_id
            ))
        
        return self.db.execute_many(query, data)
    
    def get_contacts(self, limit: int = None, offset: int = 0) -> List[Dict]:
        """Obtener lista de contactos"""
        query = "SELECT * FROM contacts ORDER BY created_at DESC"
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        return self.db.execute_query(query)
    
    def get_contact_count(self) -> int:
        """Obtener número total de contactos"""
        query = "SELECT COUNT(*) as count FROM contacts"
        result = self.db.execute_query(query, fetch_one=True)
        return result['count'] if result else 0
    
    def delete_contact(self, contact_id: int) -> bool:
        """Eliminar un contacto"""
        query = "DELETE FROM contacts WHERE id = %s"
        return self.db.execute_update(query, (contact_id,)) > 0

class TemplateModel:
    def __init__(self):
        self.db = DatabaseManager()
    
    def create_template(self, name: str, content: str, variables: str, user_id: int) -> int:
        """Crear nueva plantilla"""
        query = """
            INSERT INTO templates (name, content, variables, created_by)
            VALUES (%s, %s, %s, %s)
        """
        return self.db.execute_insert(query, (name, content, variables, user_id))
    
    def update_template(self, template_id: int, name: str, content: str, variables: str) -> bool:
        """Actualizar plantilla existente"""
        query = """
            UPDATE templates 
            SET name = %s, content = %s, variables = %s, updated_at = NOW()
            WHERE id = %s
        """
        return self.db.execute_update(query, (name, content, variables, template_id)) > 0
    
    def get_templates(self, active_only: bool = True) -> List[Dict]:
        """Obtener lista de plantillas"""
        query = "SELECT * FROM templates"
        if active_only:
            query += " WHERE is_active = TRUE"
        query += " ORDER BY created_at DESC"
        return self.db.execute_query(query)
    
    def get_template(self, template_id: int) -> Optional[Dict]:
        """Obtener una plantilla específica"""
        query = "SELECT * FROM templates WHERE id = %s"
        return self.db.execute_query(query, (template_id,), fetch_one=True)
    
    def delete_template(self, template_id: int) -> bool:
        """Eliminar plantilla (soft delete)"""
        query = "UPDATE templates SET is_active = FALSE WHERE id = %s"
        return self.db.execute_update(query, (template_id,)) > 0

class CampaignModel:
    def __init__(self):
        self.db = DatabaseManager()
    
    def create_campaign(self, name: str, template_id: int, scheduled_at: str, 
                       user_id: int, total_contacts: int) -> int:
        """Crear nueva campaña"""
        query = """
            INSERT INTO campaigns (name, template_id, scheduled_at, created_by, total_contacts)
            VALUES (%s, %s, %s, %s, %s)
        """
        return self.db.execute_insert(query, 
                                    (name, template_id, scheduled_at, user_id, total_contacts))
    
    def get_pending_campaigns(self) -> List[Dict]:
        """Obtener campañas pendientes de ejecución"""
        query = """
            SELECT c.*, t.content as template_content, t.variables
            FROM campaigns c
            JOIN templates t ON c.template_id = t.id
            WHERE c.status = 'pending' 
            AND (c.scheduled_at IS NULL OR c.scheduled_at <= NOW())
            ORDER BY c.created_at ASC
        """
        return self.db.execute_query(query)
    
    def update_campaign_status(self, campaign_id: int, status: str) -> bool:
        """Actualizar estado de campaña"""
        query = "UPDATE campaigns SET status = %s"
        if status == 'running':
            query += ", executed_at = NOW()"
        query += " WHERE id = %s"
        return self.db.execute_update(query, (status, campaign_id)) > 0
    
    def get_campaign_stats(self) -> List[Dict]:
        """Obtener estadísticas de campañas"""
        query = """
            SELECT 
                c.id, c.name, c.created_at, c.total_contacts,
                COUNT(m.id) as sent_messages,
                COALESCE(SUM(CASE WHEN m.status = 'delivered' THEN 1 ELSE 0 END), 0) as delivered,
                COALESCE(SUM(CASE WHEN m.status = 'read' THEN 1 ELSE 0 END), 0) as `read`,
                COALESCE(SUM(CASE WHEN m.status = 'failed' THEN 1 ELSE 0 END), 0) as failed
            FROM campaigns c
            LEFT JOIN messages m ON c.id = m.campaign_id
            GROUP BY c.id, c.name, c.created_at, c.total_contacts
            ORDER BY c.created_at DESC
        """
        results = self.db.execute_query(query)
        
        # Asegurarse de que todos los valores numéricos no sean None
        for result in results:
            result['sent_messages'] = result.get('sent_messages') or 0
            result['delivered'] = result.get('delivered') or 0
            result['read'] = result.get('read') or 0
            result['failed'] = result.get('failed') or 0
            result['total_contacts'] = result.get('total_contacts') or 0
        
        return results

class MessageModel:
    def __init__(self):
        self.db = DatabaseManager()
    
    def create_messages(self, campaign_id: int, template_id: int, contact_ids: List[int]) -> int:
        """Crear mensajes para una campaña"""
        query = """
            INSERT INTO messages (campaign_id, contact_id, template_id)
            VALUES (%s, %s, %s)
        """
        data = [(campaign_id, contact_id, template_id) for contact_id in contact_ids]
        return self.db.execute_many(query, data)
    
    def get_pending_messages(self, limit: int = 10) -> List[Dict]:
        """Obtener mensajes pendientes de envío"""
        query = """
            SELECT m.*, c.phone_number, c.name, c.email, c.extra_data,
                   t.content as template_content, t.variables
            FROM messages m
            JOIN contacts c ON m.contact_id = c.id
            JOIN templates t ON m.template_id = t.id
            WHERE m.status = 'pending' AND m.retry_count < %s
            ORDER BY m.created_at ASC
            LIMIT %s
        """
        return self.db.execute_query(query, (Config.MAX_RETRY_ATTEMPTS, limit))
    
    def update_message_status(self, message_id: int, status: str, 
                            twilio_sid: str = None, error: str = None) -> bool:
        """Actualizar estado de mensaje"""
        query = "UPDATE messages SET status = %s"
        params = [status]
        
        if twilio_sid:
            query += ", twilio_sid = %s"
            params.append(twilio_sid)
        
        if error:
            query += ", error_message = %s, retry_count = retry_count + 1"
            params.append(error)
        
        if status == 'sent':
            query += ", sent_at = NOW()"
        elif status == 'delivered':
            query += ", delivered_at = NOW()"
        elif status == 'read':
            query += ", read_at = NOW()"
        
        query += " WHERE id = %s"
        params.append(message_id)
        
        return self.db.execute_update(query, params) > 0
    
    def get_message_stats(self) -> Dict:
        """Obtener estadísticas generales de mensajes"""
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
                SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered,
                SUM(CASE WHEN status = 'read' THEN 1 ELSE 0 END) as `read`,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM messages
        """
        result = self.db.execute_query(query, fetch_one=True)
        
        # Si no hay resultado o los valores son None, devolver ceros
        if not result:
            return {
                'total': 0,
                'sent': 0,
                'delivered': 0,
                'read': 0,
                'failed': 0
            }
        
        # Convertir None a 0
        return {
            'total': result.get('total') or 0,
            'sent': result.get('sent') or 0,
            'delivered': result.get('delivered') or 0,
            'read': result.get('read') or 0,
            'failed': result.get('failed') or 0
        }

class ActivityLogModel:
    def __init__(self):
        self.db = DatabaseManager()
    
    def log_activity(self, user_id: int, action: str, details: str = None, 
                    ip_address: str = None) -> int:
        """Registrar actividad"""
        # Convertir details a JSON válido
        import json
        json_details = json.dumps({"message": details} if details else {})
        
        query = """
            INSERT INTO activity_logs (user_id, action, details, ip_address)
            VALUES (%s, %s, %s, %s)
        """
        return self.db.execute_insert(query, (user_id, action, json_details, ip_address))
    
    def get_recent_activities(self, user_id: int = None, limit: int = 100) -> List[Dict]:
        """Obtener actividades recientes"""
        query = "SELECT * FROM activity_logs"
        params = []
        
        if user_id:
            query += " WHERE user_id = %s"
            params.append(user_id)
        
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        return self.db.execute_query(query, params)
