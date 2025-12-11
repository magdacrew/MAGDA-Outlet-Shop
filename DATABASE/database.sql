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

-- Inserção de calças na tabela produtos
INSERT INTO produtos (nome, descricao, preco, categoria_id, imagem, destaque) VALUES
('Calça Jeans STONER', 
'A Calça Jeans STONER combina conforto e estilo com sua modelagem ampla e lavagem cinza estonada. Feita em jeans 100% algodão, possui zíper YKK, costura reforçada e detalhes personalizados que garantem durabilidade e um visual street autêntico. Ideal para quem busca um caimento solto e cheio de personalidade.', 
359.90, 
(SELECT id FROM categorias WHERE nome = 'Calcas'), 
'Calça_Jeans_STONER.webp', 
TRUE), 

('Storm Grey Baggy Jeans', 
'A Storm Grey Baggy Jeans combina conforto e estilo com sua modelagem ampla e lavagem cinza estonada. Feita em jeans 100% algodão, possui zíper YKK, costura reforçada e detalhes personalizados que garantem durabilidade e um visual street autêntico. Ideal para quem busca um caimento solto e cheio de personalidade.', 
329.90, 
(SELECT id FROM categorias WHERE nome = 'Calcas'), 
'Storm_Grey_Baggy_Jeans.webp', 
TRUE),

('Prime Baggy Jeans', 
'A Prime Baggy Jeans azul claro combina um visual moderno com conforto absoluto. Com seu caimento solto e lavagem suave, ela entrega estilo urbano e versatilidade para qualquer ocasião, garantindo um look despojado e cheio de personalidade.', 
339.90, 
(SELECT id FROM categorias WHERE nome = 'Calcas'), 
'Prime_Baggy_Jeans.webp', 
TRUE),

('Stone Black ECO', 
'A Stone Black ECO traz um jeans preto estonado com visual moderno e sustentável, caimento confortável e estilo versátil para qualquer combinação.', 
279.90, 
(SELECT id FROM categorias WHERE nome = 'Calcas'), 
'Stone_Black_ECO.webp', 
TRUE),

('Black Baggy Jeans', 
'A Black Baggy Jeans oferece caimento amplo, conforto de sobra e o visual preto clássico que combina com tudo, trazendo estilo urbano na medida certa.', 
389.90, 
(SELECT id FROM categorias WHERE nome = 'Calcas'), 
'Black_Baggy_Jeans.webp', 
TRUE),

-- Inserção de camisas na tabela produtos

('Horse Index Heavy Tee', 
'A Horse Index Heavy Tee é confeccionada em Suedine preto, um tecido nobre, de textura aveludada e toque macio, com experiência de uso confortável e caimento estruturado.', 
189.90, 
(SELECT id FROM categorias WHERE nome = 'Camisetas'), 
'Horse_Index_Heavy_Tee.webp', 
TRUE),

('Memories 2.0® Boxy Tee', 
'A Memories 2.0® Boxy Tee Vermelha traz o caimento amplo perfeito, tecido macio e visual minimalista que destaca qualquer look. Uma peça versátil, confortável e com aquele toque street na medida certa.', 
179.90, 
(SELECT id FROM categorias WHERE nome = 'Camisetas'), 
'Memories_2.0_Boxy_Tee.webp', 
TRUE),

('Camiseta Class Pipa Preto', 
'A Camiseta Class Pipa Preto une estilo minimalista e conforto, trazendo o clássico logo Pipa em destaque sobre o tecido preto. Versátil e moderna, é perfeita para compor looks casuais com personalidade.', 
209.90, 
(SELECT id FROM categorias WHERE nome = 'Camisetas'), 
'Camiseta_Class_Pipa_Preto.webp', 
TRUE),

('Camiseta ASHWALKER', 
'A Camiseta ASHWALKER une estética urbana e atitude obscura, com caimento confortável e visual marcante que eleva qualquer composição streetwear.', 
219.90, 
(SELECT id FROM categorias WHERE nome = 'Camisetas'), 
'Camiseta_ASHWALKER.webp', 
TRUE),