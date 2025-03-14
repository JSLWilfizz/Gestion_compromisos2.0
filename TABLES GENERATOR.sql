-- Borrar tablas si existen
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

-- Crear primero la tabla persona
CREATE TABLE IF NOT EXISTS persona (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    lastname VARCHAR(255),
	rut VARCHAR(255),
	dv CHAR,
    position VARCHAR(255)
);

-- Tabla departamento
CREATE TABLE IF NOT EXISTS departamento (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255)
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
    proximas_fechas TEXT,
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

-- Agregar columnas adicionales
ALTER TABLE reunion ADD COLUMN acta_pdf VARCHAR(255);
ALTER TABLE compromiso ADD COLUMN comentario TEXT;
ALTER TABLE reunion ADD COLUMN asistentes TEXT;
ALTER TABLE reunion ADD COLUMN correos TEXT;
ALTER TABLE reunion ADD COLUMN temas_analizado TEXT;
ALTER TABLE compromiso ADD COLUMN comentario_direccion TEXT;

-- Inserciones de ejemplo

-- Insertar personas
INSERT INTO persona (name, lastname, position)
VALUES
('Juan', 'Perez', 'Manager'),
('Maria', 'Lopez', 'Director'),
('Carlos', 'Garcia', 'Analyst');

-- Insertar departamentos
INSERT INTO departamento (name)
VALUES
('Recursos Humanos'),
('Finanzas'),
('TI');

-- Relacionar personas con departamentos
INSERT INTO persona_departamento (id_persona, id_departamento, es_director)
VALUES
(1, 1, FALSE),
(2, 2, TRUE),
(3, 3, FALSE);

-- Insertar usuarios
INSERT INTO users (username, password, id_persona)
VALUES
('juan.perez', 'password123', 1),
('maria.lopez', 'admin456', 2),
('carlos.garcia', 'analyst789', 3);

-- Insertar staff
INSERT INTO staff (name)
VALUES
('Equipo A'),
('Equipo B');

-- Insertar relación staff-persona
INSERT INTO staff_persona (id_staff, id_persona)
VALUES
(1, 1),
(2, 2);

-- Insertar calendario
INSERT INTO calendario (fecha, descripcion)
VALUES
('2024-12-01', 'Calendario de Proyectos 2024'),
('2024-12-15', 'Calendario de Fin de Año');

-- Insertar áreas
INSERT INTO area (name)
VALUES
('Seguridad'),
('Finanzas'),
('Tecnología');

-- Insertar orígenes
INSERT INTO origen (name)
VALUES
('Interno'),
('Externo');

-- Insertar reuniones
INSERT INTO reunion (nombre, id_staff, id_area, id_origen, fecha_creacion)
VALUES
('Reunión Seguridad', 1, 1, 1, '2024-12-01 10:00:00'),
('Reunión Finanzas', 2, 2, 2, '2024-12-15 14:00:00');

-- Insertar compromisos
INSERT INTO compromiso (descripcion, estado, prioridad, fecha_limite, id_departamento)
VALUES
('Implementar nueva política de seguridad', 'Pendiente', 'Alta', '2024-12-10', 1),
('Actualizar sistema contable', 'Completado', 'Media', '2024-12-20', 2);

-- Insertar relación persona-compromiso
INSERT INTO persona_compromiso (id_persona, id_compromiso)
VALUES
(1, 1),
(2, 2);

-- Insertar relación reunion-compromiso
INSERT INTO reunion_compromiso (id_reunion, id_compromiso)
VALUES
(1, 1),
(2, 2);

-- Crear función para el trigger
CREATE OR REPLACE FUNCTION crear_usuario()
RETURNS TRIGGER AS $$
DECLARE
    password_aleatoria VARCHAR(12);
BEGIN
    -- Generar una contraseña aleatoria de 12 caracteres
    SELECT string_agg(
        chr((trunc(random() * 62 + 48)::int)),
        ''
    )
    FROM generate_series(1, 12) INTO password_aleatoria;

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

