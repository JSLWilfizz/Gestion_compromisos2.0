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
    name VARCHAR(255)
);

-- Tabla origen (nueva)
CREATE TABLE IF NOT EXISTS origen (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255)
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
    CONSTRAINT fk_id_persona
        FOREIGN KEY (id_persona)
        REFERENCES persona(id),
    CONSTRAINT fk_id_compromiso
        FOREIGN KEY (id_compromiso)
        REFERENCES compromiso(id),
    PRIMARY KEY (id_persona, id_compromiso)
);

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
    password_aleatoria VARCHAR(12);
BEGIN
    -- Generar una contraseña con nombre y apellido solo primeras 12 letras
    password_aleatoria := SUBSTRING(NEW.name, 1, 1) || SUBSTRING(NEW.lastname, 1, 1) || SUBSTRING(NEW.lastname, 2, 1) || SUBSTRING(NEW.lastname, 3, 1) || SUBSTRING(NEW.lastname, 4, 1) || SUBSTRING(NEW.lastname, 5, 1) || SUBSTRING(NEW.lastname, 6, 1) || SUBSTRING(NEW.lastname, 7, 1) || SUBSTRING(NEW.lastname, 8, 1) || SUBSTRING(NEW.lastname, 9, 1) || SUBSTRING(NEW.lastname, 10, 1) || SUBSTRING(NEW.lastname, 11, 1);

        

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
    CONSTRAINT fk_id_persona_archivado FOREIGN KEY (id_persona) REFERENCES persona(id),
    CONSTRAINT fk_id_compromiso_archivado FOREIGN KEY (id_compromiso) REFERENCES compromisos_archivados(id),
    PRIMARY KEY (id_persona, id_compromiso)
);

CREATE TABLE IF NOT EXISTS persona_compromiso_eliminado (
    id_persona INT,
    id_compromiso INT,
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





