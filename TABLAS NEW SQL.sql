DROP TABLE IF EXISTS persona_compromiso CASCADE;
DROP TABLE IF EXISTS reunion_compromiso CASCADE;
DROP TABLE IF EXISTS compromiso CASCADE;
DROP TABLE IF EXISTS reunion CASCADE;
DROP TABLE IF EXISTS staff_persona CASCADE;
DROP TABLE IF EXISTS staff CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS persona_departamento CASCADE;
DROP TABLE IF EXISTS departamento CASCADE;
DROP TABLE IF EXISTS persona CASCADE;
DROP TABLE IF EXISTS area CASCADE;
DROP TABLE IF EXISTS origen CASCADE;
DROP TABLE IF EXISTS compromiso_modificaciones CASCADE;

--nueva tabla persona
CREATE TABLE persona (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    lastname VARCHAR(255),
    rut VARCHAR(12),
    dv VARCHAR(1) NOT NULL,
    profesion VARCHAR(255),
    correo VARCHAR(255) ,
    cargo VARCHAR(255),
    anexo_telefonico VARCHAR(255),
    nivel_jerarquico VARCHAR(255)       
);
-- Tabla departamento
CREATE TABLE IF NOT EXISTS departamento (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    id_departamento_padre INT -- Relación jerárquica con otro departamento
);

-- Tabla intermedia para persona y departamento
CREATE TABLE IF NOT EXISTS persona_departamento (
    id_persona INT,
    id_departamento INT,
    es_director BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_id_persona FOREIGN KEY (id_persona) REFERENCES persona(id),
    CONSTRAINT fk_id_departamento FOREIGN KEY (id_departamento) REFERENCES departamento(id),
    PRIMARY KEY (id_persona, id_departamento)
);

-- Tabla de usuarios con referencia a persona
CREATE TABLE IF NOT EXISTS users(
    username VARCHAR(255),
    password VARCHAR(255),
    id_persona INT,
    CONSTRAINT fk_id_persona
        FOREIGN KEY (id_persona)
        REFERENCES persona(id)
);

-- Tabla staff
CREATE TABLE IF NOT EXISTS staff(
    id SERIAL PRIMARY KEY,
    name VARCHAR(255)
);

-- Tabla intermedia staff_persona
CREATE TABLE IF NOT EXISTS staff_persona(
    id_staff INT,
    id_persona INT,
    CONSTRAINT fk_id_staff
        FOREIGN KEY (id_staff)
        REFERENCES staff(id),
    CONSTRAINT fk_id_persona
        FOREIGN KEY (id_persona)
        REFERENCES persona(id),
    PRIMARY KEY (id_staff, id_persona)
);

-- Tabla área (nueva)
CREATE TABLE IF NOT EXISTS area (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    id_departamento INT,
    CONSTRAINT fk_id_departamento_area
        FOREIGN KEY (id_departamento)
        REFERENCES departamento(id)
);

-- Tabla origen (nueva)
CREATE TABLE IF NOT EXISTS origen (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    id_departamento INT,
    CONSTRAINT fk_id_departamento_origen
        FOREIGN KEY (id_departamento)
        REFERENCES departamento(id)
);

-- Tabla reunion con referencia a calendario, staff, area y origen
CREATE TABLE IF NOT EXISTS reunion(
    id SERIAL PRIMARY KEY,
	nombre VARCHAR(255),
    id_staff INT,
    id_area INT, -- Nueva referencia a la tabla de área
    id_origen INT, -- Nueva referencia a la tabla de origen
    fecha_creacion TIMESTAMP,
    lugar VARCHAR(255),
    asistentes TEXT,
    proximas_reuniones TEXT,
    acta_pdf VARCHAR(255),
    correos TEXT,
    temas_analizado TEXT,
    tema TEXT,
    CONSTRAINT fk_id_staff_reunion
        FOREIGN KEY (id_staff)
        REFERENCES staff(id),
    CONSTRAINT fk_id_area_reunion
        FOREIGN KEY (id_area)
        REFERENCES area(id),
    CONSTRAINT fk_id_origen_reunion
        FOREIGN KEY (id_origen)
        REFERENCES origen(id)
);

-- Tabla de compromisos con relación a departamento
CREATE TABLE IF NOT EXISTS compromiso(
    id SERIAL PRIMARY KEY,
    descripcion TEXT,
    estado VARCHAR(255),
    prioridad VARCHAR(255),
    fecha_creacion TIMESTAMP,
    avance INT,
    fecha_limite TIMESTAMP,
    comentario TEXT,
    comentario_direccion TEXT,
    id_departamento INT,  -- Relación con el departamento
    CONSTRAINT fk_id_departamento_compromiso
        FOREIGN KEY (id_departamento)
        REFERENCES departamento(id)
);

-- Tabla intermedia persona_compromiso (N:N entre persona y compromiso)
CREATE TABLE IF NOT EXISTS persona_compromiso(
    id_persona INT,
    id_compromiso INT,
    es_responsable_principal BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_id_persona
        FOREIGN KEY (id_persona)
        REFERENCES persona(id),
    CONSTRAINT fk_id_compromiso
        FOREIGN KEY (id_compromiso)
        REFERENCES compromiso(id),
    PRIMARY KEY (id_persona, id_compromiso)
);

-- Add a unique constraint to ensure only one principal per compromiso
CREATE UNIQUE INDEX unique_principal_per_compromiso
ON persona_compromiso(id_compromiso)
WHERE es_responsable_principal = true;

-- Tabla intermedia reunion_compromiso (N:N entre reunion y compromiso)
CREATE TABLE IF NOT EXISTS reunion_compromiso(
    id_reunion INT,
    id_compromiso INT,
    CONSTRAINT fk_id_reunion
        FOREIGN KEY (id_reunion)
        REFERENCES reunion(id),
    CONSTRAINT fk_id_compromiso
        FOREIGN KEY (id_compromiso)
        REFERENCES compromiso(id),
    PRIMARY KEY (id_reunion, id_compromiso)
);

CREATE TABLE compromiso_modificaciones (
    id SERIAL PRIMARY KEY,
    id_compromiso INT NOT NULL,
    id_usuario INT NOT NULL,
    fecha_modificacion TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (id_compromiso) REFERENCES compromiso(id) ON DELETE CASCADE,
    FOREIGN KEY (id_usuario) REFERENCES persona(id) ON DELETE SET NULL
);

-- Tabla invitados
CREATE TABLE IF NOT EXISTS invitados (
    id SERIAL PRIMARY KEY,
    nombre_completo VARCHAR(255) NOT NULL,
    institucion VARCHAR(255) NOT NULL,
    correo VARCHAR(255) NOT NULL UNIQUE,
    telefono VARCHAR(255)
);

-- Crear función para el trigger
CREATE OR REPLACE FUNCTION crear_usuario()
RETURNS TRIGGER AS $$
DECLARE
    password_aleatoria VARCHAR(255);
BEGIN
    -- Generar una contraseña con primera letra del nombre y el RUT completo
    password_aleatoria := 
        CASE WHEN NEW.name IS NULL OR LENGTH(NEW.name) = 0 
             THEN '' 
             ELSE SUBSTRING(NEW.name FROM 1 FOR 1) 
        END || 
        COALESCE(NEW.rut, '');

    -- Insertar en la tabla users, asociando el id de persona
    INSERT INTO users (id_persona, username, password)
    VALUES (NEW.id, NEW.rut, password_aleatoria);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Crear el trigger
CREATE TRIGGER trigger_crear_usuario
AFTER INSERT ON persona
FOR EACH ROW
EXECUTE FUNCTION crear_usuario();


--nuevo 24/01/2025

-- Tabla para guardar compromisos eliminados
CREATE TABLE IF NOT EXISTS compromiso_eliminado (
    id SERIAL PRIMARY KEY, -- Clave primaria del compromiso eliminado
    descripcion TEXT,
    estado VARCHAR(255),
    prioridad VARCHAR(255),
    fecha_creacion TIMESTAMP,
    avance INT,
    fecha_limite TIMESTAMP,
    comentario TEXT,
    comentario_direccion TEXT,
    id_departamento INT,
    fecha_eliminacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Fecha de eliminación
    eliminado_por INT, -- Usuario que eliminó el compromiso
    CONSTRAINT fk_departamento_compromiso_eliminado FOREIGN KEY (id_departamento)
        REFERENCES departamento(id)
);


-- Tabla para guardar compromisos archivados
CREATE TABLE IF NOT EXISTS compromisos_archivados (
    id SERIAL PRIMARY KEY, -- Clave primaria del compromiso archivado
    descripcion TEXT,
    estado VARCHAR(255),
    prioridad VARCHAR(255),
    fecha_creacion TIMESTAMP,
    avance INT,
    fecha_limite TIMESTAMP,
    comentario TEXT,
    comentario_direccion TEXT,
    id_departamento INT,
    fecha_archivado TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Fecha de archivado
    archivado_por INT, -- Usuario que archivó el compromiso
    CONSTRAINT fk_departamento_compromiso_archivado FOREIGN KEY (id_departamento)
        REFERENCES departamento(id)
);

-- Tabla intermedia para responsables de compromisos archivados
CREATE TABLE IF NOT EXISTS persona_compromiso_archivado (
    id_persona INT,
    id_compromiso INT,
    es_responsable_principal BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_id_persona_archivado FOREIGN KEY (id_persona) REFERENCES persona(id),
    CONSTRAINT fk_id_compromiso_archivado FOREIGN KEY (id_compromiso) REFERENCES compromisos_archivados(id),
    PRIMARY KEY (id_persona, id_compromiso)
);

CREATE TABLE IF NOT EXISTS persona_compromiso_eliminado (
    id_persona INT,
    id_compromiso INT,
    es_responsable_principal BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_id_persona_eliminado
        FOREIGN KEY (id_persona) REFERENCES persona(id),
    CONSTRAINT fk_id_compromiso_eliminado
        FOREIGN KEY (id_compromiso) REFERENCES compromiso_eliminado(id),
    PRIMARY KEY (id_persona, id_compromiso)
);

CREATE TABLE IF NOT EXISTS reunion_compromiso_archivado (
    id_reunion INT,
    id_compromiso INT,
    CONSTRAINT fk_id_reunion_archivado
        FOREIGN KEY (id_reunion) REFERENCES reunion(id),
    CONSTRAINT fk_id_compromiso_archivado
        FOREIGN KEY (id_compromiso) REFERENCES compromisos_archivados(id)
);

CREATE TABLE IF NOT EXISTS reunion_compromiso_eliminado (
    id_reunion INT,
    id_compromiso INT,
    CONSTRAINT fk_id_reunion_eliminado
        FOREIGN KEY (id_reunion) REFERENCES reunion(id),
    CONSTRAINT fk_id_compromiso_eliminado
        FOREIGN KEY (id_compromiso) REFERENCES compromiso_eliminado(id)
);

-- Function to set es_responsable_principal to true for the first person added to a compromiso
CREATE OR REPLACE FUNCTION set_responsable_principal()
RETURNS TRIGGER AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM persona_compromiso
        WHERE id_compromiso = NEW.id_compromiso AND es_responsable_principal = true
    ) THEN
        NEW.es_responsable_principal := true;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to call the function before inserting into persona_compromiso
CREATE TRIGGER trg_set_responsable_principal
BEFORE INSERT ON persona_compromiso
FOR EACH ROW
EXECUTE PROCEDURE set_responsable_principal();



-- Add department relationship to area table
ALTER TABLE area 
ADD COLUMN id_departamento INT,
ADD CONSTRAINT fk_id_departamento_area
    FOREIGN KEY (id_departamento)
    REFERENCES departamento(id);

-- Add department relationship to origen table
ALTER TABLE origen
ADD COLUMN id_departamento INT,
ADD CONSTRAINT fk_id_departamento_origen
    FOREIGN KEY (id_departamento)
    REFERENCES departamento(id);

-- Tabla para almacenar verificadores de compromisos
CREATE TABLE IF NOT EXISTS compromiso_verificador (
    id SERIAL PRIMARY KEY,
    id_compromiso INT NOT NULL,
    nombre_archivo VARCHAR(255) NOT NULL,
    ruta_archivo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    subido_por INT,
    CONSTRAINT fk_compromiso_verificador
        FOREIGN KEY (id_compromiso)
        REFERENCES compromiso(id) ON DELETE CASCADE,
    CONSTRAINT fk_subido_por
        FOREIGN KEY (subido_por)
        REFERENCES persona(id) ON DELETE SET NULL
);

-- Tabla para almacenar verificadores de compromisos archivados
CREATE TABLE IF NOT EXISTS compromiso_archivado_verificador (
    id SERIAL PRIMARY KEY,
    id_compromiso INT NOT NULL,
    nombre_archivo VARCHAR(255) NOT NULL,
    ruta_archivo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    fecha_subida TIMESTAMP,
    subido_por INT,
    CONSTRAINT fk_compromiso_archivado_verificador
        FOREIGN KEY (id_compromiso)
        REFERENCES compromisos_archivados(id) ON DELETE CASCADE
);

-- Tabla para almacenar verificadores de compromisos eliminados
CREATE TABLE IF NOT EXISTS compromiso_eliminado_verificador (
    id SERIAL PRIMARY KEY,
    id_compromiso INT NOT NULL,
    nombre_archivo VARCHAR(255) NOT NULL,
    ruta_archivo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    fecha_subida TIMESTAMP,
    subido_por INT,
    CONSTRAINT fk_compromiso_eliminado_verificador
        FOREIGN KEY (id_compromiso)
        REFERENCES compromiso_eliminado(id) ON DELETE CASCADE
);

-- Asegurarse de que hay índices para optimizar las queries con verificadores
CREATE INDEX IF NOT EXISTS idx_compromiso_verificador_compromiso_id ON compromiso_verificador(id_compromiso);
CREATE INDEX IF NOT EXISTS idx_compromiso_archivado_verificador_compromiso_id ON compromiso_archivado_verificador(id_compromiso);
CREATE INDEX IF NOT EXISTS idx_compromiso_eliminado_verificador_compromiso_id ON compromiso_eliminado_verificador(id_compromiso);

-- Asegurarse de que las claves foráneas están configuradas correctamente
ALTER TABLE compromiso_verificador
    DROP CONSTRAINT IF EXISTS fk_compromiso_verificador,
    ADD CONSTRAINT fk_compromiso_verificador
        FOREIGN KEY (id_compromiso)
        REFERENCES compromiso(id) ON DELETE CASCADE;

ALTER TABLE compromiso_archivado_verificador
    DROP CONSTRAINT IF EXISTS fk_compromiso_archivado_verificador,
    ADD CONSTRAINT fk_compromiso_archivado_verificador
        FOREIGN KEY (id_compromiso)
        REFERENCES compromisos_archivados(id) ON DELETE CASCADE;

ALTER TABLE compromiso_eliminado_verificador
    DROP CONSTRAINT IF EXISTS fk_compromiso_eliminado_verificador,
    ADD CONSTRAINT fk_compromiso_eliminado_verificador
        FOREIGN KEY (id_compromiso)
        REFERENCES compromiso_eliminado(id) ON DELETE CASCADE;

-- Asegurar que existen vistas para facilitar consultas de verificadores
CREATE OR REPLACE VIEW vista_compromisos_con_verificadores AS
SELECT 
    c.id AS compromiso_id,
    c.descripcion,
    c.estado,
    c.fecha_limite,
    d.name AS departamento_name,
    COUNT(cv.id) AS num_verificadores
FROM 
    compromiso c
LEFT JOIN 
    compromiso_verificador cv ON c.id = cv.id_compromiso
LEFT JOIN 
    departamento d ON c.id_departamento = d.id
GROUP BY 
    c.id, c.descripcion, c.estado, c.fecha_limite, d.name;

CREATE OR REPLACE VIEW vista_compromisos_archivados_con_verificadores AS
SELECT 
    ca.id AS compromiso_id,
    ca.descripcion,
    ca.estado,
    ca.fecha_limite,
    ca.fecha_archivado,
    d.name AS departamento_name,
    COUNT(cv.id) AS num_verificadores
FROM 
    compromisos_archivados ca
LEFT JOIN 
    compromiso_archivado_verificador cv ON ca.id = cv.id_compromiso
LEFT JOIN 
    departamento d ON ca.id_departamento = d.id
GROUP BY 
    ca.id, ca.descripcion, ca.estado, ca.fecha_limite, ca.fecha_archivado, d.name;

-- Agregar columnas id_origen e id_area a compromisos_archivados
ALTER TABLE compromisos_archivados 
ADD COLUMN id_origen INTEGER,
ADD COLUMN id_area INTEGER;

-- Agregar columnas id_origen e id_area a compromiso_eliminado  
ALTER TABLE compromiso_eliminado 
ADD COLUMN id_origen INTEGER,
ADD COLUMN id_area INTEGER;

