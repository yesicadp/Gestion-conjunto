-- =====================================
-- BASE DE DATOS EL CIPRES
-- =====================================

CREATE DATABASE IF NOT EXISTS el_cipres;
USE el_cipres;

-- =====================================
-- TABLA USUARIO
-- =====================================

CREATE TABLE usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(100) UNIQUE NOT NULL,
    contraseña VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    rol VARCHAR(20) NOT NULL
);

-- =====================================
-- TABLA VIVIENDA
-- =====================================

CREATE TABLE vivienda (
    id_vivienda INT AUTO_INCREMENT PRIMARY KEY,
    numero VARCHAR(10) NOT NULL,
    estado VARCHAR(20),
    usuario_id INT UNIQUE,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id_usuario)
);

-- =====================================
-- TABLA PAGO
-- =====================================

CREATE TABLE pago (
    id_pago INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    estado VARCHAR(20),
    vivienda_id INT,
    FOREIGN KEY (vivienda_id) REFERENCES vivienda(id_vivienda)
);

-- =====================================
-- TABLA PARQUEADERO
-- =====================================

CREATE TABLE parqueadero (
    id_parqueadero INT AUTO_INCREMENT PRIMARY KEY,
    numero VARCHAR(10) NOT NULL,
    estado VARCHAR(20),
    vivienda_id INT UNIQUE,
    FOREIGN KEY (vivienda_id) REFERENCES vivienda(id_vivienda)
);

-- =====================================
-- TABLA SALON COMUNAL
-- =====================================

CREATE TABLE salon_comunal (
    id_salon INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100),
    descripcion TEXT,
    capacidad INT
);

-- =====================================
-- TABLA RESERVA
-- =====================================

CREATE TABLE reserva (
    id_reserva INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL,
    hora_inicio TIME,
    hora_fin TIME,
    estado VARCHAR(20),
    usuario_id INT,
    salon_id INT,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id_usuario),
    FOREIGN KEY (salon_id) REFERENCES salon_comunal(id_salon)
);

-- =====================================
-- TABLA ANUNCIO
-- =====================================

CREATE TABLE anuncio (
    id_anuncio INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(100),
    contenido TEXT,
    fecha DATE,
    usuario_id INT,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id_usuario)
);