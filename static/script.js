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
  
  // Adicionar funcionalidade aos botões de compra
  document.addEventListener('click', function(e) {
    if (e.target.classList.contains('btn-comprar')) {
        const card = e.target.closest('.card');
        const productName = card.querySelector('.produto-nome').textContent;
        const productPrice = card.querySelector('.produto-preco').textContent;
        
        // Aqui você pode adicionar a lógica para adicionar ao carrinho
        console.log(`Produto adicionado ao carrinho: ${productName} - ${productPrice}`);
        
        // Feedback visual
        const originalText = e.target.textContent;
        e.target.textContent = '✓ ADICIONADO';
        e.target.style.background = '#28a745';
        
        setTimeout(() => {
            e.target.textContent = originalText;
            e.target.style.background = '';
        }, 2000);
    }
  });

// Funcionalidades da página de detalhes do produto
document.addEventListener('DOMContentLoaded', function() {
    // Controle de quantidade
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
            if (currentValue < 10) { // Limite máximo de 10
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
    
    // Adicionar ao carrinho
    const btnAdicionarCarrinho = document.querySelector('.btn-adicionar-carrinho');
    if (btnAdicionarCarrinho) {
        btnAdicionarCarrinho.addEventListener('click', function() {
            const produtoId = window.location.pathname.split('/').pop();
            const tamanho = document.getElementById('tamanho').value;
            const cor = document.getElementById('cor').value;
            const quantidade = document.getElementById('quantidade').value;
            
            // Aqui você implementaria a lógica para adicionar ao carrinho
            alert(`Produto adicionado ao carrinho!\nTamanho: ${tamanho}\nCor: ${cor}\nQuantidade: ${quantidade}`);
        });
    }
});