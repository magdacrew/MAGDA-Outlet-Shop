# 🛍️ MAGDA — Loja de Roupas Online
<img width="500" height="125" alt="logo_white" src="https://github.com/user-attachments/assets/3642326e-a7b3-49e8-bede-868a0f9fbdcb" />

MAGDA é um projeto de e-commerce desenvolvido para uma loja de roupas com foco em preços acessíveis, experiência amigável e acessibilidade para todos os públicos.
A plataforma foi criada com uma interface intuitiva, permitindo que qualquer pessoa navegue facilmente pelo catálogo, visualize produtos e encontre rapidamente o que procura.

✨ Principais características

Layout moderno e responsivo

Navegação simples e intuitiva

Catálogo de roupas com preços acessíveis

Código organizado e fácil de manter

Ideal para estudos, portfólio e expansão futura

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
(@produto_id, 1, 3, 10),  -- PP, Cinza, 10 unidades
(@produto_id, 2, 3, 10),  -- P, Cinza, 10 unidades
(@produto_id, 3, 3, 10),   -- M, Cinza, 10 unidades
(@produto_id, 4, 3, 10),   -- G, Cinza, 10 unidades
(@produto_id, 5, 3, 10);   -- G, Cinza, 10 unidades



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
(@produto_id, 1, 5, 10),  -- PP, Azul, 10 unidades
(@produto_id, 2, 5, 10),  -- P, Azul, 10 unidades
(@produto_id, 3, 5, 10),   -- M, Azul, 10 unidades
(@produto_id, 4, 5, 10);   -- G, Azul, 10 unidades
(@produto_id, 5, 5, 10);   -- GG, Azul, 10 unidades



-- 1) INSERIR PRODUTO
INSERT INTO produtos (nome, descricao, preco, categoria_id, imagem, destaque)
VALUES (
    'Signature Black Jorts',
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
(@produto_id, 2, 4, 10),  -- P, Preto, 10 unidades
(@produto_id, 3, 4, 10),   -- M, Preto, 10 unidades
(@produto_id, 4, 4, 10),   -- G, Preto, 10 unidades
(@produto_id, 5, 4, 10);   -- GG, Preto, 10 unidades 



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
(@produto_id, 1, 4, 10),  -- PP, Vermelho, 10 unidades
(@produto_id, 2, 4, 10),  -- P, Vermelho, 10 unidades
(@produto_id, 3, 4, 10),   -- M, Vermelho, 10 unidades
(@produto_id, 4, 4, 10),   -- G, Vermelho, 10 unidades
(@produto_id, 5, 4, 10);   -- GG, Vermelho, 10 unidades
