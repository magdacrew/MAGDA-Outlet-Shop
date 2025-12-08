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