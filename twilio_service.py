# Actualización de twilio_service.py para soportar archivos adjuntos

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import logging
import time
from typing import Dict, Optional, List
from config import Config
import json
import re

logger = logging.getLogger(__name__)

class TwilioService:
    def __init__(self):
        self.account_sid = Config.TWILIO_ACCOUNT_SID
        self.auth_token = Config.TWILIO_AUTH_TOKEN
        self.from_number = Config.TWILIO_WHATSAPP_FROM
        self.client = None
        self.rate_limiter = RateLimiter(Config.MESSAGES_PER_SECOND)
        
        if self.account_sid and self.auth_token:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Servicio de Twilio inicializado correctamente")
            except Exception as e:
                logger.error(f"Error inicializando Twilio: {e}")
    
    def is_configured(self) -> bool:
        """Verificar si Twilio está configurado"""
        return bool(self.client and self.account_sid and self.auth_token)
    
    def format_message(self, template: str, contact_data: Dict) -> str:
        """Formatear mensaje con datos del contacto"""
        message = template
        
        # Reemplazar variables en el template
        for key, value in contact_data.items():
            placeholder = f"{{{key}}}"
            if placeholder in message:
                message = message.replace(placeholder, str(value) if value else "")
        
        # Limpiar variables no reemplazadas
        message = re.sub(r'\{[^}]+\}', '', message)
        
        return message.strip()
    
    def send_whatsapp_message(self, to_number: str, message: str, 
                            media_urls: List[str] = None) -> Dict:
        """Enviar mensaje de WhatsApp con soporte para múltiples archivos"""
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Twilio no está configurado correctamente'
            }
        
        # Aplicar rate limiting
        self.rate_limiter.wait_if_needed()
        
        try:
            # Asegurar formato de número
            if not to_number.startswith('whatsapp:'):
                to_number = f"whatsapp:{to_number}"
            
            # Preparar parámetros del mensaje
            message_params = {
                'from_': self.from_number,
                'to': to_number,
                'body': message
            }
            
            # Agregar media si existe
            if media_urls:
                # Twilio soporta hasta 10 archivos multimedia por mensaje
                # Filtrar solo URLs válidas (no None)
                valid_urls = [url for url in media_urls if url][:10]
                if valid_urls:
                    message_params['media_url'] = valid_urls
                    logger.info(f"Adjuntando {len(valid_urls)} archivo(s) al mensaje")
                    for i, url in enumerate(valid_urls):
                        logger.debug(f"  Archivo {i+1}: {url}")
            
            # Enviar mensaje
            message = self.client.messages.create(**message_params)
            
            logger.info(f"Mensaje enviado exitosamente a {to_number}, SID: {message.sid}")
            
            return {
                'success': True,
                'sid': message.sid,
                'status': message.status,
                'to': message.to,
                'from': message.from_,
                'media_count': len(valid_urls) if media_urls else 0
            }
            
        except TwilioRestException as e:
            logger.error(f"Error de Twilio enviando mensaje a {to_number}: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': e.code
            }
        except Exception as e:
            logger.error(f"Error inesperado enviando mensaje a {to_number}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_message_status(self, message_sid: str) -> Optional[str]:
        """Obtener estado de un mensaje"""
        if not self.is_configured():
            return None
        
        try:
            message = self.client.messages(message_sid).fetch()
            return message.status
        except Exception as e:
            logger.error(f"Error obteniendo estado del mensaje {message_sid}: {e}")
            return None
    
    def validate_phone_number(self, phone_number: str) -> Dict:
        """Validar y formatear número de teléfono"""
        # Eliminar espacios y caracteres especiales
        cleaned = re.sub(r'[^\d]', '', phone_number)
        
        # Si no tiene código de país, agregar el de Guatemala
        if len(cleaned) == Config.DEFAULT_PHONE_LENGTH:
            cleaned = Config.DEFAULT_COUNTRY_CODE.replace('+', '') + cleaned
        
        # Validar longitud
        if len(cleaned) < 10 or len(cleaned) > 15:
            return {
                'valid': False,
                'error': 'Número de teléfono inválido'
            }
        
        # Agregar prefijo +
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned
        
        return {
            'valid': True,
            'formatted': cleaned
        }
    
    def check_template_compliance(self, template_content: str) -> Dict:
        """Verificar si la plantilla cumple con las políticas de WhatsApp"""
        warnings = []
        
        # Verificar longitud
        if len(template_content) > 1024:
            warnings.append("El mensaje excede los 1024 caracteres permitidos")
        
        # Verificar contenido promocional
        promo_keywords = ['oferta', 'descuento', 'promoción', 'gratis', 'precio']
        if any(keyword in template_content.lower() for keyword in promo_keywords):
            warnings.append("El mensaje parece contener contenido promocional. "
                            "Asegúrese de tener aprobación para mensajes de marketing")
        
        # Verificar variables
        variables = re.findall(r'\{([^}]+)\}', template_content)
        if variables:
            warnings.append(f"Variables encontradas: {', '.join(variables)}. "
                            "Asegúrese de que estos campos existan en sus contactos")
        
        return {
            'compliant': len(warnings) == 0,
            'warnings': warnings,
            'variables': variables
        }
    
    def test_connection(self) -> bool:
        """Probar la conexión con Twilio"""
        if not self.is_configured():
            return False
        
        try:
            # Intentar obtener información de la cuenta
            account = self.client.api.accounts(self.account_sid).fetch()
            logger.info(f"Conexión exitosa con Twilio. Cuenta: {account.friendly_name}")
            return True
        except Exception as e:
            logger.error(f"Error probando conexión con Twilio: {e}")
            return False
    
    def validate_media_url(self, url: str) -> Dict:
        """Validar URL de archivo multimedia"""
        if not url:
            return {'valid': False, 'error': 'URL vacía'}
        
        # Verificar que sea una URL válida
        url_pattern = re.compile(
            r'^https?://'  # http:// o https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # dominio
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # puerto opcional
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            return {'valid': False, 'error': 'URL no válida'}
        
        # Verificar extensión permitida
        allowed_extensions = [
            'jpg', 'jpeg', 'png', 'gif', 'webp',  # Imágenes
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',  # Documentos
            'mp3', 'aac', 'ogg', 'opus', 'amr',  # Audio
            'mp4', 'avi', 'mov', 'wmv', 'flv'  # Video
        ]
        
        ext = url.split('.')[-1].lower().split('?')[0]  # Manejar URLs con parámetros
        if ext not in allowed_extensions:
            return {'valid': False, 'error': f'Extensión no permitida: .{ext}'}
        
        return {'valid': True, 'url': url}


class RateLimiter:
    """Limitador de velocidad para respetar límites de API"""
    
    def __init__(self, messages_per_second: int):
        self.messages_per_second = messages_per_second
        self.min_interval = 1.0 / messages_per_second
        self.last_request_time = 0
    
    def wait_if_needed(self):
        """Esperar si es necesario para respetar el límite de velocidad"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_interval:
            sleep_time = self.min_interval - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()


class MessageQueue:
    """Cola de mensajes para envío masivo con soporte de archivos"""
    
    def __init__(self, twilio_service: TwilioService):
        self.twilio_service = twilio_service
        self.queue = []
        self.processing = False
    
    def add_message(self, to_number: str, message: str, 
                    media_urls: List[str] = None, callback=None):
        """Agregar mensaje a la cola con archivos multimedia opcionales"""
        self.queue.append({
            'to_number': to_number,
            'message': message,
            'media_urls': media_urls,
            'callback': callback,
            'attempts': 0
        })
    
    def process_queue(self):
        """Procesar cola de mensajes"""
        self.processing = True
        
        while self.queue and self.processing:
            item = self.queue.pop(0)
            
            # Enviar mensaje con archivos multimedia si existen
            result = self.twilio_service.send_whatsapp_message(
                item['to_number'],
                item['message'],
                item.get('media_urls')
            )
            
            # Ejecutar callback si existe
            if item['callback']:
                item['callback'](result)
            
            # Si falló y no ha excedido intentos, volver a agregar a la cola
            if not result['success'] and item['attempts'] < Config.MAX_RETRY_ATTEMPTS:
                item['attempts'] += 1
                self.queue.append(item)
    
    def stop_processing(self):
        """Detener procesamiento de la cola"""
        self.processing = False
    
    def get_queue_size(self) -> int:
        """Obtener tamaño de la cola"""
        return len(self.queue)
