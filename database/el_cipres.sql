DROP DATABASE IF EXISTS el_cipres;
CREATE DATABASE el_cipres;
USE el_cipres;

CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombres VARCHAR(50) NOT NULL,
    apellidos VARCHAR(50) NOT NULL,
    correo_electronico VARCHAR(100) NOT NULL UNIQUE,
    contrasena VARCHAR(255) NOT NULL,
    rol ENUM('administrador', 'residente') NOT NULL,
    codigo_recuperacion VARCHAR(8) NULL,
    vencimiento_codigo DATETIME NULL
);

CREATE TABLE viviendas (
    id_vivienda INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    tiene_vehiculo TINYINT(1) NOT NULL DEFAULT 0,
    estado_financiero ENUM('al dia', 'pendiente', 'en mora') NOT NULL,

    CONSTRAINT fk_vivienda_usuario
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);

CREATE TABLE parqueaderos (
    id_parqueadero INT AUTO_INCREMENT PRIMARY KEY,
    estado ENUM('disponible','ocupado') NOT NULL DEFAULT 'ocupado'
);


CREATE TABLE asignacion_parqueaderos (
    id_asignacion INT AUTO_INCREMENT PRIMARY KEY,
    id_parqueadero INT NOT NULL,
    id_vivienda INT NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,

    CONSTRAINT fk_asig_parq
    FOREIGN KEY (id_parqueadero) REFERENCES parqueaderos(id_parqueadero),

    CONSTRAINT fk_asig_viv
    FOREIGN KEY (id_vivienda) REFERENCES viviendas(id_vivienda)
);

CREATE TABLE reservas (
    id_reserva INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    fecha_evento DATE NOT NULL,
    estado ENUM('pendiente', 'aprobada', 'rechazada') NOT NULL,

    CONSTRAINT fk_reserva_usuario
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);

CREATE TABLE facturas (
    id_factura INT AUTO_INCREMENT PRIMARY KEY,
    id_vivienda INT NOT NULL,
    fecha DATE NOT NULL,
    fecha_pago_oportuno DATE NOT NULL,
    fecha_limite DATE NOT NULL,
    estado ENUM('pendiente', 'pagado', 'vencido') NOT NULL,

    CONSTRAINT fk_factura_vivienda
    FOREIGN KEY (id_vivienda) REFERENCES viviendas(id_vivienda)
);

CREATE TABLE detalle_facturas (
    id_detalle INT AUTO_INCREMENT PRIMARY KEY,
    id_factura INT NOT NULL,
    concepto ENUM('administracion', 'parqueadero', 'reserva', 'multa') NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    descripcion VARCHAR(100),

    CONSTRAINT fk_detalle_factura
    FOREIGN KEY (id_factura) REFERENCES facturas(id_factura)
);

CREATE TABLE anuncios (
    id_anuncio INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    titulo VARCHAR(100) NOT NULL,
    contenido TEXT NOT NULL,
    fecha_creacion DATETIME NOT NULL,

    CONSTRAINT fk_anuncio_usuario
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);