# Actualización de message_scheduler.py para soportar archivos adjuntos

import schedule
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable, List
from database import CampaignModel, MessageModel, ContactModel, AttachmentModel
from twilio_service import TwilioService, MessageQueue
from config import Config
import json

logger = logging.getLogger(__name__)

class MessageScheduler:
    def __init__(self):
        self.campaign_model = CampaignModel()
        self.message_model = MessageModel()
        self.contact_model = ContactModel()
        self.attachment_model = AttachmentModel()
        self.twilio_service = TwilioService()
        self.message_queue = MessageQueue(self.twilio_service)
        self.running = False
        self.thread = None
        self.callbacks = {}
    
    def start(self):
        """Iniciar el programador"""
        if self.running:
            logger.warning("El scheduler ya está en ejecución")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("Programador de mensajes iniciado")
        logger.info("Configuración del scheduler:")
        logger.info("  - Verificar campañas: cada 1 minuto")
        logger.info("  - Procesar mensajes: cada 5 segundos")
        logger.info("  - Reintentar fallidos: cada 5 minutos")
        logger.info("  - Actualizar estados: cada 1 hora")
    
    def stop(self):
        """Detener el programador"""
        self.running = False
        self.message_queue.stop_processing()
        if self.thread:
            self.thread.join()
        logger.info("Programador de mensajes detenido")
    
    def _run_scheduler(self):
        """Loop principal del programador"""
        try:
            # Programar tareas
            schedule.every(10).seconds.do(self._check_pending_campaigns)  # Temporalmente cada 10 segundos para pruebas
            schedule.every(5).seconds.do(self._process_pending_messages)
            schedule.every(5).minutes.do(self._retry_failed_messages)
            schedule.every(1).hours.do(self._update_message_statuses)
            
            logger.info("✅ Scheduler configurado correctamente")
            logger.info("📅 Tareas programadas:")
            for job in schedule.jobs:
                logger.info(f"  - {job}")
            
            # Ejecutar verificación inicial de campañas
            logger.info("Ejecutando verificación inicial de campañas...")
            self._check_pending_campaigns()
            
            while self.running:
                schedule.run_pending()
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error fatal en scheduler: {e}", exc_info=True)
            self.running = False
    
    def _check_pending_campaigns(self):
        """Verificar y ejecutar campañas pendientes"""
        try:
            logger.info("=" * 50)
            logger.info("🔍 Verificando campañas programadas...")
            logger.info(f"Hora actual: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Primero, veamos TODAS las campañas para debug
            from database import DatabaseManager
            db = DatabaseManager()
            all_campaigns = db.execute_query(
                "SELECT id, name, status, scheduled_at FROM campaigns WHERE status = 'pending' ORDER BY scheduled_at ASC"
            )
            
            if all_campaigns:
                logger.debug("Campañas pendientes en BD:")
                for c in all_campaigns:
                    scheduled_time = c['scheduled_at']
                    time_diff = (scheduled_time - datetime.now()).total_seconds()
                    if time_diff > 0:
                        minutes_left = int(time_diff / 60)
                        seconds_left = int(time_diff % 60)
                        logger.info(f"  📅 '{c['name']}' se ejecutará en {minutes_left}m {seconds_left}s (a las {scheduled_time.strftime('%H:%M:%S')})")
                    else:
                        logger.info(f"  ✅ '{c['name']}' lista para ejecutar (programada para {scheduled_time.strftime('%H:%M:%S')})")
            
            # Ahora buscar las pendientes que ya deben ejecutarse
            campaigns = self.campaign_model.get_pending_campaigns()
            
            if campaigns:
                logger.info(f"🚀 Campañas listas para ejecutar: {len(campaigns)}")
                for c in campaigns:
                    logger.info(f"  - {c['name']} programada para {c.get('scheduled_at')}")
            else:
                logger.info("⏳ No hay campañas listas para ejecutar en este momento")
            
            for campaign in campaigns:
                logger.info(f"🚀 Iniciando campaña: {campaign['name']} (ID: {campaign['id']})")
                
                # Actualizar estado a 'running'
                self.campaign_model.update_campaign_status(campaign['id'], 'running')
                
                # Obtener contactos
                contacts = self.contact_model.get_contacts()
                contact_ids = [c['id'] for c in contacts]
                logger.info(f"Contactos encontrados: {len(contact_ids)}")
                
                # Crear mensajes para la campaña
                if contact_ids:
                    created = self.message_model.create_messages(
                        campaign['id'],
                        campaign['template_id'],
                        contact_ids
                    )
                    logger.info(f"✅ Creados {len(contact_ids)} mensajes para campaña {campaign['id']}")
                else:
                    logger.warning("⚠️ No hay contactos para enviar")
                
                # Ejecutar callback si existe
                if campaign['id'] in self.callbacks:
                    self.callbacks[campaign['id']]('started', campaign)
                    
            logger.info("=" * 50)
        
        except Exception as e:
            logger.error(f"❌ Error procesando campañas pendientes: {e}", exc_info=True)
    
    def _process_pending_messages(self):
        """Procesar mensajes pendientes de envío con archivos adjuntos"""
        try:
            logger.info("Iniciando procesamiento de mensajes pendientes...")
            
            # Obtener mensajes pendientes
            messages = self.message_model.get_pending_messages(limit=10)
            logger.info(f"Mensajes pendientes encontrados: {len(messages)}")
            
            if not messages:
                return
                
            for message in messages:
                logger.info(f"Procesando mensaje ID: {message['id']} para {message['phone_number']}")
                logger.debug(f"Datos del mensaje: {message}")
                
                # Formatear mensaje con datos del contacto
                contact_data = {
                    'nombre': message.get('name', ''),
                    'email': message.get('email', ''),
                    'empresa': message.get('company', ''),
                    'telefono': message.get('phone_number', '')
                }
                
                # Agregar datos extra si existen
                if message.get('extra_data'):
                    try:
                        extra = json.loads(message['extra_data'])
                        contact_data.update(extra)
                    except:
                        pass
                
                # Formatear mensaje
                formatted_message = self.twilio_service.format_message(
                    message['template_content'],
                    contact_data
                )
                
                logger.info(f"Mensaje formateado: {formatted_message[:100]}...")
                
                # Obtener archivos adjuntos de la plantilla
                media_urls = []
                try:
                    attachments = self.attachment_model.get_template_attachments(
                        message['template_id']
                    )
                    
                    # WhatsApp permite hasta 10 archivos por mensaje
                    for attachment in attachments[:10]:
                        # Usar URL pública si está disponible
                        if attachment.get('public_url'):
                            media_urls.append(attachment['public_url'])
                            logger.info(f"Agregando archivo a enviar: {attachment['file_name']}")
                        else:
                            # Log de advertencia si no hay URL pública
                            logger.warning(
                                f"Archivo adjunto sin URL pública: {attachment['file_name']}. "
                                "Necesita configurar un servicio de hosting de archivos."
                            )
                    
                    if len(media_urls) > 0:
                        logger.info(f"Total de archivos a enviar: {len(media_urls)}")
                    
                except Exception as e:
                    logger.error(f"Error obteniendo archivos adjuntos: {e}")
                
                # Estrategia para múltiples archivos
                if len(media_urls) > 1:
                    logger.info(f"Dividiendo en múltiples mensajes debido a limitación de WhatsApp")
                    
                    # Primer mensaje con texto y primer archivo
                    self.message_queue.add_message(
                        message['phone_number'],
                        formatted_message,
                        media_urls=[media_urls[0]] if media_urls else None,
                        callback=lambda result, msg_id=message['id']: 
                            self._handle_send_result(msg_id, result)
                    )
                    
                    # Mensajes adicionales para el resto de archivos
                    for i, media_url in enumerate(media_urls[1:], 2):
                        additional_text = f"📎 Archivo {i} de {len(media_urls)}"
                        self.message_queue.add_message(
                            message['phone_number'],
                            additional_text,
                            media_urls=[media_url],
                            callback=lambda result, msg_id=message['id'], idx=i: 
                                logger.info(f"Archivo {idx} enviado para mensaje {msg_id}")
                        )
                else:
                    # Un solo archivo o ninguno
                    self.message_queue.add_message(
                        message['phone_number'],
                        formatted_message,
                        media_urls=media_urls if media_urls else None,
                        callback=lambda result, msg_id=message['id']: 
                            self._handle_send_result(msg_id, result)
                    )
            
            # Procesar cola
            queue_size = self.message_queue.get_queue_size()
            if queue_size > 0:
                logger.info(f"Procesando cola con {queue_size} mensajes...")
                queue_thread = threading.Thread(
                    target=self.message_queue.process_queue,
                    daemon=True
                )
                queue_thread.start()
            else:
                logger.warning("La cola de mensajes está vacía")
        
        except Exception as e:
            logger.error(f"Error procesando mensajes pendientes: {e}", exc_info=True)
    
    def _retry_failed_messages(self):
        """Reintentar mensajes fallidos"""
        try:
            # Actualizar mensajes fallidos a pendiente para reintento
            query = """
                UPDATE messages 
                SET status = 'pending', error_message = NULL
                WHERE status = 'failed' 
                AND retry_count < %s
                AND updated_at < NOW() - INTERVAL %s MINUTE
            """
            
            from database import DatabaseManager
            db = DatabaseManager()
            affected = db.execute_update(
                query, 
                (Config.MAX_RETRY_ATTEMPTS, Config.RETRY_DELAY_MINUTES)
            )
            
            if affected > 0:
                logger.info(f"Programados {affected} mensajes para reintento")
        
        except Exception as e:
            logger.error(f"Error programando reintentos: {e}")
    
    def _update_message_statuses(self):
        """Actualizar estados de mensajes desde Twilio"""
        try:
            # Obtener mensajes enviados que necesitan actualización
            query = """
                SELECT id, twilio_sid 
                FROM messages 
                WHERE status IN ('sent', 'queued')
                AND twilio_sid IS NOT NULL
                AND updated_at < NOW() - INTERVAL 5 MINUTE
                LIMIT 50
            """
            
            from database import DatabaseManager
            db = DatabaseManager()
            messages = db.execute_query(query)
            
            for message in messages:
                status = self.twilio_service.get_message_status(message['twilio_sid'])
                
                if status and status != message['status']:
                    # Mapear estados de Twilio a nuestros estados
                    status_map = {
                        'delivered': 'delivered',
                        'read': 'read',
                        'failed': 'failed',
                        'undelivered': 'failed'
                    }
                    
                    if status in status_map:
                        self.message_model.update_message_status(
                            message['id'],
                            status_map[status]
                        )
        
        except Exception as e:
            logger.error(f"Error actualizando estados de mensajes: {e}")
    
    def _handle_send_result(self, message_id: int, result: dict):
        """Manejar resultado de envío de mensaje"""
        try:
            if result['success']:
                self.message_model.update_message_status(
                    message_id,
                    'sent',
                    twilio_sid=result.get('sid')
                )
                logger.info(
                    f"Mensaje {message_id} enviado exitosamente"
                    f"{' con ' + str(result.get('media_count', 0)) + ' archivo(s)' if result.get('media_count') else ''}"
                )
            else:
                self.message_model.update_message_status(
                    message_id,
                    'failed',
                    error=result.get('error', 'Error desconocido')
                )
                logger.error(f"Error enviando mensaje {message_id}: {result.get('error')}")
        
        except Exception as e:
            logger.error(f"Error manejando resultado de envío: {e}")
    
    def schedule_campaign(self, name: str, template_id: int, 
                         scheduled_at: datetime, user_id: int,
                         callback: Optional[Callable] = None) -> int:
        """Programar una nueva campaña"""
        try:
            # Obtener número de contactos
            total_contacts = self.contact_model.get_contact_count()
            
            # Crear campaña
            campaign_id = self.campaign_model.create_campaign(
                name,
                template_id,
                scheduled_at.strftime('%Y-%m-%d %H:%M:%S'),
                user_id,
                total_contacts
            )
            
            # Registrar callback si existe
            if callback:
                self.callbacks[campaign_id] = callback
            
            logger.info(f"Campaña programada: {name} para {scheduled_at}")
            return campaign_id
        
        except Exception as e:
            logger.error(f"Error programando campaña: {e}")
            raise
    
    def cancel_campaign(self, campaign_id: int) -> bool:
        """Cancelar una campaña programada"""
        try:
            # Actualizar estado
            success = self.campaign_model.update_campaign_status(campaign_id, 'cancelled')
            
            # Eliminar callback si existe
            if campaign_id in self.callbacks:
                del self.callbacks[campaign_id]
            
            # Cancelar mensajes pendientes
            query = """
                UPDATE messages 
                SET status = 'cancelled'
                WHERE campaign_id = %s AND status = 'pending'
            """
            
            from database import DatabaseManager
            db = DatabaseManager()
            db.execute_update(query, (campaign_id,))
            
            logger.info(f"Campaña {campaign_id} cancelada")
            return success
        
        except Exception as e:
            logger.error(f"Error cancelando campaña: {e}")
            return False
    
    def send_immediate(self, template_id: int, contact_ids: List[int], 
                      user_id: int, callback: Optional[Callable] = None) -> int:
        """Enviar mensajes inmediatamente"""
        try:
            # Crear campaña inmediata
            campaign_id = self.campaign_model.create_campaign(
                f"Envío inmediato - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                template_id,
                None,  # Sin programación
                user_id,
                len(contact_ids)
            )
            
            # Crear mensajes
            self.message_model.create_messages(campaign_id, template_id, contact_ids)
            
            # Registrar callback
            if callback:
                self.callbacks[campaign_id] = callback
            
            # Actualizar estado a running
            self.campaign_model.update_campaign_status(campaign_id, 'running')
            
            logger.info(f"Iniciado envío inmediato para {len(contact_ids)} contactos")
            return campaign_id
        
        except Exception as e:
            logger.error(f"Error en envío inmediato: {e}")
            raise
    
    def get_campaign_progress(self, campaign_id: int) -> dict:
        """Obtener progreso de una campaña"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
                    SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                FROM messages
                WHERE campaign_id = %s
            """
            
            from database import DatabaseManager
            db = DatabaseManager()
            result = db.execute_query(query, (campaign_id,), fetch_one=True)
            
            if result:
                total = result['total'] or 0
                progress = {
                    'total': total,
                    'pending': result['pending'] or 0,
                    'sent': result['sent'] or 0,
                    'delivered': result['delivered'] or 0,
                    'failed': result['failed'] or 0,
                    'progress_percentage': 0
                }
                
                if total > 0:
                    completed = progress['sent'] + progress['delivered'] + progress['failed']
                    progress['progress_percentage'] = (completed / total) * 100
                
                return progress
            
            return {
                'total': 0,
                'pending': 0,
                'sent': 0,
                'delivered': 0,
                'failed': 0,
                'progress_percentage': 0
            }
        
        except Exception as e:
            logger.error(f"Error obteniendo progreso de campaña: {e}")
            return {
                'total': 0,
                'pending': 0,
                'sent': 0,
                'delivered': 0,
                'failed': 0,
                'progress_percentage': 0
            }
