-- Actualizar el usuario admin con el password correcto
-- Password: admin123

USE whatsapp_manager;

-- Primero verificar si existe el usuario admin
SELECT id, username FROM users WHERE username = 'admin';

-- Actualizar el password del usuario admin
-- Este hash corresponde a 'admin123' usando Argon2
UPDATE users 
SET password_hash = '$argon2id$v=19$m=65536,t=3,p=4$YPqZ2bM2RsjJGKOUkkLIfg$2H4sVlF8eYqGFVlJYLpXk4L5rVJLp0QqxVzWS5SDDKY'
WHERE username = 'admin';

-- Si no existe el usuario admin, crearlo
INSERT INTO users (username, password_hash, email, is_active) 
SELECT 'admin', '$argon2id$v=19$m=65536,t=3,p=4$YPqZ2bM2RsjJGKOUkkLIfg$2H4sVlF8eYqGFVlJYLpXk4L5rVJLp0QqxVzWS5SDDKY', 'admin@example.com', TRUE
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin');

-- Verificar que el usuario esté activo
UPDATE users SET is_active = TRUE WHERE username = 'admin';

-- Mostrar el usuario admin
SELECT id, username, email, is_active, created_at FROM users WHERE username = 'admin';
