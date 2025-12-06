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
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    data_cadastro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ativo BOOLEAN NOT NULL DEFAULT TRUE;
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

CREATE TABLE vendas(
    id INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT,
    data_venda DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valor_total DECIMAL(10,2) NOT NULL,
    forma_pagamento ENUM('PIX','Cartão Débito','Cartão Crédito','Boleto') NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE itens_venda (
    id INT PRIMARY KEY AUTO_INCREMENT,
    venda_id INT NOT NULL,
    produto_id INT NOT NULL,
    tamanho_id INT NOT NULL,
    cor_id INT NOT NULL,
    quantidade INT NOT NULL,
    preco_unitario DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (venda_id) REFERENCES vendas(id),
    FOREIGN KEY (produto_id) REFERENCES produtos(id),
    FOREIGN KEY (tamanho_id) REFERENCES tamanhos(id),
    FOREIGN KEY (cor_id) REFERENCES cores(id)
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

/*
Exemplo de inserção de produtos no estoque:
*/
INSERT INTO estoque(produto_id, tamanho_id, cor_id, quantidade) VALUES
(1, 1, 1, 50), -- P Preto 50 un
(1, 2, 1, 30), -- M Preto 30 un
(2, 3, 2, 20), -- G Branco 20 un

/*
Exemplo de inserção de produtos:
*/

INSERT INTO produtos(nome, descricao, preco, categoria_id,imagem) VALUES
('Camiseta Básica', 'Camiseta de algodão básica disponível em várias cores e tamanhos.', 29.90, 1,'static/uploads/MAGDAtee.png'),
('Casaco Jeans', 'Casaco jeans estiloso para todas as ocasiões.', 99.90, 2),
('Calça Chino', 'Calça chino confortável e elegante.', 79.90, 3),
('Bermuda Casual', 'Bermuda casual perfeita para o verão.', 49.90, 4),
('Boné Esportivo', 'Boné esportivo com design moderno.', 19.90, 5);

/*
Exemplo de insertação de venda COMPLETA
*/
--1. Inserindo venda:
INSERT INTO itens_venda (venda_id, produto_id, tamanho_id, cor_id, quantidade, preco_unitario)
VALUES 
(1, 1, 2, 1, 2, 79.90),   -- 2 camisetas M preta
(1, 2, 3, 2, 1, 159.90);  -- 1 moletom G branco

--2. Inserindo itens da venda:
INSERT INTO vendas (cliente_id, valor_total, forma_pagamento)
VALUES 
(1, 259.90, 'PIX')

/*
Exemplo de Cadastro de clientes:
*/
INSERT INTO clientes(nome,email,telefone,cpf,data_nascimento)
VALUES 
('Adrian Holz','holzadrian8@gmail.com','(47) 99784-5924','148.060.359-71','2008-06-06')