import argon2
from typing import Optional, Dict
import logging
from database import UserModel, ActivityLogModel

logger = logging.getLogger(__name__)

class AuthManager:
    def __init__(self):
        self.ph = argon2.PasswordHasher()
        self.user_model = UserModel()
        self.log_model = ActivityLogModel()
        self.current_user = None
    
    def hash_password(self, password: str) -> str:
        """Hashear contraseña usando Argon2"""
        return self.ph.hash(password)
    
    def verify_password(self, password_hash: str, password: str) -> bool:
        """Verificar contraseña contra hash"""
        try:
            self.ph.verify(password_hash, password)
            return True
        except argon2.exceptions.VerifyMismatchError:
            return False
        except Exception as e:
            logger.error(f"Error verificando contraseña: {e}")
            return False
    
    def login(self, username: str, password: str) -> Optional[Dict]:
        """Iniciar sesión"""
        try:
            # Obtener usuario
            user = self.user_model.get_user_by_username(username)
            if not user:
                logger.warning(f"Intento de login fallido: usuario '{username}' no encontrado")
                return None
            
            # Verificar contraseña
            if not self.verify_password(user['password_hash'], password):
                logger.warning(f"Intento de login fallido: contraseña incorrecta para '{username}'")
                self.log_model.log_activity(
                    user['id'], 
                    'login_failed', 
                    'Contraseña incorrecta'
                )
                return None
            
            # Verificar si el usuario está activo
            if not user['is_active']:
                logger.warning(f"Intento de login fallido: usuario '{username}' inactivo")
                return None
            
            # Login exitoso - actualizar último login en la base de datos
            self.user_model.update_last_login(user['id'])
            
            # Establecer usuario actual
            self.current_user = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
            
            # Registrar actividad
            self.log_model.log_activity(user['id'], 'login', 'Login exitoso')
            
            logger.info(f"Usuario '{username}' ha iniciado sesión")
            return self.current_user
            
        except Exception as e:
            logger.error(f"Error en login: {e}")
            return None
    
    def logout(self):
        """Cerrar sesión"""
        if self.current_user:
            self.log_model.log_activity(self.current_user['id'], 'logout', 'Logout exitoso')
            logger.info(f"Usuario '{self.current_user['username']}' ha cerrado sesión")
            self.current_user = None
    
    def register(self, username: str, password: str, email: str = None) -> bool:
        """Registrar nuevo usuario"""
        try:
            # Verificar si el usuario ya existe
            if self.user_model.get_user_by_username(username):
                logger.warning(f"Intento de registro fallido: usuario '{username}' ya existe")
                return False
            
            # Hashear contraseña
            password_hash = self.hash_password(password)
            
            # Crear usuario
            user_id = self.user_model.create_user(username, password_hash, email)
            
            if user_id:
                # Registrar actividad
                self.log_model.log_activity(user_id, 'register', 'Usuario registrado')
                logger.info(f"Nuevo usuario registrado: '{username}'")
                return True
            else:
                return False
            
        except Exception as e:
            logger.error(f"Error en registro: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Verificar si hay un usuario autenticado"""
        return self.current_user is not None
    
    def get_current_user(self) -> Optional[Dict]:
        """Obtener usuario actual"""
        return self.current_user
    
    def require_auth(self, func):
        """Decorador para requerir autenticación"""
        def wrapper(*args, **kwargs):
            if not self.is_authenticated():
                raise PermissionError("Se requiere autenticación")
            return func(*args, **kwargs)
        return wrapper

# Instancia global del gestor de autenticación
auth_manager = AuthManager()
