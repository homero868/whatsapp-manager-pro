# file_uploader.py - Nuevo archivo para manejar la carga de archivos

import os
import shutil
import hashlib
import mimetypes
from typing import Dict, Optional, Tuple
from datetime import datetime
from config import Config
import logging

logger = logging.getLogger(__name__)

class FileUploader:
    """Manejador de carga de archivos"""
    
    # Tipos de archivo permitidos para WhatsApp Business API
    ALLOWED_EXTENSIONS = {
        # Imágenes (Solo JPEG y PNG según WhatsApp)
        'jpg', 'jpeg', 'png',
        # Documentos
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt',
        # Audio (formatos soportados por WhatsApp)
        'aac', 'mp4', 'm4a', 'amr', 'ogg', 'opus',
        # Video (formatos soportados por WhatsApp)
        'mp4', '3gp'
    }
    
    # Límites de tamaño por tipo según WhatsApp Business API (en MB)
    SIZE_LIMITS = {
        'image': 5,      # 5MB para imágenes (JPEG, PNG)
        'document': 100, # 100MB para documentos (PDF, DOC, etc.)
        'audio': 16,     # 16MB para audio
        'video': 16      # 16MB para video
    }
    
    # Límite máximo de archivos por mensaje en WhatsApp
    MAX_FILES_PER_MESSAGE = 10
    
    # Tipos MIME permitidos según WhatsApp Business API
    MIME_TYPES = {
        # Imágenes (Solo JPEG y PNG)
        'image/jpeg': ['jpg', 'jpeg'],
        'image/png': ['png'],
        # Documentos
        'application/pdf': ['pdf'],
        'application/msword': ['doc'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['docx'],
        'application/vnd.ms-excel': ['xls'],
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['xlsx'],
        'application/vnd.ms-powerpoint': ['ppt'],
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['pptx'],
        'text/plain': ['txt'],
        # Audio
        'audio/aac': ['aac'],
        'audio/mp4': ['mp4', 'm4a'],
        'audio/amr': ['amr'],
        'audio/ogg': ['ogg'],
        'audio/opus': ['opus'],
        # Video
        'video/mp4': ['mp4'],
        'video/3gpp': ['3gp']
    }
    
    def __init__(self):
        self.upload_folder = Config.UPLOAD_FOLDER
        self._ensure_upload_folder()
    
    def _ensure_upload_folder(self):
        """Asegurar que existe la carpeta de uploads"""
        os.makedirs(self.upload_folder, exist_ok=True)
        
        # Crear subcarpetas por tipo
        for folder in ['images', 'documents', 'audio', 'video', 'temp']:
            os.makedirs(os.path.join(self.upload_folder, folder), exist_ok=True)
    
    def get_file_type_category(self, mime_type: str) -> str:
        """Obtener categoría del archivo según su tipo MIME"""
        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('audio/'):
            return 'audio'
        elif mime_type.startswith('video/'):
            return 'video'
        else:
            return 'document'
    
    def validate_file(self, file_path: str, original_name: str) -> Tuple[bool, str, Dict]:
        """Validar archivo antes de procesarlo"""
        try:
            # Verificar extensión
            ext = original_name.rsplit('.', 1)[1].lower() if '.' in original_name else ''
            if ext not in self.ALLOWED_EXTENSIONS:
                return False, f"Tipo de archivo no permitido: .{ext}", {}
            
            # Obtener tipo MIME
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Verificar tipo MIME
            mime_allowed = False
            for allowed_mime, extensions in self.MIME_TYPES.items():
                if mime_type == allowed_mime or (mime_type.startswith(allowed_mime.split('/')[0]) and ext in extensions):
                    mime_allowed = True
                    break
            
            if not mime_allowed:
                return False, f"Tipo MIME no permitido: {mime_type}", {}
            
            # Verificar tamaño
            file_size = os.path.getsize(file_path)
            file_category = self.get_file_type_category(mime_type)
            max_size = self.SIZE_LIMITS.get(file_category, 16) * 1024 * 1024  # Convertir a bytes
            
            if file_size > max_size:
                size_mb = file_size / (1024 * 1024)
                max_mb = max_size / (1024 * 1024)
                return False, f"Archivo demasiado grande: {size_mb:.1f}MB (máximo: {max_mb}MB)", {}
            
            # Información del archivo
            file_info = {
                'extension': ext,
                'mime_type': mime_type,
                'category': file_category,
                'size': file_size,
                'size_mb': round(file_size / (1024 * 1024), 2)
            }
            
            return True, "Archivo válido", file_info
            
        except Exception as e:
            logger.error(f"Error validando archivo: {e}")
            return False, f"Error validando archivo: {str(e)}", {}
    
    def generate_unique_filename(self, original_name: str, template_id: int) -> str:
        """Generar nombre único para el archivo"""
        ext = original_name.rsplit('.', 1)[1].lower() if '.' in original_name else ''
        
        # Crear hash único basado en tiempo y nombre original
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        hash_input = f"{original_name}_{template_id}_{timestamp}".encode()
        file_hash = hashlib.md5(hash_input).hexdigest()[:8]
        
        # Sanitizar nombre original (quitar caracteres especiales)
        import re
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', original_name.rsplit('.', 1)[0])
        safe_name = safe_name[:50]  # Limitar longitud
        
        return f"{template_id}_{timestamp}_{file_hash}_{safe_name}.{ext}"
    
    def save_file(self, file_path: str, original_name: str, template_id: int) -> Tuple[bool, str, Dict]:
        """Guardar archivo en el sistema"""
        try:
            # Validar archivo
            is_valid, message, file_info = self.validate_file(file_path, original_name)
            if not is_valid:
                return False, message, {}
            
            # Generar nombre único
            unique_filename = self.generate_unique_filename(original_name, template_id)
            
            # Determinar carpeta de destino
            category = file_info['category']
            if category == 'image':
                folder = 'images'
            elif category == 'audio':
                folder = 'audio'
            elif category == 'video':
                folder = 'video'
            else:
                folder = 'documents'
            
            # Ruta completa de destino
            destination_path = os.path.join(self.upload_folder, folder, unique_filename)
            
            # Copiar archivo
            shutil.copy2(file_path, destination_path)
            
            # Preparar respuesta
            result = {
                'file_name': original_name,
                'file_path': destination_path,
                'file_type': file_info['extension'],
                'file_size': file_info['size'],
                'mime_type': file_info['mime_type'],
                'category': category,
                'unique_name': unique_filename
            }
            
            logger.info(f"Archivo guardado: {destination_path}")
            return True, "Archivo guardado exitosamente", result
            
        except Exception as e:
            logger.error(f"Error guardando archivo: {e}")
            return False, f"Error guardando archivo: {str(e)}", {}
    
    def delete_file(self, file_path: str) -> bool:
        """Eliminar archivo del sistema"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Archivo eliminado: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error eliminando archivo: {e}")
            return False
    
    def get_file_url(self, file_path: str) -> Optional[str]:
        """Obtener URL pública del archivo usando servidor local"""
        try:
            # Importar el servidor local
            from local_file_server import get_public_file_url
            
            # Obtener URL del servidor local
            url = get_public_file_url(file_path)
            
            if url:
                logger.info(f"URL generada para archivo: {url}")
                return url
            else:
                logger.warning(f"No se pudo generar URL para: {file_path}")
                return None
                
        except ImportError:
            logger.error("local_file_server no está disponible. Asegúrese de que el servidor esté iniciado.")
            return None
        except Exception as e:
            logger.error(f"Error obteniendo URL del archivo: {e}")
            return None
    
    def get_file_preview(self, file_path: str, file_type: str) -> Optional[str]:
        """Generar vista previa del archivo si es posible"""
        try:
            if file_type in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                # Para imágenes, podríamos generar thumbnails
                # Por ahora retornamos la ruta original
                return file_path
            elif file_type == 'pdf':
                # Para PDFs, podríamos generar una imagen de la primera página
                return None
            else:
                return None
        except Exception as e:
            logger.error(f"Error generando preview: {e}")
            return None
