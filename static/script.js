document.addEventListener("DOMContentLoaded", function () {
    const navbar = document.querySelector(".navbar");
  
    // Verifica se está no index
    const isIndex = window.location.pathname === "/" ||
                    window.location.pathname === "" ||
                    window.location.pathname.endsWith("index");
  
    if (!isIndex) {
      // Todas as páginas, exceto index → navbar sempre preta
      navbar.classList.add("scrolled");
    } else {
      // Index → ativa o efeito de scroll
      window.addEventListener("scroll", function () {
        if (window.scrollY > 400) {
          navbar.classList.add("scrolled");
        } else {
          navbar.classList.remove("scrolled");
        }
      });
    }
  
    // Inicializar carrossel se estiver na página inicial
    if (isIndex) {
        initializeCarrossel();
    }
    
    // Inicializar carrinho
    atualizarContador();
    
    // Botão de adicionar na página de visualização (mantém funcionalidade)
    const btnAdicionarDetalhes = document.querySelector('.btn-adicionar-carrinho');
    if (btnAdicionarDetalhes) {
        btnAdicionarDetalhes.addEventListener('click', function() {
            const produtoNome = document.querySelector('.produto-nome')?.textContent;
            const produtoPrecoText = document.querySelector('.produto-preco')?.textContent;
            const produtoPreco = parseFloat(produtoPrecoText?.replace('R$ ', '').replace(',', '.') || 0);
            const produtoImagem = document.querySelector('.produto-imagem-principal')?.src || '/static/images/default.png';
            
            // Obter tamanho e cor selecionados
            const tamanhoSelect = document.getElementById('tamanho');
            const corSelect = document.getElementById('cor');
            const tamanho = tamanhoSelect ? tamanhoSelect.options[tamanhoSelect.selectedIndex]?.text : null;
            const cor = corSelect ? corSelect.options[corSelect.selectedIndex]?.text : null;
            const quantidade = document.getElementById('quantidade')?.value || 1;
            
            // Verificar se tamanho e cor foram selecionados
            if (tamanhoSelect && (!tamanhoSelect.value || tamanhoSelect.value === '')) {
                alert('Por favor, selecione um tamanho');
                return;
            }
            
            if (corSelect && (!corSelect.value || corSelect.value === '')) {
                alert('Por favor, selecione uma cor');
                return;
            }
            
            // Adicionar múltiplas vezes baseado na quantidade
            for (let i = 0; i < quantidade; i++) {
                adicionarAoCarrinho(
                    window.location.pathname.split('/').pop(),
                    produtoNome,
                    produtoPreco,
                    produtoImagem,
                    tamanho,
                    cor
                );
            }
            
            // Abrir carrinho após adicionar
            abrirCarrinho();
        });
    }
    
    // Botão "Comprar agora" na página de detalhes
    const btnComprarAgora = document.querySelector('.btn-comprar-agora');
    if (btnComprarAgora) {
        btnComprarAgora.addEventListener('click', function() {
            const btnAdicionar = document.querySelector('.btn-adicionar-carrinho');
            if (btnAdicionar) btnAdicionar.click();
        });
    }
    
    // Controle de quantidade na página de detalhes
    const diminuirBtn = document.getElementById('diminuir');
    const aumentarBtn = document.getElementById('aumentar');
    const quantidadeInput = document.getElementById('quantidade');
    
    if (diminuirBtn && aumentarBtn && quantidadeInput) {
        diminuirBtn.addEventListener('click', function() {
            let currentValue = parseInt(quantidadeInput.value);
            if (currentValue > 1) {
                quantidadeInput.value = currentValue - 1;
            }
        });
        
        aumentarBtn.addEventListener('click', function() {
            let currentValue = parseInt(quantidadeInput.value);
            if (currentValue < (quantidadeInput.max || 99)) {
                quantidadeInput.value = currentValue + 1;
            }
        });
    }
    
    // Troca de miniaturas (se houver)
    const miniaturas = document.querySelectorAll('.miniatura');
    const imagemPrincipal = document.querySelector('.produto-imagem-principal');
    
    miniaturas.forEach(miniatura => {
        miniatura.addEventListener('click', function() {
            // Remover classe ativa de todas as miniaturas
            miniaturas.forEach(m => m.classList.remove('ativa'));
            
            // Adicionar classe ativa à miniatura clicada
            this.classList.add('ativa');
            
            // Trocar imagem principal (se houver imagens diferentes)
            // Esta funcionalidade precisaria de implementação adicional
            // se você tiver múltiplas imagens para o produto
        });
    });
    
    // Botão "Iniciar compra" no carrinho
    const iniciarCompraBtn = document.getElementById('iniciar-compra');
    if (iniciarCompraBtn) {
        iniciarCompraBtn.addEventListener('click', function() {
            if (carrinho.length > 0) {
                // Aqui você pode redirecionar para a página de checkout
                alert('Redirecionando para a página de checkout...');
                // window.location.href = '/checkout';
            }
        });
    }
    
    // Atribuir IDs de produto aos cards na página de produtos
    document.querySelectorAll('.card').forEach(card => {
        const link = card.querySelector('a[href^="/visualizacao/"]');
        if (link) {
            const produtoId = link.getAttribute('href').split('/').pop();
            card.dataset.produtoId = produtoId;
        }
    });
  });
  
  function togglePassword() {
    const input = document.getElementById("senha");
    const toggle = document.querySelector(".toggle-password");
  
    if (input.type === "password") {
        input.type = "text";
        toggle.classList.add("show");
    } else {
        input.type = "password";
        toggle.classList.remove("show");
    }
  }
  
  // Função do Carrossel de Destaques
  function initializeCarrossel() {
    const track = document.getElementById('carrosselTrack');
    if (!track) return; // Sai se não encontrar o carrossel
    
    const items = document.querySelectorAll('.carrossel-item');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const indicatorsContainer = document.getElementById('carrosselIndicators');
    
    if (items.length === 0) return;
    
    let currentIndex = 0;
    let autoPlayInterval;
    const itemWidth = items[0].offsetWidth + 25; // Largura do item + gap
    const wrapper = document.querySelector('.carrossel-wrapper');
    const visibleItems = Math.floor(wrapper.offsetWidth / itemWidth);
    const totalItems = items.length;
    
    // Criar indicadores
    function createIndicators() {
        if (!indicatorsContainer) return;
        
        indicatorsContainer.innerHTML = '';
        const totalPages = Math.ceil(totalItems / visibleItems);
        
        for (let i = 0; i < totalPages; i++) {
            const indicator = document.createElement('button');
            indicator.className = 'carrossel-indicator';
            indicator.setAttribute('aria-label', `Ir para slide ${i + 1}`);
            if (i === 0) indicator.classList.add('active');
            
            indicator.addEventListener('click', () => {
                goToSlide(i);
            });
            
            indicatorsContainer.appendChild(indicator);
        }
    }
    
    // Atualizar indicadores
    function updateIndicators() {
        const indicators = document.querySelectorAll('.carrossel-indicator');
        const currentPage = Math.floor(currentIndex / visibleItems);
        
        indicators.forEach((indicator, index) => {
            indicator.classList.toggle('active', index === currentPage);
        });
    }
    
    // Ir para slide específico
    function goToSlide(index) {
        currentIndex = index * visibleItems;
        updateCarrossel();
        updateIndicators();
        resetAutoPlay();
    }
    
    // Atualizar posição do carrossel
    function updateCarrossel() {
        track.style.transform = `translateX(-${currentIndex * itemWidth}px)`;
    }
    
    // Próximo slide
    function nextSlide() {
        if (currentIndex >= totalItems - visibleItems) {
            currentIndex = 0; // Volta ao início
        } else {
            currentIndex++;
        }
        
        track.style.transition = 'transform 0.5s ease-in-out';
        updateCarrossel();
        updateIndicators();
    }
    
    // Slide anterior
    function prevSlide() {
        if (currentIndex <= 0) {
            currentIndex = totalItems - visibleItems; // Vai para o final
        } else {
            currentIndex--;
        }
        
        track.style.transition = 'transform 0.5s ease-in-out';
        updateCarrossel();
        updateIndicators();
    }
    
    // Iniciar auto-play
    function startAutoPlay() {
        autoPlayInterval = setInterval(nextSlide, 3000);
    }
    
    // Parar auto-play
    function stopAutoPlay() {
        clearInterval(autoPlayInterval);
    }
    
    // Reiniciar auto-play
    function resetAutoPlay() {
        stopAutoPlay();
        startAutoPlay();
    }
    
    // Event listeners para os botões
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            prevSlide();
            resetAutoPlay();
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            nextSlide();
            resetAutoPlay();
        });
    }
    
    // Pausar auto-play ao interagir
    if (track) {
        track.addEventListener('mouseenter', stopAutoPlay);
        track.addEventListener('mouseleave', startAutoPlay);
        track.addEventListener('touchstart', stopAutoPlay);
        track.addEventListener('touchend', startAutoPlay);
    }
    
    // Pausar auto-play ao focar nos botões
    if (prevBtn) {
        prevBtn.addEventListener('focus', stopAutoPlay);
        prevBtn.addEventListener('blur', startAutoPlay);
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('focus', stopAutoPlay);
        nextBtn.addEventListener('blur', startAutoPlay);
    }
    
    // Inicializar
    createIndicators();
    updateCarrossel();
    startAutoPlay();
    
    // Ajustar carrossel no redimensionamento da tela
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            updateCarrossel();
            createIndicators();
        }, 250);
    });
  
    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowLeft') {
            prevSlide();
            resetAutoPlay();
        } else if (e.key === 'ArrowRight') {
            nextSlide();
            resetAutoPlay();
        }
    });
  }

// ===========================
// CARRINHO DE COMPRAS
// ===========================

let carrinho = JSON.parse(localStorage.getItem('carrinho')) || [];

// Elementos do DOM
const carrinhoBtn = document.getElementById('carrinho-btn');
const carrinhoSidebar = document.getElementById('carrinho-sidebar');
const carrinhoOverlay = document.getElementById('carrinho-overlay');
const fecharCarrinhoBtn = document.getElementById('fechar-carrinho');
const carrinhoItens = document.getElementById('carrinho-itens');
const carrinhoQuantidade = document.getElementById('carrinho-quantidade');
const carrinhoSubtotal = document.getElementById('carrinho-subtotal');
const carrinhoTotal = document.getElementById('carrinho-total');
const carrinhoParcelado = document.getElementById('carrinho-parcelado');
const iniciarCompraBtn = document.getElementById('iniciar-compra');

// Abrir carrinho
if (carrinhoBtn) {
    carrinhoBtn.addEventListener('click', function(e) {
        e.preventDefault();
        abrirCarrinho();
    });
}

// Fechar carrinho
if (fecharCarrinhoBtn) {
    fecharCarrinhoBtn.addEventListener('click', fecharCarrinho);
}

if (carrinhoOverlay) {
    carrinhoOverlay.addEventListener('click', fecharCarrinho);
}

// Funções do carrinho
function abrirCarrinho() {
    carrinhoSidebar.classList.add('active');
    carrinhoOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    atualizarCarrinho();
}

function fecharCarrinho() {
    carrinhoSidebar.classList.remove('active');
    carrinhoOverlay.classList.remove('active');
    document.body.style.overflow = '';
}

// Adicionar produto ao carrinho
function adicionarAoCarrinho(produtoId, produtoNome, produtoPreco, produtoImagem, tamanho = null, cor = null) {
    const produtoExistente = carrinho.find(item => 
        item.id === produtoId && 
        item.tamanho === tamanho && 
        item.cor === cor
    );
    
    if (produtoExistente) {
        produtoExistente.quantidade += 1;
    } else {
        carrinho.push({
            id: produtoId,
            nome: produtoNome,
            preco: parseFloat(produtoPreco),
            imagem: produtoImagem,
            tamanho: tamanho,
            cor: cor,
            quantidade: 1
        });
    }
    
    salvarCarrinho();
    atualizarContador();
    mostrarMensagemSucesso(`${produtoNome} adicionado ao carrinho!`);
    
    // Se o carrinho estiver aberto, atualiza a visualização
    if (carrinhoSidebar.classList.contains('active')) {
        atualizarCarrinho();
    }
}

// Remover produto do carrinho
function removerDoCarrinho(index) {
    carrinho.splice(index, 1);
    salvarCarrinho();
    atualizarContador();
    atualizarCarrinho();
}

// Atualizar quantidade
function atualizarQuantidade(index, novaQuantidade) {
    if (novaQuantidade < 1) {
        removerDoCarrinho(index);
        return;
    }
    
    carrinho[index].quantidade = novaQuantidade;
    salvarCarrinho();
    atualizarContador();
    atualizarCarrinho();
}

// Salvar carrinho no localStorage
function salvarCarrinho() {
    localStorage.setItem('carrinho', JSON.stringify(carrinho));
}

// Atualizar contador na navbar
function atualizarContador() {
    if (carrinhoQuantidade) {
        const totalItens = carrinho.reduce((total, item) => total + item.quantidade, 0);
        carrinhoQuantidade.textContent = totalItens;
        carrinhoQuantidade.style.display = totalItens > 0 ? 'flex' : 'none';
    }
}

// Atualizar visualização do carrinho
function atualizarCarrinho() {
    if (!carrinhoItens) return;
    
    if (carrinho.length === 0) {
        carrinhoItens.innerHTML = `
            <div class="carrinho-vazio">
                <p>Seu carrinho está vazio</p>
            </div>
        `;
        if (iniciarCompraBtn) iniciarCompraBtn.disabled = true;
    } else {
        let html = '';
        let subtotal = 0;
        
        carrinho.forEach((item, index) => {
            const itemTotal = item.preco * item.quantidade;
            subtotal += itemTotal;
            
            // Formatar detalhes do produto
            let detalhes = '';
            if (item.tamanho || item.cor) {
                detalhes = '<div class="carrinho-item-detalhes">';
                if (item.tamanho) detalhes += `<span>Tamanho: ${item.tamanho}</span>`;
                if (item.cor) detalhes += `<span>Cor: ${item.cor}</span>`;
                detalhes += '</div>';
            }
            
            html += `
                <div class="carrinho-item" data-index="${index}">
                    <img src="${item.imagem}" alt="${item.nome}" class="carrinho-item-imagem">
                    <div class="carrinho-item-info">
                        <div class="carrinho-item-nome">${item.nome}</div>
                        ${detalhes}
                        <div class="carrinho-item-preco">R$ ${item.preco.toFixed(2)}</div>
                        <div class="carrinho-item-controles">
                            <div class="quantidade-controle">
                                <button class="quantidade-btn diminuir-quantidade" data-index="${index}">-</button>
                                <input type="number" class="quantidade-input" value="${item.quantidade}" min="1" data-index="${index}">
                                <button class="quantidade-btn aumentar-quantidade" data-index="${index}">+</button>
                            </div>
                            <button class="remover-item" data-index="${index}">Remover</button>
                        </div>
                    </div>
                </div>
            `;
        });
        
        carrinhoItens.innerHTML = html;
        
        // Adicionar eventos aos controles
        document.querySelectorAll('.diminuir-quantidade').forEach(btn => {
            btn.addEventListener('click', function() {
                const index = parseInt(this.dataset.index);
                atualizarQuantidade(index, carrinho[index].quantidade - 1);
            });
        });
        
        document.querySelectorAll('.aumentar-quantidade').forEach(btn => {
            btn.addEventListener('click', function() {
                const index = parseInt(this.dataset.index);
                atualizarQuantidade(index, carrinho[index].quantidade + 1);
            });
        });
        
        document.querySelectorAll('.quantidade-input').forEach(input => {
            input.addEventListener('change', function() {
                const index = parseInt(this.dataset.index);
                const novaQuantidade = parseInt(this.value);
                if (!isNaN(novaQuantidade)) {
                    atualizarQuantidade(index, novaQuantidade);
                }
            });
        });
        
        document.querySelectorAll('.remover-item').forEach(btn => {
            btn.addEventListener('click', function() {
                const index = parseInt(this.dataset.index);
                removerDoCarrinho(index);
            });
        });
        
        if (iniciarCompraBtn) iniciarCompraBtn.disabled = false;
    }
    
    // Atualizar totais
    atualizarTotaisCarrinho();
}

// Atualizar totais do carrinho
function atualizarTotaisCarrinho() {
    const subtotal = carrinho.reduce((total, item) => total + (item.preco * item.quantidade), 0);
    const totalComFrete = subtotal + (freteAtual || 0);
    const parcelado = (totalComFrete * 1.01).toFixed(2);
    
    if (carrinhoSubtotal) {
        carrinhoSubtotal.textContent = `R$ ${subtotal.toFixed(2).replace('.', ',')}`;
    }
    
    if (carrinhoTotal) {
        carrinhoTotal.textContent = `R$ ${totalComFrete.toFixed(2).replace('.', ',')}`;
    }
    
    if (carrinhoParcelado) {
        const span = carrinhoParcelado.querySelector('span');
        if (span) {
            span.textContent = `R$ ${parcelado.replace('.', ',')}`;
        }
    }
}

// Mostrar mensagem de sucesso
function mostrarMensagemSucesso(mensagem) {
    // Remove mensagem anterior se existir
    const mensagemAnterior = document.querySelector('.carrinho-mensagem');
    if (mensagemAnterior) mensagemAnterior.remove();
    
    // Cria nova mensagem
    const mensagemDiv = document.createElement('div');
    mensagemDiv.className = 'carrinho-mensagem';
    mensagemDiv.textContent = mensagem;
    document.body.appendChild(mensagemDiv);
    
    // Mostra a mensagem
    setTimeout(() => {
        mensagemDiv.style.display = 'block';
    }, 10);
    
    // Remove após 3 segundos
    setTimeout(() => {
        mensagemDiv.style.opacity = '0';
        mensagemDiv.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (mensagemDiv.parentNode) {
                mensagemDiv.parentNode.removeChild(mensagemDiv);
            }
        }, 300);
    }, 3000);
}

// Fechar carrinho com a tecla ESC
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        if (carrinhoSidebar && carrinhoSidebar.classList.contains('active')) {
            fecharCarrinho();
        }
        if (modalProduto && modalProduto.classList.contains('active')) {
            fecharModalProduto();
        }
    }
});

// ===========================
// MODAL DE PRODUTO
// ===========================

let produtoAtual = null;
let estoqueDisponivel = [];

// Elementos do modal
const modalProduto = document.getElementById('modal-produto');
const modalFechar = document.querySelector('.modal-fechar');
const modalImagem = document.getElementById('modal-imagem');
const modalNome = document.getElementById('modal-nome');
const modalPreco = document.getElementById('modal-preco');
const modalParcelado = document.getElementById('modal-parcelado');
const modalTamanhos = document.getElementById('modal-tamanhos');
const modalCores = document.getElementById('modal-cores');
const modalQuantidade = document.getElementById('modal-quantidade');
const modalDiminuir = document.getElementById('modal-diminuir');
const modalAumentar = document.getElementById('modal-aumentar');
const modalAdicionar = document.getElementById('modal-adicionar');
const modalComprar = document.getElementById('modal-comprar');

// Abrir modal do produto
function abrirModalProduto(produtoId) {
    // Buscar informações do produto
    const card = document.querySelector(`.card[data-produto-id="${produtoId}"]`);
    if (!card) {
        // Tenta buscar pelo ID direto
        const cards = document.querySelectorAll('.card');
        for (let card of cards) {
            const link = card.querySelector('a[href^="/visualizacao/"]');
            if (link) {
                const id = link.getAttribute('href').split('/').pop();
                if (id == produtoId) {
                    card.dataset.produtoId = produtoId;
                    break;
                }
            }
        }
    }
    
    if (!card) return;
    
    const produtoNome = card.querySelector('.produto-nome').textContent;
    const produtoPrecoText = card.querySelector('.produto-preco').textContent;
    const produtoPreco = parseFloat(produtoPrecoText.replace('R$ ', '').replace(',', '.'));
    const produtoImagem = card.querySelector('.produto-imagem')?.src || '/static/images/default.png';
    
    // Preencher informações básicas
    produtoAtual = {
        id: produtoId,
        nome: produtoNome,
        preco: produtoPreco,
        imagem: produtoImagem
    };
    
    modalImagem.src = produtoImagem;
    modalNome.textContent = produtoNome;
    modalPreco.textContent = `R$ ${produtoPreco.toFixed(2)}`;
    
    // Calcular parcelado (5% de desconto no PIX)
    const precoPix = produtoPreco * 0.95;
    modalParcelado.innerHTML = `R$ ${precoPix.toFixed(2)} <small>pagando com PIX</small>`;
    
    // Buscar estoque via API
    buscarEstoqueProduto(produtoId);
    
    // Mostrar modal
    modalProduto.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    // Resetar seleções
    modalQuantidade.value = 1;
}

// Buscar estoque do produto
async function buscarEstoqueProduto(produtoId) {
    try {
        const response = await fetch(`/api/produto/${produtoId}/estoque`);
        const data = await response.json();
        
        if (data.success) {
            estoqueDisponivel = data.estoque;
            renderizarOpcoesDisponiveis();
        } else {
            alert('Erro ao carregar opções do produto');
        }
    } catch (error) {
        console.error('Erro ao buscar estoque:', error);
        // Fallback: permitir adicionar sem selecionar tamanho/cor
        estoqueDisponivel = [];
        renderizarOpcoesDisponiveis();
    }
}

// Renderizar tamanhos e cores disponíveis
function renderizarOpcoesDisponiveis() {
    // Resetar
    modalTamanhos.innerHTML = '';
    modalCores.innerHTML = '';
    
    // Agrupar estoque por tamanho e cor
    const tamanhosDisponiveis = [];
    const coresDisponiveis = [];
    
    estoqueDisponivel.forEach(item => {
        if (!tamanhosDisponiveis.find(t => t.id === item.tamanho_id)) {
            tamanhosDisponiveis.push({
                id: item.tamanho_id,
                nome: item.tamanho_nome,
                quantidade: 0
            });
        }
        
        if (!coresDisponiveis.find(c => c.id === item.cor_id)) {
            coresDisponiveis.push({
                id: item.cor_id,
                nome: item.cor_nome,
                quantidade: 0
            });
        }
    });
    
    // Renderizar tamanhos
    tamanhosDisponiveis.forEach(tamanho => {
        const totalEmEstoque = estoqueDisponivel
            .filter(item => item.tamanho_id === tamanho.id)
            .reduce((total, item) => total + item.quantidade, 0);
        
        const button = document.createElement('button');
        button.className = 'modal-tamanho-btn';
        if (totalEmEstoque === 0) button.classList.add('disabled');
        button.textContent = tamanho.nome;
        button.dataset.tamanhoId = tamanho.id;
        button.dataset.tamanhoNome = tamanho.nome;
        
        button.addEventListener('click', function() {
            if (this.classList.contains('disabled')) return;
            
            // Remover seleção anterior
            document.querySelectorAll('.modal-tamanho-btn').forEach(btn => {
                btn.classList.remove('selected');
            });
            
            // Selecionar este tamanho
            this.classList.add('selected');
            
            // Atualizar cores disponíveis para este tamanho
            filtrarCoresPorTamanho(tamanho.id);
        });
        
        modalTamanhos.appendChild(button);
    });
    
    // Renderizar cores
    coresDisponiveis.forEach(cor => {
        const button = document.createElement('button');
        button.className = 'modal-cor-btn';
        button.dataset.corId = cor.id;
        button.dataset.corNome = cor.nome;
        button.title = cor.nome;
        
        // Adicionar cor de fundo baseada no nome da cor
        const corMap = {
            'Preto': '#000000',
            'Branco': '#ffffff',
            'Cinza': '#808080',
            'Vermelho': '#ff0000',
            'Azul': '#0000ff',
            'Verde': '#008000',
            'Amarelo': '#ffff00',
            'Rosa': '#ffc0cb',
            'Roxo': '#800080',
            'Bege': '#f5f5dc',
            'Marrom': '#a52a2a',
            'Laranja': '#ffa500'
        };
        
        button.style.backgroundColor = corMap[cor.nome] || '#ccc';
        button.style.border = cor.nome === 'Branco' ? '2px solid #ddd' : '2px solid transparent';
        
        button.addEventListener('click', function() {
            if (this.classList.contains('disabled')) return;
            
            // Remover seleção anterior
            document.querySelectorAll('.modal-cor-btn').forEach(btn => {
                btn.classList.remove('selected');
            });
            
            // Selecionar esta cor
            this.classList.add('selected');
        });
        
        modalCores.appendChild(button);
    });
    
    // Selecionar primeiro tamanho disponível
    const primeiroTamanho = modalTamanhos.querySelector('.modal-tamanho-btn:not(.disabled)');
    if (primeiroTamanho) {
        primeiroTamanho.click();
    }
}

// Filtrar cores por tamanho selecionado
function filtrarCoresPorTamanho(tamanhoId) {
    const coresParaTamanho = estoqueDisponivel
        .filter(item => item.tamanho_id === tamanhoId && item.quantidade > 0)
        .map(item => item.cor_id);
    
    document.querySelectorAll('.modal-cor-btn').forEach(btn => {
        const corId = parseInt(btn.dataset.corId);
        const temEstoque = coresParaTamanho.includes(corId);
        
        if (temEstoque) {
            btn.classList.remove('disabled');
        } else {
            btn.classList.add('disabled');
            btn.classList.remove('selected');
        }
    });
    
    // Selecionar primeira cor disponível
    const primeiraCor = modalCores.querySelector('.modal-cor-btn:not(.disabled)');
    if (primeiraCor) {
        primeiraCor.click();
    }
}

// Fechar modal
function fecharModalProduto() {
    modalProduto.classList.remove('active');
    document.body.style.overflow = '';
    produtoAtual = null;
    estoqueDisponivel = [];
}

// Controles de quantidade no modal
if (modalDiminuir && modalAumentar) {
    modalDiminuir.addEventListener('click', function() {
        let valor = parseInt(modalQuantidade.value);
        if (valor > 1) {
            modalQuantidade.value = valor - 1;
        }
    });
    
    modalAumentar.addEventListener('click', function() {
        let valor = parseInt(modalQuantidade.value);
        modalQuantidade.value = valor + 1;
    });
    
    modalQuantidade.addEventListener('change', function() {
        let valor = parseInt(this.value);
        if (isNaN(valor) || valor < 1) {
            this.value = 1;
        }
    });
}

// Adicionar ao carrinho do modal
if (modalAdicionar) {
    modalAdicionar.addEventListener('click', function() {
        if (!produtoAtual) return;
        
        // Verificar seleções
        const tamanhoSelecionado = modalTamanhos.querySelector('.modal-tamanho-btn.selected');
        const corSelecionada = modalCores.querySelector('.modal-cor-btn.selected');
        
        if (!tamanhoSelecionado || tamanhoSelecionado.classList.contains('disabled')) {
            alert('Por favor, selecione um tamanho disponível');
            return;
        }
        
        if (!corSelecionada || corSelecionada.classList.contains('disabled')) {
            alert('Por favor, selecione uma cor disponível');
            return;
        }
        
        const tamanho = tamanhoSelecionado.dataset.tamanhoNome;
        const cor = corSelecionada.dataset.corNome;
        const quantidade = parseInt(modalQuantidade.value);
        
        // Verificar estoque disponível
        const estoqueParaCombinacao = estoqueDisponivel.find(item => 
            item.tamanho_nome === tamanho && 
            item.cor_nome === cor
        );
        
        if (!estoqueParaCombinacao || estoqueParaCombinacao.quantidade < quantidade) {
            alert(`Estoque insuficiente. Disponível: ${estoqueParaCombinacao?.quantidade || 0} unidades`);
            return;
        }
        
        // Adicionar ao carrinho
        for (let i = 0; i < quantidade; i++) {
            adicionarAoCarrinho(
                produtoAtual.id,
                produtoAtual.nome,
                produtoAtual.preco,
                produtoAtual.imagem,
                tamanho,
                cor
            );
        }
        
        // Fechar modal e abrir carrinho
        fecharModalProduto();
        abrirCarrinho();
    });
}

// Comprar agora do modal
if (modalComprar) {
    modalComprar.addEventListener('click', function() {
        modalAdicionar.click(); // Adiciona ao carrinho primeiro
    });
}

// Fechar modal
if (modalFechar) {
    modalFechar.addEventListener('click', fecharModalProduto);
}

// Fechar modal ao clicar fora
if (modalProduto) {
    modalProduto.addEventListener('click', function(e) {
        if (e.target === this) {
            fecharModalProduto();
        }
    });
}

// ===========================
// CÁLCULO DE FRETE
// ===========================

const cepFrete = document.getElementById('cep-frete');
const btnCalcularFrete = document.getElementById('calcular-frete');
const freteResultados = document.getElementById('frete-resultados');
const freteSelecionado = document.getElementById('frete-selecionado');
const freteTipo = document.getElementById('frete-tipo');
const freteValor = document.getElementById('frete-valor');

let freteAtual = 0;

// Formatar CEP
if (cepFrete) {
    cepFrete.addEventListener('input', function(e) {
        let value = e.target.value.replace(/\D/g, '');
        if (value.length > 5) {
            value = value.replace(/^(\d{5})(\d)/, '$1-$2');
        }
        e.target.value = value;
    });
}

// Calcular frete
if (btnCalcularFrete) {
    btnCalcularFrete.addEventListener('click', function() {
        const cep = cepFrete.value.replace(/\D/g, '');
        
        if (cep.length !== 8) {
            alert('Digite um CEP válido (8 dígitos)');
            return;
        }
        
        if (carrinho.length === 0) {
            alert('Adicione produtos ao carrinho para calcular o frete');
            return;
        }
        
        calcularFrete(cep);
    });
}

async function calcularFrete(cep) {
    // Simulação de cálculo de frete
    // Em produção, você integraria com uma API de fretes
    
    const opcoesFrete = [
        {
            nome: 'Entrega Padrão',
            prazo: '5-8 dias úteis',
            valor: 15.90
        },
        {
            nome: 'Entrega Expressa',
            prazo: '2-3 dias úteis',
            valor: 29.90
        },
        {
            nome: 'Entrega Agendada',
            prazo: 'Escolha a data',
            valor: 24.90
        }
    ];
    
    // Calcular valor baseado no subtotal
    const subtotal = carrinho.reduce((total, item) => total + (item.preco * item.quantidade), 0);
    
    if (subtotal > 599.90) {
        opcoesFrete.unshift({
            nome: 'Frete Grátis',
            prazo: '5-10 dias úteis',
            valor: 0
        });
    }
    
    // Renderizar opções
    freteResultados.innerHTML = '';
    
    opcoesFrete.forEach((opcao, index) => {
        const div = document.createElement('div');
        div.className = 'frete-opcao';
        div.dataset.index = index;
        
        div.innerHTML = `
            <div class="frete-opcao-info">
                <div class="frete-opcao-nome">${opcao.nome}</div>
                <div class="frete-opcao-prazo">${opcao.prazo}</div>
            </div>
            <div class="frete-opcao-valor">
                ${opcao.valor === 0 ? 'Grátis' : `R$ ${opcao.valor.toFixed(2)}`}
            </div>
        `;
        
        div.addEventListener('click', function() {
            // Remover seleção anterior
            document.querySelectorAll('.frete-opcao').forEach(el => {
                el.classList.remove('selected');
            });
            
            // Selecionar esta opção
            this.classList.add('selected');
            
            // Atualizar frete
            freteAtual = opcao.valor;
            freteTipo.textContent = opcao.nome;
            freteValor.textContent = opcao.valor === 0 ? 'Grátis' : `R$ ${opcao.valor.toFixed(2)}`;
            
            // Mostrar seleção
            if (freteSelecionado) freteSelecionado.style.display = 'flex';
            
            // Atualizar totais
            atualizarTotaisCarrinho();
        });
        
        freteResultados.appendChild(div);
    });
    
    if (freteResultados) freteResultados.classList.add('active');
}

function atualizarCalculoFrete() {
    if (freteAtual > 0 && cepFrete && cepFrete.value) {
        atualizarTotaisCarrinho();
    }
}
