from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
from functools import wraps
import mysql.connector
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
from functools import wraps


app = Flask(__name__)
app.secret_key = 'MAGDA_GAE'

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Configurações de sessão
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
app.config['SESSION_COOKIE_SECURE'] = False  # True em produção com HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True

def conectar():
    return mysql.connector.connect(host='localhost', user='root', port='3406', database='crew_magda')

# ==================== DECORATORS DE AUTENTICAÇÃO ====================


def verificar_conta_ativa():
    """Função auxiliar para verificar se a conta do usuário está ativa"""
    if 'usuario_id' not in session:
        return True  # Se não está logado, não precisa verificar
        
    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("""
            SELECT ativo, nome_completo 
            FROM usuarios 
            WHERE id = %s
        """, (session['usuario_id'],))
        usuario = cursor.fetchone()
        cursor.close()
        conexao.close()
        
        # Se usuário não existe ou está desativado
        if not usuario or not usuario.get('ativo', True):
            return False, usuario.get('nome_completo', 'Usuário') if usuario else 'Usuário'
        
        return True, usuario.get('nome_completo', 'Usuário')
        
    except Exception as e:
        print(f"Erro ao verificar conta ativa: {e}")
        # Em caso de erro, assume que está ativo para não bloquear o usuário
        return True, 'Usuário'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash("Você precisa fazer login para acessar esta página", "error")
            return redirect('/login')
        
        # VERIFICAÇÃO DE CONTA ATIVA - NOVO
        conta_ativa, nome_usuario = verificar_conta_ativa()
        if not conta_ativa:
            session.clear()
            flash(f"Sua conta ({nome_usuario}) foi desativada. Entre em contato com o administrador.", "error")
            return redirect('/login')
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash("Você precisa fazer login para acessar esta página", "error")
            return redirect('/login')
        
        # VERIFICAÇÃO DE CONTA ATIVA - NOVO
        conta_ativa, nome_usuario = verificar_conta_ativa()
        if not conta_ativa:
            session.clear()
            flash(f"Sua conta ({nome_usuario}) foi desativada. Entre em contato com o administrador.", "error")
            return redirect('/login')
        
        # Verificar se é admin
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("""
            SELECT is_admin, nome_completo 
            FROM usuarios 
            WHERE id = %s
        """, (session['usuario_id'],))
        usuario = cursor.fetchone()
        cursor.close()
        conexao.close()
        
        if not usuario or not usuario.get('is_admin'):
            flash("Acesso restrito. Permissões insuficientes.", "error")
            return redirect('/')
        
        return f(*args, **kwargs)
    return decorated_function

def verificar_permissao_admin():
    """Verifica se o usuário atual é admin"""
    if 'usuario_id' not in session:
        return False
    
    # VERIFICAÇÃO DE CONTA ATIVA - NOVO
    conta_ativa, _ = verificar_conta_ativa()
    if not conta_ativa:
        session.clear()
        return False
    
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("""
        SELECT is_admin, ativo 
        FROM usuarios 
        WHERE id = %s
    """, (session['usuario_id'],))
    usuario = cursor.fetchone()
    cursor.close()
    conexao.close()
    
    # Verifica se usuário existe, está ativo e é admin
    return usuario and usuario.get('ativo', True) and usuario.get('is_admin')

# ==================== ROTAS PÚBLICAS ====================

@app.route("/")
def home():
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)

    sql = """
        SELECT p.id, p.nome, p.preco, p.imagem
        FROM produtos p
        WHERE p.destaque = TRUE AND p.ativo = TRUE
    """
    cursor.execute(sql)
    produtos_destaque = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template("/pages/index.html", produtos_destaque=produtos_destaque)

@app.route("/sobre")
def about():
    return render_template("/pages/sobre.html")

@app.route("/contato")
def contato():
    return render_template("/pages/contato.html")

@app.route("/produtos")
def produtos():
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    # Coletar parâmetros de filtro da URL
    categorias_filtro = request.args.getlist('categoria')
    tamanhos_filtro = request.args.getlist('tamanho')
    cores_filtro = request.args.getlist('cor')
    precos_filtro = request.args.getlist('preco')

    # Query base
    sql = """
        SELECT DISTINCT p.id, p.nome, p.preco, p.imagem, p.destaque, p.categoria_id
        FROM produtos p
        WHERE p.ativo = TRUE
    """
    params = []

    # Aplicar filtros
    if categorias_filtro:
        placeholders = ','.join(['%s'] * len(categorias_filtro))
        sql += f" AND p.categoria_id IN ({placeholders})"
        params.extend(categorias_filtro)

    if tamanhos_filtro:
        sql += """
            AND EXISTS (
                SELECT 1 FROM estoque e 
                WHERE e.produto_id = p.id 
                AND e.tamanho_id IN ({})
            )
        """.format(','.join(['%s'] * len(tamanhos_filtro)))
        params.extend(tamanhos_filtro)

    if cores_filtro:
        sql += """
            AND EXISTS (
                SELECT 1 FROM estoque e 
                WHERE e.produto_id = p.id 
                AND e.cor_id IN ({})
            )
        """.format(','.join(['%s'] * len(cores_filtro)))
        params.extend(cores_filtro)

    # Filtro por preço
    if precos_filtro:
        condicoes_preco = []
        for preco_range in precos_filtro:
            if preco_range == '0-50':
                condicoes_preco.append("p.preco <= 50")
            elif preco_range == '50-100':
                condicoes_preco.append("p.preco BETWEEN 50 AND 100")
            elif preco_range == '100-200':
                condicoes_preco.append("p.preco BETWEEN 100 AND 200")
            elif preco_range == '200+':
                condicoes_preco.append("p.preco > 200")
        
        if condicoes_preco:
            sql += " AND (" + " OR ".join(condicoes_preco) + ")"

    # Ordenação
    sql += " ORDER BY p.nome"

    cursor.execute(sql, params)
    produtos = cursor.fetchall()

    # Buscar categorias, tamanhos e cores para o filtro
    cursor.execute("SELECT id, nome FROM categorias")
    categorias = cursor.fetchall()

    cursor.execute("SELECT id, nome FROM tamanhos")
    tamanhos = cursor.fetchall()

    cursor.execute("SELECT id, nome FROM cores")
    cores = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template("/pages/produtos.html", 
                         produtos=produtos, 
                         categorias=categorias, 
                         tamanhos=tamanhos, 
                         cores=cores)

@app.route("/visualizacao/<int:produto_id>")
def visualizar_produto(produto_id):
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT p.id, p.nome, p.descricao, p.preco, p.categoria_id, p.imagem 
        FROM produtos p 
        WHERE p.id = %s AND p.ativo = TRUE
    """, (produto_id,))
    produto = cursor.fetchone()
    
    if produto:
        cursor.execute("""
            SELECT p.id, p.nome, p.preco, p.imagem 
            FROM produtos p 
            WHERE p.categoria_id = %s AND p.id != %s AND p.ativo = TRUE 
            LIMIT 4
        """, (produto['categoria_id'], produto_id))
        produtos_relacionados = cursor.fetchall()
    else:
        produtos_relacionados = []

    cursor.execute("""SELECT DISTINCT t.id, t.nome 
                FROM tamanhos t
                JOIN estoque e ON e.tamanho_id = t.id
                JOIN produtos p ON p.id = e.produto_id
                WHERE p.id = %s AND p.ativo = TRUE ORDER BY t.id""", (produto_id,))
    tamanhos = cursor.fetchall()

    cursor.execute("""SELECT DISTINCT c.id, c.nome, e.tamanho_id, e.quantidade
                FROM cores c
                JOIN estoque e ON e.cor_id = c.id
                JOIN produtos p ON p.id = e.produto_id
                WHERE p.id = %s AND p.ativo = TRUE
                ORDER BY c.nome  """, (produto_id,))
    cores = cursor.fetchall()

    cursor.close()
    conexao.close()
    
    if produto:
        return render_template("/pages/visualizacao.html", produto=produto, produtos_relacionados=produtos_relacionados, cores=cores, tamanhos=tamanhos)
    else:
        return "Produto não encontrado", 404

# ==================== AUTENTICAÇÃO ====================

@app.route("/cadastro", methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome_completo = request.form.get('nome_completo', '').strip()
        email = request.form.get('email', '').strip().lower()
        telefone = request.form.get('telefone', '').strip()
        cpf = request.form.get('cpf', '').strip()
        nascimento = request.form.get('nascimento', '')
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar', '')

        erros = []

        if not nome_completo:
            erros.append('O nome completo é obrigatório.')
        
        if not email or '@' not in email:
            erros.append('E-mail inválido.')
        
        if not telefone:
            erros.append('Telefone é obrigatório.')
        
        if not cpf or len(cpf) < 11:
            erros.append('CPF inválido.')
        
        if not nascimento:
            erros.append('Data de nascimento é obrigatória.')
        else:
            nascimento_date = datetime.strptime(nascimento, '%Y-%m-%d')
            idade = (datetime.now() - nascimento_date).days // 365
            if idade < 18:
                erros.append('É necessário ter 18 anos ou mais para se cadastrar.')
        
        if not senha or len(senha) < 6:
            erros.append('A senha deve ter pelo menos 6 caracteres.')
        
        if senha != confirmar_senha:
            erros.append('As senhas não coincidem.')

        if erros:
            for erro in erros:
                flash(erro, 'error')
            return render_template("auth/cadastro.html")

        try:
            conexao = conectar()
            cursor = conexao.cursor()

            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
            if cursor.fetchone():
                flash('Este e-mail já está cadastrado.', 'error')
                return render_template("auth/cadastro.html")

            cursor.execute("SELECT id FROM usuarios WHERE cpf = %s", (cpf,))
            if cursor.fetchone():
                flash('Este CPF já está cadastrado.', 'error')
                return render_template("auth/cadastro.html")

            senha_hash = generate_password_hash(senha)

            sql_inserir = """
                INSERT INTO usuarios 
                (nome_completo, email, telefone, cpf, nascimento, senha_hash, is_admin)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            # Por padrão, novos usuários NÃO são admin
            cursor.execute(sql_inserir, (nome_completo, email, telefone, cpf, nascimento, senha_hash, False))
            conexao.commit()

            usuario_id = cursor.lastrowid

            cursor.close()
            conexao.close()

            session['usuario_id'] = usuario_id
            session['usuario_nome'] = nome_completo
            session['usuario_email'] = email
            session['is_admin'] = False

            flash('Cadastro realizado com sucesso! Bem-vindo(a) à MAGDA.', 'success')
            return redirect('/usuario')

        except mysql.connector.Error as err:
            flash(f'Erro no banco de dados: {err}', 'error')
            return render_template("auth/cadastro.html")
        except Exception as e:
            flash(f'Erro inesperado: {str(e)}', 'error')
            return render_template("auth/cadastro.html")
    return render_template("auth/cadastro.html")

#---LOGIN---#
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')

        if not email or not senha:
            flash('Por favor, preencha todos os campos.', 'error')
            return render_template("auth/login.html")

        try:
            conexao = conectar()
            cursor = conexao.cursor(dictionary=True)

            # MODIFICADO: Adicionar coluna 'ativo' na consulta
            cursor.execute("""
                SELECT id, nome_completo, email, cpf, senha_hash, is_admin, ativo 
                FROM usuarios 
                WHERE email = %s
            """, (email,))
            
            usuario = cursor.fetchone()
            
            if usuario:
                # VERIFICAÇÃO DE CONTA ATIVA - NOVO
                if not usuario.get('ativo', True):  # Se não tiver coluna ativo, assume True
                    cursor.close()
                    conexao.close()
                    flash('Sua conta está desativada. Entre em contato com o administrador.', 'error')
                    return render_template("auth/login.html")
                
                # Verificar senha
                if check_password_hash(usuario['senha_hash'], senha):
                    # Login bem-sucedido
                    session['usuario_id'] = usuario['id']
                    session['usuario_nome'] = usuario['nome_completo']
                    session['usuario_email'] = usuario['email']
                    session['usuario_cpf'] = usuario['cpf']
                    session['is_admin'] = usuario['is_admin']
                    
                    flash(f'Bem-vindo(a) de volta, {usuario["nome_completo"]}!', 'success')
                    
                    cursor.close()
                    conexao.close()
                    
                    return redirect('/')
                else:
                    cursor.close()
                    conexao.close()
                    flash('E-mail ou senha incorretos.', 'error')
                    return render_template("auth/login.html")
            else:
                cursor.close()
                conexao.close()
                flash('E-mail ou senha incorretos.', 'error')
                return render_template("auth/login.html")

        except Exception as e:
            if 'cursor' in locals():
                cursor.close()
            if 'conexao' in locals():
                conexao.close()
            flash(f'Erro ao fazer login: {str(e)}', 'error')
            return render_template("auth/login.html")

    return render_template("auth/login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'info')
    return redirect('/')

@app.route("/usuario")
@login_required
def usuario():
    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, nome_completo, email, telefone, cpf, nascimento, data_cadastro, is_admin
            FROM usuarios
            WHERE id = %s
        """, (session["usuario_id"],))

        usuario = cursor.fetchone()

        cursor.close()
        conexao.close()

        if not usuario:
            flash("Usuário não encontrado.", "error")
            return redirect("/login")

        return render_template("/auth/usuario.html", usuario=usuario)

    except Exception as e:
        flash(f"Erro ao carregar informações: {str(e)}", "error")
        return redirect("/")

# ==================== CARRINHO DE COMPRAS ====================

@app.route("/carrinho")
def carrinho_page():
        
    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
    
        # Buscar itens do carrinho
        cursor.execute("""
            SELECT c.*, p.nome, p.imagem, p.descricao, p.preco,
                (c.quantidade * p.preco) as subtotal
            FROM carrinho c
            JOIN produtos p ON c.produto_id = p.id
            WHERE c.usuario_id = %s AND p.ativo = TRUE
            ORDER BY c.data_adicao DESC
        """, (session['usuario_id'],))
        
        itens_carrinho = cursor.fetchall()
        
        # Calcular totais
        subtotal = sum(item['subtotal'] for item in itens_carrinho)
        frete = 0  # Frete grátis para este exemplo
        total = subtotal + frete
        
        cursor.close()
        conexao.close()
        
        return render_template("/pages/carrinho.html", 
                             itens_carrinho=itens_carrinho,
                             subtotal=subtotal,
                             frete=frete,
                             total=total)

    except Exception as e:
        cursor.close()
        conexao.close()
        flash(f"Erro ao carregar o carrinho: {str(e)}", "error")
        return redirect("/")
        

@app.route("/adicionar_carrinho/<int:produto_id>", methods=['POST'])
@login_required
def adicionar_carrinho(produto_id):
    try:
        if 'usuario_id' not in session:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        quantidade = int(request.form.get('quantidade', 1))
        tamanho_id = request.form.get('tamanho_id', '')
        cor_id = request.form.get('cor_id', '')
        
        # Validações
        if quantidade < 1:
            return jsonify({'success': False, 'message': 'Quantidade inválida'}), 400
        
        if not tamanho_id or not cor_id:
            return jsonify({'success': False, 'message': 'Selecione tamanho e cor'}), 400
        
        try:
            tamanho_id = int(tamanho_id)
            cor_id = int(cor_id)
        except ValueError:
            return jsonify({'success': False, 'message': 'Tamanho ou cor inválidos'}), 400
        
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
        
        # Buscar produto
        cursor.execute("""
            SELECT p.id, p.nome, p.preco
            FROM produtos p
            WHERE p.id = %s AND p.ativo = TRUE
        """, (produto_id,))
        
        produto = cursor.fetchone()
        
        if not produto:
            cursor.close()
            conexao.close()
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404
        
        # Verificar estoque
        cursor.execute("""
            SELECT quantidade 
            FROM estoque
            WHERE produto_id = %s 
            AND tamanho_id = %s 
            AND cor_id = %s
        """, (produto_id, tamanho_id, cor_id))
        
        estoque = cursor.fetchone()
        
        if not estoque:
            cursor.close()
            conexao.close()
            return jsonify({'success': False, 'message': 'Combinação de tamanho/cor não disponível'}), 400
        
        estoque_disponivel = estoque['quantidade']
        
        if estoque_disponivel <= 0:
            cursor.close()
            conexao.close()
            return jsonify({'success': False, 'message': 'Produto esgotado para esta combinação'}), 400
        
        if quantidade > estoque_disponivel:
            cursor.close()
            conexao.close()
            return jsonify({'success': False, 'message': f'Estoque insuficiente. Disponível: {estoque_disponivel}'}), 400
        
        # Verificar se já existe no carrinho
        cursor.execute("""
            SELECT id, quantidade 
            FROM carrinho 
            WHERE usuario_id = %s 
            AND produto_id = %s 
            AND tamanho_id = %s 
            AND cor_id = %s
        """, (session['usuario_id'], produto_id, tamanho_id, cor_id))
        
        item_existente = cursor.fetchone()
        
        if item_existente:
            nova_quantidade_total = item_existente['quantidade'] + quantidade
            
            if nova_quantidade_total > estoque_disponivel:
                cursor.close()
                conexao.close()
                return jsonify({'success': False, 'message': f'Limite de estoque atingido. Disponível: {estoque_disponivel}'}), 400
            
            cursor.execute("""
                UPDATE carrinho 
                SET quantidade = %s, data_adicao = NOW()
                WHERE id = %s
            """, (nova_quantidade_total, item_existente['id']))
            mensagem = f"Quantidade atualizada para {nova_quantidade_total}!"
        else:
            cursor.execute("""
                INSERT INTO carrinho 
                (usuario_id, produto_id, quantidade, tamanho_id, cor_id, data_adicao)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (session['usuario_id'], produto_id, quantidade, tamanho_id, cor_id))
            mensagem = f"{produto['nome']} adicionado ao carrinho!"
        
        # Contar itens no carrinho para atualizar badge
        cursor.execute("""
            SELECT COUNT(*) as count FROM carrinho 
            WHERE usuario_id = %s
        """, (session['usuario_id'],))
        
        carrinho_count = cursor.fetchone()['count']
        
        conexao.commit()
        cursor.close()
        conexao.close()
        
        return jsonify({
            'success': True,
            'message': mensagem,
            'carrinho_count': carrinho_count
        })
        
    except Exception as e:
        print(f"Erro ao adicionar ao carrinho: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro ao adicionar produto ao carrinho'}), 500

@app.route("/remover_carrinho/<int:item_id>")
@login_required
def remover_carrinho(item_id):
    try:
        conexao = conectar()
        cursor = conexao.cursor()
        
        cursor.execute("""
            DELETE FROM carrinho 
            WHERE id = %s AND usuario_id = %s
        """, (item_id, session['usuario_id']))
        
        conexao.commit()
        cursor.close()
        conexao.close()
        
        flash("Item removido do carrinho", "success")
        return redirect("/carrinho")
        
    except Exception as e:
        flash(f"Erro ao remover item: {str(e)}", "error")
        return redirect("/carrinho")

@app.route("/atualizar_carrinho/<int:item_id>", methods=['POST'])
@login_required
def atualizar_carrinho(item_id):
    try:
        quantidade = int(request.form.get('quantidade', 1))
        
        if quantidade <= 0:
            return redirect("/remover_carrinho/" + str(item_id))
        
        conexao = conectar()
        cursor = conexao.cursor()
        
        cursor.execute("""
            UPDATE carrinho 
            SET quantidade = %s 
            WHERE id = %s AND usuario_id = %s
        """, (quantidade, item_id, session['usuario_id']))
        
        conexao.commit()
        cursor.close()
        conexao.close()
        
        flash("Quantidade atualizada", "success")
        return redirect("/carrinho")
        
    except Exception as e:
        flash(f"Erro ao atualizar: {str(e)}", "error")
        return redirect("/carrinho")
    
# ==================== CHECKOUT ====================

@app.route("/checkout")
@login_required
def checkout():

        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
        
        # Buscar itens do carrinho com detalhes completos
        cursor.execute("""
            SELECT 
                c.id,
                c.quantidade,
                p.id as produto_id,
                p.nome,
                p.preco,
                p.imagem,
                t.nome as tamanho_nome,
                cr.nome as cor_nome,
                (c.quantidade * p.preco) as subtotal
            FROM carrinho c
            JOIN produtos p ON c.produto_id = p.id
            LEFT JOIN tamanhos t ON c.tamanho_id = t.id
            LEFT JOIN cores cr ON c.cor_id = cr.id
            WHERE c.usuario_id = %s
            ORDER BY c.data_adicao DESC
        """, (session['usuario_id'],))
        
        itens = cursor.fetchall()
        
        if not itens:
            flash("Seu carrinho está vazio", "warning")
            return redirect("/carrinho")
        
        # Calcular totais
        subtotal = sum(float(item['subtotal']) for item in itens if item['subtotal'])
        frete = 0  # Frete grátis ou calcular depois
        total = subtotal + frete
        
        # Buscar dados do usuário
        cursor.execute("""
            SELECT 
                nome_completo, 
                email, 
                telefone, 
                cpf,
                nascimento
            FROM usuarios 
            WHERE id = %s
        """, (session['usuario_id'],))
        
        usuario = cursor.fetchone()
        
        # Buscar endereço da última venda do usuário (se houver)
        cursor.execute("""
            SELECT ev.* 
            FROM enderecos_venda ev
            JOIN vendas v ON ev.venda_id = v.id
            WHERE v.usuario_id = %s
            ORDER BY v.data_venda DESC
            LIMIT 1
        """, (session['usuario_id'],))
        
        endereco = cursor.fetchone()
        
        cursor.close()
        conexao.close()
        
        return render_template("/pages/checkout.html",
                             itens=itens,
                             subtotal=subtotal,
                             frete=frete,
                             total=total,
                             usuario=usuario,
                             endereco=endereco)
        
        

@app.route("/finalizar_compra", methods=['POST'])
@login_required
def finalizar_compra():

        # Coletar dados do formulário
        forma_pagamento = request.form.get('forma_pagamento', 'simulacao')
        cep = request.form.get('cep', '')
        logradouro = request.form.get('logradouro', '')
        numero = request.form.get('numero', '')
        complemento = request.form.get('complemento', '')
        bairro = request.form.get('bairro', '')
        cidade = request.form.get('cidade', '')
        estado = request.form.get('estado', '')
        destinatario = request.form.get('destinatario', '')
        cpf_cnpj_nota = request.form.get('cpf_cnpj_nota', '')
        
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
        
        # Buscar itens do carrinho com todos os detalhes
        cursor.execute("""
            SELECT 
                c.id,
                c.quantidade,
                c.produto_id,
                c.tamanho_id,
                c.cor_id,
                p.nome,
                p.preco,
                t.nome as tamanho_nome,
                cr.nome as cor_nome,
                (c.quantidade * p.preco) as subtotal
            FROM carrinho c
            JOIN produtos p ON c.produto_id = p.id
            LEFT JOIN tamanhos t ON c.tamanho_id = t.id
            LEFT JOIN cores cr ON c.cor_id = cr.id
            WHERE c.usuario_id = %s
        """, (session['usuario_id'],))
        
        itens = cursor.fetchall()
        
        if not itens:
            flash("Seu carrinho está vazio", "warning")
            return redirect("/carrinho")
        
        # Calcular totais
        subtotal = sum(float(item['subtotal']) for item in itens)
        frete = 0  # Frete grátis
        total = subtotal + frete
        
        # Verificar estoque para cada item
        for item in itens:
            cursor.execute("""
                SELECT quantidade 
                FROM estoque 
                WHERE produto_id = %s 
                AND tamanho_id = %s 
                AND cor_id = %s
            """, (item['produto_id'], item['tamanho_id'], item['cor_id']))
            
            estoque = cursor.fetchone()
            
            if not estoque:
                flash(f"Produto '{item['nome']}' não disponível nesta combinação", "error")
                return redirect("/carrinho")
            
            if item['quantidade'] > estoque['quantidade']:
                flash(f"Estoque insuficiente para '{item['nome']}'. Disponível: {estoque['quantidade']}", "error")
                return redirect("/carrinho")
        
        # Inserir venda
        cursor.execute("""
            INSERT INTO vendas 
            (usuario_id, valor_total, subtotal, valor_frete, forma_pagamento, 
             frete_tipo, cpf_cnpj_nota, status, data_venda)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (session['usuario_id'], total, subtotal, frete, 
              forma_pagamento, 'grátis', cpf_cnpj_nota, 'confirmado'))
        
        venda_id = cursor.lastrowid
        
        # Inserir endereço da venda
        cursor.execute("""
            INSERT INTO enderecos_venda 
            (venda_id, cep, logradouro, numero, complemento, 
             bairro, cidade, estado, destinatario)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (venda_id, cep, logradouro, numero, complemento, 
              bairro, cidade, estado, destinatario))
        
        # Inserir itens da venda e atualizar estoque
        for item in itens:
            # Inserir item da venda
            cursor.execute("""
                INSERT INTO itens_venda 
                (venda_id, produto_id, quantidade, preco_unitario, tamanho, cor)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (venda_id, item['produto_id'], item['quantidade'], 
                  item['preco'], item['tamanho_nome'], item['cor_nome']))
            
            # Atualizar estoque na tabela estoque
            cursor.execute("""
                UPDATE estoque 
                SET quantidade = quantidade - %s 
                WHERE produto_id = %s 
                AND tamanho_id = %s 
                AND cor_id = %s
            """, (item['quantidade'], item['produto_id'], 
                  item['tamanho_id'], item['cor_id']))
        
        # Limpar carrinho
        cursor.execute("DELETE FROM carrinho WHERE usuario_id = %s", (session['usuario_id'],))
        
        conexao.commit()
        cursor.close()
        conexao.close()
        
        # Redirecionar para página de confirmação
        return redirect(f"/confirmacao.html/{venda_id}")
        

        

# ==================== ÁREA ADMINISTRATIVA ====================
        
@app.route("/admin/login", methods=['GET', 'POST'])
def admin_login():
    # Redirecionar se já estiver logado como admin
    if 'usuario_id' in session and session.get('is_admin'):
        return redirect('/admin/dashboard')
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        chave_admin = request.form.get('chave_admin', '')  # Chave especial para admin

        if not email or not senha:
            flash('Por favor, preencha todos os campos.', 'error')
            return render_template("admin/admin_login.html")

        try:
            conexao = conectar()
            cursor = conexao.cursor(dictionary=True)

            cursor.execute("""
                SELECT id, nome_completo, email, senha_hash, is_admin 
                FROM usuarios 
                WHERE email = %s AND is_admin = TRUE
            """, (email,))
            
            usuario = cursor.fetchone()
            cursor.close()
            conexao.close()

            # Verificar senha
            if usuario and check_password_hash(usuario['senha_hash'], senha):
                # Verificar chave admin (opcional - pode remover se não quiser esta camada extra)
                chave_correta = "ADMIN_MAGDA_2025"  # Altere para sua chave secreta
                if chave_admin == chave_correta:
                    # Login bem-sucedido como admin
                    session['usuario_id'] = usuario['id']
                    session['usuario_nome'] = usuario['nome_completo']
                    session['usuario_email'] = usuario['email']
                    session['is_admin'] = True
                    
                    flash(f'Bem-vindo(a) ao painel admin, {usuario["nome_completo"]}!', 'success')
                    return redirect('/admin/dashboard')
                else:
                    flash('Chave administrativa incorreta.', 'error')
            else:
                flash('E-mail ou senha incorretos, ou usuário não é administrador.', 'error')
                return render_template("admin/admin_login.html")

        except Exception as e:
            flash(f'Erro ao fazer login: {str(e)}', 'error')
            return render_template("admin/admin_login.html")

    return render_template("admin/admin_login.html")

@app.route("/admin/dashboard")
@admin_required
def dashboardmagda():
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        
        # Métricas principais
        cursor.execute("SELECT COALESCE(SUM(valor_total), 0) as total_vendas_hoje FROM vendas WHERE DATE(data_venda) = CURDATE()")
        vendas_hoje = cursor.fetchone()['total_vendas_hoje']
        
        cursor.execute("SELECT COUNT(*) as total_produtos FROM produtos WHERE ativo = TRUE")
        total_produtos = cursor.fetchone()['total_produtos']
        
        cursor.execute("SELECT COUNT(*) as novos_usuarios FROM usuarios WHERE DATE(data_cadastro) = CURDATE()")
        novos_usuarios = cursor.fetchone()['novos_usuarios']
        
        cursor.execute("""
            SELECT COUNT(DISTINCT produto_id) as estoque_baixo 
            FROM estoque 
            GROUP BY produto_id 
            HAVING SUM(quantidade) < 10
        """)
        estoque_baixo_result = cursor.fetchone()
        estoque_baixo = estoque_baixo_result['estoque_baixo'] if estoque_baixo_result else 0
        
        # Vendas últimos 7 dias
        cursor.execute("""
            SELECT DATE(data_venda) as data, COALESCE(SUM(valor_total), 0) as total 
            FROM vendas 
            WHERE data_venda >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(data_venda) 
            ORDER BY data
        """)
        vendas_db = cursor.fetchall()
        
        # Preencher datas faltantes
        datas_completas = []
        datas_labels = []
        
        for i in range(7):
            data_alvo = (datetime.now() - timedelta(days=6-i)).date()
            total = 0
            
            for venda in vendas_db:
                venda_data = venda['data']
                if venda_data == data_alvo:
                    total = float(venda['total'])
                    break
            
            data_formatada = data_alvo.strftime('%d/%m')
            datas_completas.append(total)
            datas_labels.append(data_formatada)
        
        # Produtos mais vendidos
        cursor.execute("""
            SELECT p.nome, SUM(iv.quantidade) as total_vendido, 
                   SUM(iv.quantidade * iv.preco_unitario) as receita
            FROM itens_venda iv 
            JOIN produtos p ON iv.produto_id = p.id
            GROUP BY p.id, p.nome 
            ORDER BY total_vendido DESC 
            LIMIT 5
        """)
        produtos_mais_vendidos = cursor.fetchall()
        
        # Vendas por categoria
        cursor.execute("""
            SELECT c.nome as categoria, COALESCE(SUM(iv.quantidade * iv.preco_unitario), 0) as total
            FROM categorias c
            LEFT JOIN produtos p ON c.id = p.categoria_id
            LEFT JOIN itens_venda iv ON p.id = iv.produto_id
            GROUP BY c.id, c.nome
            ORDER BY total DESC
        """)
        vendas_por_categoria = cursor.fetchall()
        
        # Atividades recentes
        cursor.execute("""
            SELECT v.data_venda as data, v.forma_pagamento, v.valor_total as valor
            FROM vendas v
            ORDER BY v.data_venda DESC
            LIMIT 5
        """)
        atividades_recentes_raw = cursor.fetchall()
        
        atividades_recentes = []
        for atividade in atividades_recentes_raw:
            atividades_recentes.append({
                'data': atividade['data'],
                'forma_pagamento': atividade['forma_pagamento'],
                'valor': float(atividade['valor'])
            })

        cursor.close()
        conn.close()

        crescimento = 12.5

        return render_template(
            "/pages/dashboard.html",
            vendas_hoje=float(vendas_hoje),
            total_produtos=total_produtos,
            novos_usuarios=novos_usuarios,
            estoque_baixo=estoque_baixo,
            vendas_7_dias=datas_completas,
            vendas_labels=datas_labels,
            produtos_mais_vendidos=produtos_mais_vendidos,
            vendas_por_categoria=vendas_por_categoria,
            atividades_recentes=atividades_recentes,
            crescimento=crescimento,
            now=datetime.now()
        )

    except Exception as e:
        print(f"Erro ao carregar a dashboard: {e}")
        import traceback
        traceback.print_exc()
        
        hoje = datetime.now().date()
        datas_exemplo = [0, 0, 0, 0, 0, 0, 0]
        labels_exemplo = [(hoje - timedelta(days=i)).strftime('%d/%m') for i in range(6, -1, -1)]
        
        return render_template(
            "/pages/dashboard.html",
            vendas_hoje=0,
            total_produtos=0,
            novos_usuarios=0,
            estoque_baixo=0,
            vendas_7_dias=datas_exemplo,
            vendas_labels=labels_exemplo,
            produtos_mais_vendidos=[],
            vendas_por_categoria=[],
            atividades_recentes=[],
            crescimento=0,
            now=datetime.now()
        )

@app.route("/admin/estoque")
@admin_required
def estoque():
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)

    categorias_filtro = request.args.getlist('categoria')
    tamanhos_filtro = request.args.getlist('tamanho')
    cores_filtro = request.args.getlist('cor')
    precos_filtro = request.args.getlist('preco')

    sql_ativos = """
        SELECT DISTINCT p.id, p.nome, p.preco, p.imagem, p.destaque, p.categoria_id, p.ativo
        FROM produtos p
        WHERE p.ativo = TRUE
    """
    
    sql_desativados = """
        SELECT DISTINCT p.id, p.nome, p.preco, p.imagem, p.destaque, p.categoria_id, p.ativo
        FROM produtos p
        WHERE p.ativo = FALSE
    """
    
    def aplicar_filtros(sql_base, params):
        sql = sql_base
        local_params = params.copy()
        
        if categorias_filtro:
            placeholders = ','.join(['%s'] * len(categorias_filtro))
            sql += f" AND p.categoria_id IN ({placeholders})"
            local_params.extend(categorias_filtro)

        if tamanhos_filtro:
            sql += """
                AND EXISTS (
                    SELECT 1 FROM estoque e 
                    WHERE e.produto_id = p.id 
                    AND e.tamanho_id IN ({})
                )
            """.format(','.join(['%s'] * len(tamanhos_filtro)))
            local_params.extend(tamanhos_filtro)

        if cores_filtro:
            sql += """
                AND EXISTS (
                    SELECT 1 FROM estoque e 
                    WHERE e.produto_id = p.id 
                    AND e.cor_id IN ({})
                )
            """.format(','.join(['%s'] * len(cores_filtro)))
            local_params.extend(cores_filtro)

        if precos_filtro:
            condicoes_preco = []
            for preco_range in precos_filtro:
                if preco_range == '0-50':
                    condicoes_preco.append("p.preco <= 50")
                elif preco_range == '50-100':
                    condicoes_preco.append("p.preco BETWEEN 50 AND 100")
                elif preco_range == '100-200':
                    condicoes_preco.append("p.preco BETWEEN 100 AND 200")
                elif preco_range == '200+':
                    condicoes_preco.append("p.preco > 200")
            
            if condicoes_preco:
                sql += " AND (" + " OR ".join(condicoes_preco) + ")"
        
        sql += " ORDER BY p.nome"
        
        return sql, local_params

    sql_ativos_filtrado, params_ativos = aplicar_filtros(sql_ativos, [])
    sql_desativados_filtrado, params_desativados = aplicar_filtros(sql_desativados, [])

    cursor.execute(sql_ativos_filtrado, params_ativos)
    produtos_ativos = cursor.fetchall()

    cursor.execute(sql_desativados_filtrado, params_desativados)
    produtos_desativados = cursor.fetchall()

    cursor.execute("SELECT id, nome FROM categorias")
    categorias = cursor.fetchall()

    cursor.execute("SELECT id, nome FROM tamanhos")
    tamanhos = cursor.fetchall()

    cursor.execute("SELECT id, nome FROM cores")
    cores = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template("/pages/estoque.html", 
                         produtos_ativos=produtos_ativos,
                         produtos_desativados=produtos_desativados,
                         categorias=categorias, 
                         tamanhos=tamanhos, 
                         cores=cores)

@app.route("/admin/novo_produto")
@admin_required
def novo_produto():
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    
    cursor.execute("SELECT c.id, c.nome FROM cores c")
    cores = cursor.fetchall()
    
    cursor.execute("SELECT t.id, t.nome FROM tamanhos t")
    tamanhos = cursor.fetchall()
    
    cursor.execute("SELECT c.id, c.nome FROM categorias c")
    categorias = cursor.fetchall()
    
    cursor.close()
    conexao.close()

    return render_template("/pages/novo_produto.html", cores=cores, tamanhos=tamanhos, categorias=categorias)

@app.route("/admin/salvar", methods=['POST'])
@admin_required
def salvar_produto():
    nome = request.form.get('nome', '')
    descricao = request.form.get('descricao', '')
    preco = request.form.get('preco', '')
    categoria_id = request.form.get('categoria_id', '')
    destaque = request.form.get('destaque', 'FALSE')
    
    tamanhos_ids = request.form.getlist('tamanho_id[]')
    cores_ids = request.form.getlist('cor_id[]')
    quantidades = request.form.getlist('quantidade[]')
    
    imagem_file = request.files.get("imagem")
    imagem_nome = None
    
    if imagem_file and imagem_file.filename != "":
        imagem_nome = secure_filename(imagem_file.filename)
        imagem_file.save(os.path.join(app.config["UPLOAD_FOLDER"], imagem_nome))

    if nome.strip() == "":
        flash("Erro: O nome não pode ser vazio.", "error")
        return redirect("/admin/novo_produto")
    if descricao.strip() == "":
        flash("Erro: A descrição não pode ser vazia.", "error")
        return redirect("/admin/novo_produto")
    if not tamanhos_ids or not cores_ids or not quantidades:
        flash("Erro: É necessário informar pelo menos um tamanho, cor e quantidade.", "error")
        return redirect("/admin/novo_produto")

    try:
        preco = float(preco)
        categoria_id = int(categoria_id)
        destaque = True if destaque == 'TRUE' else False
        
        tamanhos_ids = [int(t) for t in tamanhos_ids]
        cores_ids = [int(c) for c in cores_ids]
        quantidades = [int(q) for q in quantidades]
        
    except ValueError:
        flash("Erro: Tipos inválidos (preço/quantidade/ids).", "error")
        return redirect("/admin/novo_produto")

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)

    try:
        sql_produto_ins = """
            INSERT INTO produtos (nome, descricao, preco, categoria_id, imagem, destaque)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql_produto_ins, (nome, descricao, preco, categoria_id, imagem_nome, destaque))
        conexao.commit()
        produto_id = cursor.lastrowid

        sql_estoque_ins = """
            INSERT INTO estoque (produto_id, tamanho_id, cor_id, quantidade)
            VALUES (%s, %s, %s, %s)
        """
        
        for i in range(len(tamanhos_ids)):
            cursor.execute(sql_estoque_ins, (produto_id, tamanhos_ids[i], cores_ids[i], quantidades[i]))
        
        conexao.commit()
        flash("Produto cadastrado com sucesso!", "success")

    except Exception as e:
        conexao.rollback()
        flash(f"Erro interno: {str(e)}", "error")
        return redirect("/admin/novo_produto")
    finally:
        cursor.close()
        conexao.close()

    return redirect("/admin/estoque")

@app.route("/admin/editar_produto/<int:id>")
@admin_required
def editar_produto(id):
    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
        
        cursor.execute("SELECT c.id, c.nome FROM cores c")
        cores = cursor.fetchall()
        
        cursor.execute("SELECT t.id, t.nome FROM tamanhos t")
        tamanhos = cursor.fetchall()
        
        cursor.execute("SELECT c.id, c.nome FROM categorias c")
        categorias = cursor.fetchall()
        
        cursor.execute("""
            SELECT p.* 
            FROM produtos p 
            WHERE p.id = %s
        """, (id,))
        produto = cursor.fetchone()
        
        if not produto:
            cursor.close()
            conexao.close()
            flash("Produto não encontrado", "error")
            return redirect("/admin/estoque")
        
        cursor.execute("""
            SELECT e.id as estoque_id, e.tamanho_id, e.cor_id, e.quantidade,
                   t.nome as tamanho_nome, c.nome as cor_nome
            FROM estoque e 
            LEFT JOIN tamanhos t ON e.tamanho_id = t.id
            LEFT JOIN cores c ON e.cor_id = c.id
            WHERE e.produto_id = %s
        """, (id,))
        estoque_variacoes = cursor.fetchall()
        
        cursor.close()
        conexao.close()
            
        return render_template("/pages/editar_produto.html", 
                             produto=produto, 
                             cores=cores, 
                             tamanhos=tamanhos, 
                             categorias=categorias,
                             estoque_variacoes=estoque_variacoes)
        
    except Exception as e:
        flash(f"Erro ao buscar produto: {str(e)}", "error")
        return redirect("/admin/estoque")

@app.route("/atualizar/<int:id>", methods=['POST'])
@admin_required
def atualizar_produto(id):
    try:
        nome = request.form["nome"].strip()
        descricao = request.form["descricao"].strip()
        preco = request.form["preco"]
        categoria_id = request.form["categoria_id"]
        destaque = request.form.get('destaque', 'FALSE')
        
        tamanhos_ids = request.form.getlist('tamanho_id[]')
        cores_ids = request.form.getlist('cor_id[]')
        quantidades = request.form.getlist('quantidade[]')
        estoque_ids = request.form.getlist('estoque_id[]')
        
        if not nome:
            flash("Erro: O nome não pode ser vazio.", "error")
            return redirect(f"/admin/editar_produto/{id}")
        if not descricao:
            flash("Erro: A descrição não pode ser vazia.", "error")
            return redirect(f"/admin/editar_produto/{id}")
        if not tamanhos_ids or not cores_ids or not quantidades:
            flash("Erro: É necessário informar pelo menos um tamanho, cor e quantidade.", "error")
            return redirect(f"/admin/editar_produto/{id}")

        try:
            preco = float(preco)
            categoria_id = int(categoria_id)
            destaque = True if destaque == 'TRUE' else False
            
            tamanhos_ids = [int(t) for t in tamanhos_ids]
            cores_ids = [int(c) for c in cores_ids]
            quantidades = [int(q) for q in quantidades]
            estoque_ids = [int(e) if e else None for e in estoque_ids]
            
        except ValueError:
            flash("Erro: Valores numéricos inválidos.", "error")
            return redirect(f"/admin/editar_produto/{id}")

        imagem_nome = None
        imagem_file = request.files.get("imagem")
        
        if imagem_file and imagem_file.filename != "":
            imagem_nome = secure_filename(imagem_file.filename)
            imagem_file.save(os.path.join(app.config["UPLOAD_FOLDER"], imagem_nome))
        
        conexao = conectar()
        cursor = conexao.cursor()

        try:
            if imagem_nome:
                sql_produto = """
                    UPDATE produtos 
                    SET nome = %s, descricao = %s, preco = %s, categoria_id = %s, 
                        imagem = %s, destaque = %s 
                    WHERE id = %s
                """
                cursor.execute(sql_produto, (nome, descricao, preco, categoria_id, imagem_nome, destaque, id))
            else:
                sql_produto = """
                    UPDATE produtos 
                    SET nome = %s, descricao = %s, preco = %s, categoria_id = %s, 
                        destaque = %s 
                    WHERE id = %s
                """
                cursor.execute(sql_produto, (nome, descricao, preco, categoria_id, destaque, id))

            cursor.execute("DELETE FROM estoque WHERE produto_id = %s", (id,))
            
            sql_estoque = """
                INSERT INTO estoque (id, produto_id, tamanho_id, cor_id, quantidade)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            for i in range(len(tamanhos_ids)):
                estoque_id = estoque_ids[i] if i < len(estoque_ids) else None
                cursor.execute(sql_estoque, (estoque_id, id, tamanhos_ids[i], cores_ids[i], quantidades[i]))
            
            conexao.commit()
            cursor.close()
            conexao.close()
            
            flash("Produto atualizado com sucesso!", "success")
            return redirect("/admin/estoque")
            
        except Exception as e:
            conexao.rollback()
            flash(f"Erro ao atualizar produto: {str(e)}", "error")
            return redirect(f"/admin/editar_produto/{id}")
            
    except Exception as e:
        if 'conexao' in locals():
            conexao.rollback()
            conexao.close()
        flash(f"Erro ao atualizar produto: {str(e)}", "error")
   
        flash(f"Erro ao atualizar produto: {str(e)}", "error")
        return redirect(f"/admin/editar_produto/{id}")

@app.route("/admin/desativar_produto/<int:id>")
@admin_required
def desativar_produto(id):
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    
    try:
        sql_produto = "UPDATE produtos SET ativo = FALSE WHERE id = %s"
        cursor.execute(sql_produto, (id,))
        conexao.commit()
        flash("Produto desativado com sucesso!", "success")
    except Exception as e:
        conexao.rollback()
        flash(f"Erro ao desativar produto: {str(e)}", "error")
    finally:
        cursor.close()
        conexao.close()  
    return redirect("/admin/estoque")

@app.route("/admin/reativar_produto/<int:id>")
@admin_required
def reativar_produto(id):
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    
    try:
        sql_produto = "UPDATE produtos SET ativo = TRUE WHERE id = %s"
        cursor.execute(sql_produto, (id,))
        conexao.commit()
        flash("Produto reativado com sucesso!", "success")
    except Exception as e:
        conexao.rollback()
        flash(f"Erro ao reativar produto: {str(e)}", "error")
    finally:
        cursor.close()
        conexao.close()
    
    return redirect("/admin/estoque")

@app.route("/produto/<int:id>/destaque", methods=['POST'])
@admin_required
def toggle_destaque(id):
    conexao = conectar()
    cursor = conexao.cursor()
    
    try:
        sql = "UPDATE produtos SET destaque = NOT destaque WHERE id = %s"
        cursor.execute(sql, (id,))
        conexao.commit()
        flash("Destaque alterado com sucesso!", "success")
    except Exception as e:
        conexao.rollback()
        flash(f"Erro: {str(e)}", "error")
    finally:
        cursor.close()
        conexao.close()
    
    return redirect("/admin/estoque")

# ==================== ROTA PARA CRIAR ADMIN MANUALMENTE ====================

@app.route("/criar-admin", methods=['GET', 'POST'])
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"[DEBUG] Verificando admin... Sessão: {dict(session)}")
        
        # Se não estiver logado
        if 'usuario_id' not in session:
            print("[DEBUG] Não está logado - redirecionando para dashboard")
            flash('Faça login para acessar.', 'error')
            return redirect('/dashboardmagda')
        
        # Verificar se é admin no banco
        try:
            conexao = conectar()
            cursor = conexao.cursor(dictionary=True)
            cursor.execute("SELECT is_admin FROM usuarios WHERE id = %s", (session['usuario_id'],))
            usuario = cursor.fetchone()
            cursor.close()
            conexao.close()
            
            if usuario and usuario['is_admin']:
                print(f"[DEBUG] É admin! ID: {session['usuario_id']}")
                return f(*args, **kwargs)
            else:
                print(f"[DEBUG] NÃO é admin! ID: {session['usuario_id']}")
                flash('Acesso restrito a administradores.', 'error')
                return redirect('/dashboardmagda')
                
        except Exception as e:
            print(f"[DEBUG] Erro ao verificar admin: {str(e)}")
            flash('Erro ao verificar permissões.', 'error')
            return redirect('/dashboardmagda')
    
    return decorated_function

def criar_admin():
    # Esta rota só deve estar ativa durante desenvolvimento
    # Em produção, remova ou proteja com uma chave especial
    
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        if email and senha:
            try:
                conexao = conectar()
                cursor = conexao.cursor()
                
                senha_hash = generate_password_hash(senha)
                
                cursor.execute("""
                    UPDATE usuarios 
                    SET senha_hash = %s, is_admin = TRUE 
                    WHERE email = %s
                """, (senha_hash, email))
                
                conexao.commit()
                
                cursor.close()
                conexao.close()
                
                flash(f'Usuário {email} promovido a administrador!', 'success')
                return redirect('/login')
                
            except Exception as e:
                flash(f'Erro: {str(e)}', 'error')
    
    return '''
    <form method="post">
        <h2>Criar Admin</h2>
        <input type="email" name="email" placeholder="Email do usuário" required><br>
        <input type="password" name="senha" placeholder="Nova senha" required><br>
        <button type="submit">Tornar Admin</button>
    </form>
    '''

@app.route("/setup-admin", methods=['GET', 'POST'])
def setup_admin():
    """Rota para configurar o primeiro administrador"""
    
    # Verificar se já existe algum admin
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as count FROM usuarios WHERE is_admin = TRUE")
    resultado = cursor.fetchone()
    cursor.close()
    conexao.close()
    
    if resultado and resultado['count'] > 0:
        flash("Já existe um administrador configurado. Use o login admin.", "warning")
        return redirect('/admin/login')
    
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')
        
        if not all([nome, email, senha, confirmar_senha]):
            flash("Todos os campos são obrigatórios.", "error")
            return render_template("admin/setup_admin.html")
        
        if senha != confirmar_senha:
            flash("As senhas não coincidem.", "error")
            return render_template("admin/setup_admin.html")
        
        if len(senha) < 6:
            flash("A senha deve ter pelo menos 6 caracteres.", "error")
            return render_template("admin/setup_admin.html")
        
        try:
            conexao = conectar()
            cursor = conexao.cursor()
            
            # Verificar se o email já existe
            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
            if cursor.fetchone():
                flash("Este email já está cadastrado.", "error")
                return render_template("admin/setup_admin.html")
            
            # Criar hash da senha
            senha_hash = generate_password_hash(senha)
            
            # Inserir o usuário admin
            sql = """
                INSERT INTO usuarios 
                (nome_completo, email, senha_hash, is_admin, data_cadastro)
                VALUES (%s, %s, %s, TRUE, NOW())
            """
            cursor.execute(sql, (nome, email, senha_hash))
            conexao.commit()
            
            cursor.close()
            conexao.close()
            
            flash(f"Administrador '{nome}' criado com sucesso! Agora faça login.", "success")
            return redirect('/admin/login')
            
        except Exception as e:
            flash(f"Erro ao criar administrador: {str(e)}", "error")
            return render_template("admin/setup_admin.html")
    
    return render_template("admin/setup_admin.html")

@app.before_request
def redirecionar_rotas_antigas():
    """Redireciona rotas antigas para as novas versões com admin/"""
    rotas_redirecionamento = {
        '/dashboard': '/admin/dashboard',
        '/estoque': '/admin/estoque',
        '/novo_produto': '/admin/novo_produto',
        '/salvar': '/admin/salvar',
        '/gerenciar_usuarios': '/admin/gerenciar_usuarios',
    }
    
    if request.path in rotas_redirecionamento:
        return redirect(rotas_redirecionamento[request.path])
    
# ==================== FUNÇÕES HELPER PARA TEMPLATES ====================

@app.context_processor
def inject_template_vars():
    """Injeta variáveis e funções em todos os templates"""
    def usuario_logado():
        return 'usuario_id' in session
    
    def eh_admin():
        """Verifica se o usuário atual é admin"""
        if 'usuario_id' not in session:
            return False
        
        # Usar cache na sessão para evitar consultas ao banco
        if 'is_admin_checked' in session:
            return session.get('is_admin', False)
        
        # Consultar banco se não tiver cache
        try:
            conexao = conectar()
            cursor = conexao.cursor(dictionary=True)
            cursor.execute("SELECT is_admin FROM usuarios WHERE id = %s", (session['usuario_id'],))
            usuario = cursor.fetchone()
            cursor.close()
            conexao.close()
            
            is_admin = usuario and usuario.get('is_admin', False)
            session['is_admin'] = is_admin
            session['is_admin_checked'] = True
            return is_admin
        except:
            return False
    
    def get_usuario_nome():
        return session.get('usuario_nome', 'Visitante')
    
    return dict(
        usuario_logado=usuario_logado,
        eh_admin=eh_admin,
        get_usuario_nome=get_usuario_nome,
        agora=datetime.now
    )
    
# ==================== TEMPLATE FILTERS ====================

@app.template_filter('formatar_data')
def formatar_data(data):
    if isinstance(data, str):
        data = datetime.strptime(data, '%Y-%m-%d')
    return data.strftime('%d/%m/%Y')

@app.template_filter('formatar_moeda')
def formatar_moeda(valor):
    return f"R$ {float(valor):.2f}".replace('.', ',')

# ==================== ROTA DE GERENCIAMENTO DE USUÁRIOS ====================
#/GERENCIAR CLIENTES/#
@app.route("/admin/gerenciar_clientes")
@admin_required
def gerenciar_clientes():
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            id,
            nome_completo,
            email,
            telefone,
            cpf,
            nascimento,
            data_cadastro,
            ativo
        FROM usuarios
        ORDER BY data_cadastro DESC
    """)
    
    clientes = cursor.fetchall()

    cursor.close()
    conexao.close() 

    return render_template("/auth/gerenciar_clientes.html", clientes=clientes)

@app.route("/editar_cliente/<int:id>", methods=["GET", "POST"])
def editar_cliente(id):
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)

    # Buscar cliente
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
    cliente = cursor.fetchone()

    if not cliente:
        flash("Cliente não encontrado!", "erro")
        return redirect(url_for("gerenciar_clientes"))

    if request.method == "POST":
        nome = request.form["nome_completo"]
        email = request.form["email"]
        telefone = request.form["telefone"]
        cpf = request.form["cpf"]
        nascimento = request.form["nascimento"]
        senha = request.form.get("senha", "").strip()

        # Atualização SEM senha
        if senha == "":
            cursor.execute("""
                UPDATE usuarios
                SET nome_completo=%s, email=%s, telefone=%s, cpf=%s, nascimento=%s
                WHERE id=%s
            """, (nome, email, telefone, cpf, nascimento, id))

        # Atualização COM senha
        else:
            senha_hash = generate_password_hash(senha)

            cursor.execute("""
                UPDATE usuarios
                SET nome_completo=%s, email=%s, telefone=%s, cpf=%s, nascimento=%s, senha_hash=%s
                WHERE id=%s
            """, (nome, email, telefone, cpf, nascimento, senha_hash, id))

        conexao.commit()
        cursor.close()
        conexao.close()

        flash("Cliente atualizado com sucesso!", "sucesso")
        return redirect(url_for("gerenciar_clientes"))

    cursor.close()
    conexao.close()

    return render_template("auth/editar_cliente.html", cliente=cliente)

#/DESATIVAR USUARIO/
@app.route("/admin/desativar_usuario/<int:id>")
@admin_required
def desativar_usuario(id):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("UPDATE usuarios SET ativo = FALSE WHERE id = %s", (id,))
    conexao.commit()

    cursor.close()
    conexao.close()

    flash("Usuário desativado!", "aviso")
    return redirect(url_for("gerenciar_clientes"))

#/ATIVAR USUARIO/
@app.route("/admin/ativar_usuario/<int:id>")
@admin_required
def ativar_usuario(id):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("UPDATE usuarios SET ativo = TRUE WHERE id = %s", (id,))
    conexao.commit()

    cursor.close()
    conexao.close()

    flash("Usuário ativado!", "sucesso")
    return redirect(url_for("gerenciar_clientes"))

    
# Teste a query isoladamente
@app.route("/teste_query")
def teste_query():
    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
        
        # Teste cada parte da query
        print("Testando query básica...")
        cursor.execute("SELECT * FROM usuarios LIMIT 3")
        usuarios = cursor.fetchall()
        
        print("Testando query com LEFT JOIN...")
        cursor.execute("""
            SELECT u.id, u.nome_completo, COUNT(v.id) as total_vendas
            FROM usuarios u
            LEFT JOIN vendas v ON u.id = v.usuario_id
            GROUP BY u.id
            LIMIT 3
        """)
        usuarios_compras = cursor.fetchall()
        
        cursor.close()
        conexao.close()
        
        return jsonify({
            "query_basica": usuarios,
            "query_compras": usuarios_compras
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)