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

  // Funções para o carrinho
document.addEventListener('DOMContentLoaded', function() {
    // Atualizar contador do carrinho
    atualizarContadorCarrinho();
    
    // Adicionar ao carrinho via AJAX (opcional)
    document.querySelectorAll('.btn-adicionar-carrinho').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const form = this.closest('form');
            const formData = new FormData(form);
            
            fetch(form.action, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    atualizarContadorCarrinho();
                    mostrarNotificacao('Produto adicionado ao carrinho!');
                }
            })
            .catch(error => {
                console.error('Erro:', error);
            });
        });
    });
});

function atualizarContadorCarrinho() {
    // Implementar contador via AJAX se quiser atualizar em tempo real
    // Por enquanto, apenas mostra se há itens no carrinho
}

function mostrarNotificacao(mensagem) {
    const notificacao = document.createElement('div');
    notificacao.className = 'notificacao';
    notificacao.textContent = mensagem;
    notificacao.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: #000;
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notificacao);
    
    setTimeout(() => {
        notificacao.remove();
    }, 3000);
}