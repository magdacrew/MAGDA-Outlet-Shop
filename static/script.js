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
  });
