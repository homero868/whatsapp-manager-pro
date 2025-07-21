# local_file_server.py - Servidor local para servir archivos estáticos

try:
    from flask import Flask, send_file, abort, send_from_directory, request
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("ERROR: Flask no está instalado. Ejecuta: pip install flask")

import os
import threading
import logging
from config import Config

logger = logging.getLogger(__name__)

class LocalFileServer:
    """Servidor local para servir archivos estáticos en desarrollo"""
    
    def __init__(self, port=8888):
        if not FLASK_AVAILABLE:
            raise ImportError("Flask no está disponible. Instala con: pip install flask")
            
        self.app = Flask(__name__)
        self.port = port
        self.server_thread = None
        self.is_running = False
        
        # Intentar detectar ngrok automáticamente
        self.base_url = self._get_base_url(port)
        
        self.upload_folder = Config.UPLOAD_FOLDER
        
        # Configurar rutas
        self._setup_routes()
    
    def _get_base_url(self, port):
        """Detectar URL base (ngrok si está disponible, sino localhost)"""
        try:
            # Intentar obtener URL de ngrok
            import requests
            ngrok_api = f"http://localhost:4040/api/tunnels"
            response = requests.get(ngrok_api, timeout=1)
            tunnels = response.json()['tunnels']
            
            # Buscar el túnel HTTPS
            for tunnel in tunnels:
                if tunnel['proto'] == 'https' and str(port) in tunnel['config']['addr']:
                    logger.info(f"Ngrok detectado: {tunnel['public_url']}")
                    return tunnel['public_url']
        except:
            pass
        
        # Si no hay ngrok, usar localhost
        logger.warning("Ngrok no detectado. Usando localhost (no funcionará con Twilio)")
        return f"http://localhost:{port}"
        
        # Configurar rutas
        self._setup_routes()
    
    def _setup_routes(self):
        """Configurar rutas del servidor"""
        
        @self.app.route('/uploads/<path:filepath>')
        def serve_file(filepath):
            """Servir archivo desde la carpeta de uploads"""
            logger.info(f"Solicitud recibida para archivo: {filepath}")
            
            try:
                # Construir ruta completa
                full_path = os.path.join(self.upload_folder, filepath)
                logger.debug(f"Ruta completa: {full_path}")
                
                # Verificar que el archivo existe
                if not os.path.exists(full_path):
                    logger.error(f"Archivo no encontrado: {full_path}")
                    return "Archivo no encontrado", 404
                
                # Verificar seguridad
                if not os.path.abspath(full_path).startswith(os.path.abspath(self.upload_folder)):
                    logger.error(f"Intento de acceso no autorizado: {full_path}")
                    return "Acceso denegado", 403
                
                # Usar send_from_directory que es más seguro
                from flask import send_from_directory
                directory = os.path.dirname(full_path)
                filename = os.path.basename(full_path)
                
                logger.info(f"Sirviendo archivo: {filename} desde {directory}")
                return send_from_directory(directory, filename)
                
            except Exception as e:
                logger.error(f"Error sirviendo archivo: {e}", exc_info=True)
                return f"Error interno: {str(e)}", 500
        
        @self.app.route('/health')
        def health_check():
            """Verificar que el servidor está funcionando"""
            return {'status': 'ok', 'server': 'LocalFileServer'}, 200
        
        @self.app.errorhandler(404)
        def not_found(e):
            logger.warning(f"404 - Ruta no encontrada: {request.path}")
            return {'error': 'Not found'}, 404
        
        @self.app.errorhandler(500)
        def server_error(e):
            logger.error(f"500 - Error interno: {str(e)}")
            return {'error': 'Internal server error'}, 500
    
    def start(self):
        """Iniciar servidor en un hilo separado"""
        if self.is_running:
            logger.warning("El servidor ya está en ejecución")
            return
            
        def run_server():
            try:
                logger.info(f"Iniciando servidor Flask en 0.0.0.0:{self.port}")
                from werkzeug.serving import make_server
                
                # Crear servidor
                self.server = make_server('0.0.0.0', self.port, self.app, threaded=True)
                self.is_running = True
                
                # Iniciar servidor
                self.server.serve_forever()
                
            except Exception as e:
                logger.error(f"Error iniciando servidor Flask: {e}")
                self.is_running = False
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # Esperar un momento para que el servidor inicie
        import time
        time.sleep(2)
        
        # Verificar que el servidor está respondiendo
        self._verify_server()
        
        logger.info(f"URL base configurada: {self.base_url}")
        
        if "localhost" in self.base_url:
            logger.warning("⚠️  IMPORTANTE: Para enviar archivos con Twilio, ejecuta 'ngrok http 8888' en otra terminal")
    
    def _verify_server(self):
        """Verificar que el servidor está funcionando"""
        max_attempts = 5
        attempt = 0
        
        while attempt < max_attempts:
            try:
                import requests
                response = requests.get(f"http://localhost:{self.port}/health", timeout=1)
                if response.status_code == 200:
                    logger.info(f"✅ Servidor Flask verificado y funcionando en puerto {self.port}")
                    return True
            except:
                pass
            
            attempt += 1
            if attempt < max_attempts:
                import time
                time.sleep(1)
        
        logger.error(f"❌ No se pudo verificar el servidor Flask después de {max_attempts} intentos")
        return False
    
    def stop(self):
        """Detener el servidor"""
        if hasattr(self, 'server') and self.server:
            self.server.shutdown()
            self.is_running = False
            logger.info("Servidor detenido")
    
    def get_file_url(self, file_path: str) -> str:
        """Obtener URL pública para un archivo"""
        # Obtener ruta relativa desde upload_folder
        try:
            rel_path = os.path.relpath(file_path, self.upload_folder)
            # Reemplazar backslashes con forward slashes para URLs
            rel_path = rel_path.replace('\\', '/')
            return f"{self.base_url}/uploads/{rel_path}"
        except Exception as e:
            logger.error(f"Error generando URL para archivo: {e}")
            return None


# Instancia global del servidor
file_server = LocalFileServer()

# Función auxiliar para obtener URL de archivo
def get_public_file_url(file_path: str) -> str:
    """Obtener URL pública para un archivo local"""
    return file_server.get_file_url(file_path)
