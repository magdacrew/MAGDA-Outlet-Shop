CREATE TABLE categorias (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL
);

INSERT INTO categorias(nome) VALUES 
 ('Camisetas'),
 ('Casacos'),
 ('Calças'),
 ('Bermudas'),
 ('Acessórios');

CREATE TABLE cores(
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(50) NOT NULL
);

INSERT INTO cores(nome) VALUES 
('Preto'),
('Branco'),
('Cinza'),
('Vermelho'),
('Azul'),
('Verde'),
('Amarelo'),
('Rosa'),
('Roxo'),
('Bege'),
('Marrom'),
('Laranja');

CREATE TABLE tamanhos(
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(10) NOT NULL
);
INSERT INTO tamanhos(nome) VALUES
('PP'),
('P'),
('M'),
('G'),
('GG'),
('XGG'); 

CREATE TABLE usuarios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome_completo VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    telefone VARCHAR(20),
    cpf VARCHAR(14) UNIQUE,
    nascimento DATE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    data_cadastro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    ativo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE produtos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    descricao TEXT,
    preco DECIMAL(10, 2) NOT NULL,
    categoria_id INT,
    imagem VARCHAR(255),
    destaque BOOLEAN NOT NULL DEFAULT FALSE,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id)
    
);

CREATE TABLE estoque(
    id INT PRIMARY KEY AUTO_INCREMENT,
    produto_id INT NOT NULL,
    tamanho_id INT NOT NULL,
    cor_id INT NOT NULL,
    quantidade INT NOT NULL DEFAULT 0,
    FOREIGN KEY (tamanho_id) REFERENCES tamanhos(id),
    FOREIGN KEY (cor_id) REFERENCES cores(id),
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);


CREATE TABLE vendas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT NOT NULL,
    valor_total DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    valor_frete DECIMAL(10,2) NOT NULL,
    forma_pagamento VARCHAR(50) DEFAULT 'simulacao',
    frete_tipo VARCHAR(50),
    cpf_cnpj_nota VARCHAR(20),
    status VARCHAR(50) DEFAULT 'confirmado',
    data_venda DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE enderecos_venda (
    id INT PRIMARY KEY AUTO_INCREMENT,
    venda_id INT NOT NULL,
    cep VARCHAR(10),
    logradouro VARCHAR(255),
    numero VARCHAR(20),
    complemento VARCHAR(255),
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    estado VARCHAR(2),
    destinatario VARCHAR(255),
    FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE CASCADE
);


CREATE TABLE itens_venda (
    id INT PRIMARY KEY AUTO_INCREMENT,
    venda_id INT NOT NULL,
    produto_id INT,
    quantidade INT NOT NULL,
    preco_unitario DECIMAL(10,2) NOT NULL,
    tamanho VARCHAR(50),
    cor VARCHAR(50),
    FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);


CREATE TABLE carrinho (
    id INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT NOT NULL,
    produto_id INT NOT NULL,
    quantidade INT DEFAULT 1,
    tamanho_id INT,
    cor_id INT,
    data_adicao DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (produto_id) REFERENCES produtos(id),
    FOREIGN KEY (tamanho_id) REFERENCES tamanhos(id),
    FOREIGN KEY (cor_id) REFERENCES cores(id)
);



-- 1) INSERIR PRODUTO
INSERT INTO produtos (nome, descricao, preco, categoria_id, imagem, destaque)
VALUES (
    'Calça Jeans STONER',
    'A Calça Jeans STONER combina conforto e estilo com sua modelagem ampla e lavagem cinza estonada. Feita em jeans 100% algodão, possui zíper YKK, costura reforçada e detalhes personalizados que garantem durabilidade e um visual street autêntico. Ideal para quem busca um caimento solto e cheio de personalidade.',
    359.90,          -- preço
    3,             -- categoria_id 
    'Calça_Jeans_STONER.webp',  -- nome do arquivo
    TRUE          -- destaque (TRUE/FALSE)
);

-- 2) PEGAR ID DO PRODUTO
SET @produto_id = LAST_INSERT_ID();

-- 3) INSERIR ESTOQUE (repita quantas variações quiser)
INSERT INTO estoque (produto_id, tamanho_id, cor_id, quantidade)
VALUES
(@produto_id, 1, 1, 10),  -- PP, Preto, 10 unidades
(@produto_id, 2, 1, 10),  -- P, Preto, 15 unidades
(@produto_id, 3, 1, 10);   -- M, Cinza, 8 unidades
(@produto_id, 4, 1, 10);   -- G,
(@produto_id, 5, 1, 10);   -- G,



-- 1) INSERIR PRODUTO
INSERT INTO produtos (nome, descricao, preco, categoria_id, imagem, destaque)
VALUES (
    'Storm Grey Baggy Jeans',
    'A Calça Jeans STONER combina conforto e estilo com sua modelagem ampla e lavagem cinza estonada. Feita em jeans 100% algodão, possui zíper YKK, costura reforçada e detalhes personalizados que garantem durabilidade e um visual street autêntico. Ideal para quem busca um caimento solto e cheio de personalidade.',
    329.90,          -- preço
    3,             -- categoria_id 
    'Storm_Grey_Baggy_Jeans.webp',  -- nome do arquivo
    TRUE          -- destaque (TRUE/FALSE)
);

-- 2) PEGAR ID DO PRODUTO
SET @produto_id = LAST_INSERT_ID();

-- 3) INSERIR ESTOQUE (repita quantas variações quiser)
INSERT INTO estoque (produto_id, tamanho_id, cor_id, quantidade)
VALUES
(@produto_id, 1, 3, 10),  -- PP, Preto, 10 unidades
(@produto_id, 2, 3, 10),  -- P, Preto, 15 unidades
(@produto_id, 3, 3, 10);   -- M, Cinza, 8 unidades
(@produto_id, 4, 3, 10);   -- G,
(@produto_id, 5, 3, 10);   -- G,



-- 1) INSERIR PRODUTO
INSERT INTO produtos (nome, descricao, preco, categoria_id, imagem, destaque)
VALUES (
    'Prime Baggy Jeans',
    'A Prime Baggy Jeans azul claro combina um visual moderno com conforto absoluto. Com seu caimento solto e lavagem suave, ela entrega estilo urbano e versatilidade para qualquer ocasião, garantindo um look despojado e cheio de personalidade.',
    349.90,          -- preço
    3,             -- categoria_id 
    'Prime_Baggy_Jeans.webp',  -- nome do arquivo
    TRUE          -- destaque (TRUE/FALSE)
);

-- 2) PEGAR ID DO PRODUTO
SET @produto_id = LAST_INSERT_ID();

-- 3) INSERIR ESTOQUE (repita quantas variações quiser)
INSERT INTO estoque (produto_id, tamanho_id, cor_id, quantidade)
VALUES
(@produto_id, 1, 5, 10),  -- PP, Preto, 10 unidades
(@produto_id, 2, 5, 10),  -- P, Preto, 15 unidades
(@produto_id, 3, 5, 10);   -- M, Cinza, 8 unidades
(@produto_id, 4, 5, 10);   -- G,
(@produto_id, 5, 5, 10);   -- G,



-- 1) INSERIR PRODUTO
INSERT INTO produtos (nome, descricao, preco, categoria_id, imagem, destaque)
VALUES (
    'Signature Black Jorts',A 
    'O Signature Black Jorts é uma bermuda confeccionada em jeans de alta durabilidade. A peça tem arte em laser na parte traseira que traz uma estética única pra peça. Com modelagem ampla e exclusiva, proporciona além de conforto, um caimento fluído ao corpo.',
    249.90,          -- preço
    4,             -- categoria_id 
    'Signature_Black_Jorts.webp',  -- nome do arquivo
    FALSE          -- destaque (TRUE/FALSE)
);

-- 2) PEGAR ID DO PRODUTO
SET @produto_id = LAST_INSERT_ID();

-- 3) INSERIR ESTOQUE (repita quantas variações quiser)
INSERT INTO estoque (produto_id, tamanho_id, cor_id, quantidade)
VALUES
(@produto_id, 1, 4, 10),  -- PP, Preto, 10 unidades
(@produto_id, 2, 4, 10),  -- P, Preto, 15 unidades
(@produto_id, 3, 4, 10);   -- M, Cinza, 8 unidades
(@produto_id, 4, 4, 10);   -- G,
(@produto_id, 5, 4, 10);   -- G,



-- 1) INSERIR PRODUTO
INSERT INTO produtos (nome, descricao, preco, categoria_id, imagem, destaque)
VALUES (
    'Memories 2.0 Boxy Tee',A 
    'A Memories 2.0® Boxy Tee Vermelha traz o caimento amplo perfeito, tecido macio e visual minimalista que destaca qualquer look. Uma peça versátil, confortável e com aquele toque street na medida certa.',
    189.90,          -- preço
    1 ,             -- categoria_id 
    'Memories_2.0_Boxy_Tee.webp',  -- nome do arquivo
    FALSE          -- destaque (TRUE/FALSE)
);

-- 2) PEGAR ID DO PRODUTO
SET @produto_id = LAST_INSERT_ID();

-- 3) INSERIR ESTOQUE (repita quantas variações quiser)
INSERT INTO estoque (produto_id, tamanho_id, cor_id, quantidade)
VALUES
(@produto_id, 1, 4, 10),  -- PP, Preto, 10 unidades
(@produto_id, 2, 4, 10),  -- P, Preto, 15 unidades
(@produto_id, 3, 4, 10);   -- M, Cinza, 8 unidades
(@produto_id, 4, 4, 10);   -- G,
(@produto_id, 5, 4, 10);   -- G,