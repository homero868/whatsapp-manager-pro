# WhatsApp Manager Pro
Aplicación de escritorio en Python para gestionar envíos masivos de mensajes de WhatsApp utilizando la API de Twilio.

# 🚀 Características
Importación de Contactos: Importa contactos desde archivos Excel (.xlsx, .xls) con detección automática de columnas.
Gestión de Plantillas: Crea y gestiona plantillas de mensajes con variables dinámicas.
Envío Masivo: Envía mensajes a múltiples contactos con límite de velocidad configurable.
Programación de Campañas: Programa envíos para fechas y horas específicas.
Seguimiento en Tiempo Real: Monitorea el estado de los mensajes (enviado, entregado, leído, fallido).
Reportes y Estadísticas: Genera reportes detallados y exporta a Excel.
Autenticación de Usuarios: Sistema seguro con contraseñas hasheadas usando Argon2.
Interfaz Gráfica Moderna: Desarrollada con PyQt6 para una experiencia de usuario fluida.

📋 Requisitos Previos
Python 3.8 o superior
MySQL 5.7 o superior
Cuenta de Twilio con WhatsApp habilitado
Sistema operativo: Windows, macOS o Linux

🔧 Instalación
1. Clonar el repositorio
bash
git clone https://github.com/tu-usuario/whatsapp-manager-pro.git
cd whatsapp-manager-pro

2. Crear entorno virtual
bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En macOS/Linux
source venv/bin/activate
3. Instalar dependencias
bash
pip install -r requirements.txt
4. Configurar base de datos MySQL
bash
# Conectarse a MySQL
mysql -u root -p

# Ejecutar el script de base de datos
mysql> source database_schema.sql
5. Configurar variables de entorno
bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus credenciales
Configurar en .env:

Credenciales de Twilio (Account SID, Auth Token, número de WhatsApp)
Conexión a MySQL (host, puerto, usuario, contraseña)
🚀 Uso
Ejecutar la aplicación
bash
python main.py
Credenciales por defecto
Usuario: admin
Contraseña: admin123
⚠️ Importante: Cambia estas credenciales después del primer inicio de sesión.

📱 Configuración de Twilio
Crear cuenta en Twilio
Visita console.twilio.com
Registra una cuenta gratuita o de pago
Configurar WhatsApp
Ve a Messaging > Try it out > Send a WhatsApp message
Sigue las instrucciones para activar el sandbox de WhatsApp
Copia tu número de WhatsApp (formato: whatsapp:+14155238886)
Obtener credenciales
En el Dashboard, copia tu Account SID
Copia tu Auth Token
Agrega estas credenciales al archivo .env
💡 Guía de Uso
1. Importar Contactos
Prepara un archivo Excel con los contactos
Ve a la pestaña "Contactos"
Haz clic en "Importar Excel"
Selecciona la columna que contiene los números de teléfono
Mapea las columnas adicionales (nombre, email, empresa)
2. Crear Plantillas
Ve a la pestaña "Plantillas"
Haz clic en "Nueva"
Escribe el contenido del mensaje
Usa variables como {nombre}, {email}, {empresa}
Guarda la plantilla
3. Enviar Mensajes
Envío Inmediato:

Haz clic en "Envío Rápido"
Selecciona una plantilla
Selecciona los contactos
Confirma el envío
Envío Programado:

Haz clic en "Programar Campaña"
Nombra la campaña
Selecciona plantilla y fecha/hora
La campaña se ejecutará automáticamente
4. Monitorear Envíos
La pestaña "Campañas" muestra el progreso en tiempo real
Los estados se actualizan automáticamente
Los mensajes fallidos se reintentan automáticamente
5. Generar Reportes
Ve a la pestaña "Reportes"
Selecciona el tipo de reporte
Aplica filtros de fecha si es necesario
Exporta a Excel para análisis adicional
🔒 Seguridad
Contraseñas hasheadas con Argon2
Credenciales almacenadas en variables de entorno
Logs de actividad para auditoría
Validación de números de teléfono
🛠️ Solución de Problemas
Error de conexión a MySQL
Verifica que MySQL esté ejecutándose
Confirma las credenciales en .env
Asegúrate de que la base de datos existe
Error de Twilio
Verifica las credenciales de Twilio
Confirma que el número de WhatsApp esté activo
Revisa los límites de tu cuenta
Problemas de importación de Excel
Asegúrate de que el archivo no esté corrupto
Verifica que los números tengan formato correcto
El límite es de 10,000 contactos por archivo
📊 Estructura del Proyecto
whatsapp-manager-pro/
├── main.py              # Punto de entrada
├── config.py           # Configuración
├── database.py         # Modelos de base de datos
├── auth.py             # Sistema de autenticación
├── twilio_service.py   # Integración con Twilio
├── excel_handler.py    # Manejo de archivos Excel
├── message_scheduler.py # Programador de mensajes
├── logger.py           # Sistema de logging
├── main_window.py      # Ventana principal
├── ui/                 # Módulos de interfaz
│   ├── login_window.py
│   ├── contacts_window.py
│   ├── templates_window.py
│   ├── campaigns_window.py
│   ├── reports_window.py
│   └── settings_window.py
├── database_schema.sql # Esquema de base de datos
├── requirements.txt    # Dependencias
├── .env.example       # Ejemplo de configuración
└── README.md          # Este archivo
🤝 Contribuciones
Las contribuciones son bienvenidas. Por favor:

Fork el proyecto
Crea una rama para tu feature (git checkout -b feature/AmazingFeature)
Commit tus cambios (git commit -m 'Add some AmazingFeature')
Push a la rama (git push origin feature/AmazingFeature)
Abre un Pull Request
📄 Licencia
Este proyecto está bajo la Licencia MIT. Ver el archivo LICENSE para más detalles.

👥 Soporte
Para soporte y consultas:

Abre un issue en GitHub
Contacta al equipo de desarrollo
🙏 Agradecimientos
Twilio por proporcionar la API de WhatsApp
PyQt6 por el framework de interfaz gráfica
La comunidad de Python por las excelentes librerías
