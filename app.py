from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
from functools import wraps
import mysql.connector
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json


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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash("Você precisa fazer login para acessar esta página", "error")
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash("Você precisa fazer login para acessar esta página", "error")
            return redirect('/login')
        
        # Verificar se é admin
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT is_admin FROM usuarios WHERE id = %s", (session['usuario_id'],))
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
    
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT is_admin FROM usuarios WHERE id = %s", (session['usuario_id'],))
    usuario = cursor.fetchone()
    cursor.close()
    conexao.close()
    
    return usuario and usuario.get('is_admin')

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

            cursor.execute("""
                SELECT id, nome_completo, email, senha_hash, is_admin 
                FROM usuarios 
                WHERE email = %s
            """, (email,))
            
            usuario = cursor.fetchone()
            cursor.close()
            conexao.close()

            if usuario and check_password_hash(usuario['senha_hash'], senha):
                # Login bem-sucedido
                session['usuario_id'] = usuario['id']
                session['usuario_nome'] = usuario['nome_completo']
                session['usuario_email'] = usuario['email']
                session['is_admin'] = usuario['is_admin']
                
                flash(f'Bem-vindo(a) de volta, {usuario["nome_completo"]}!', 'success')
                return redirect('/')
            else:
                flash('E-mail ou senha incorretos.', 'error')
                return render_template("auth/login.html")

        except Exception as e:
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

@app.route("/admin/gerenciar_clientes")
@admin_required
def clientes():   
    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, nome_completo, email, telefone, cpf, nascimento, 
                   data_cadastro, is_admin
            FROM usuarios
            ORDER BY data_cadastro DESC
        """)
        clientes = cursor.fetchall()
        
        cursor.close()
        conexao.close()
        
        return render_template("/auth/gerenciar_clientes.html", clientes=clientes)
    
    except Exception as e:
        flash(f"Erro ao carregar clientes: {str(e)}", "error")
        return redirect("/admin/dashboard")

@app.route("/admin/tornar_admin/<int:usuario_id>")
@admin_required
def tornar_admin(usuario_id):
    try:
        conexao = conectar()
        cursor = conexao.cursor()
        
        cursor.execute("UPDATE usuarios SET is_admin = TRUE WHERE id = %s", (usuario_id,))
        conexao.commit()
        
        cursor.close()
        conexao.close()
        
        flash("Usuário promovido a administrador com sucesso!", "success")
        
    except Exception as e:
        flash(f"Erro ao promover usuário: {str(e)}", "error")
    
    return redirect("/admin/gerenciar_clientes")

@app.route("/admin/remover_admin/<int:usuario_id>")
@admin_required
def remover_admin(usuario_id):
    try:
        conexao = conectar()
        cursor = conexao.cursor()
        
        cursor.execute("UPDATE usuarios SET is_admin = FALSE WHERE id = %s", (usuario_id,))
        conexao.commit()
        
        cursor.close()
        conexao.close()
        
        flash("Permissões de administrador removidas com sucesso!", "success")
        
    except Exception as e:
        flash(f"Erro ao remover permissões: {str(e)}", "error")
    
    return redirect("/admin/gerenciar_clientes")

@app.route("/admin/excluir_usuario/<int:usuario_id>")
@admin_required
def excluir_usuario(usuario_id):
    try:
        # Não permitir excluir a si mesmo
        if usuario_id == session.get('usuario_id'):
            flash("Você não pode excluir sua própria conta!", "error")
            return redirect("/admin/gerenciar_clientes")
        
        conexao = conectar()
        cursor = conexao.cursor()
        
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
        conexao.commit()
        
        cursor.close()
        conexao.close()
        
        flash("Usuário excluído com sucesso!", "success")
        
    except Exception as e:
        flash(f"Erro ao excluir usuário: {str(e)}", "error")
    
    return redirect("/admin/gerenciar_clientes")

@app.route("/admin/pedidos")
@admin_required
def pedidos():
    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT v.*, u.nome_completo, u.email
            FROM vendas v
            LEFT JOIN usuarios u ON v.usuario_id = u.id
            ORDER BY v.data_venda DESC
        """)
        pedidos = cursor.fetchall()
        
        cursor.close()
        conexao.close()
        
        return render_template("admin/pedidos.html", pedidos=pedidos)
    
    except Exception as e:
        flash(f"Erro ao carregar pedidos: {str(e)}", "error")
        return redirect("/admin/dashboard")

@app.route("/admin/relatorios")
@admin_required
def relatorios():
    return render_template("admin/relatorios.html")

@app.route("/admin/sair")
def admin_logout():
    session.clear()
    flash('Você saiu do painel administrativo.', 'info')
    return redirect('/')

# ==================== ROTAS DE USUÁRIO COMUM ====================

@app.route("/editar_usuario/<int:usuario_id>", methods=['GET', 'POST'])
@login_required
def editar_usuario(usuario_id):
    # Verificar se o usuário está editando seu próprio perfil
    if usuario_id != session.get('usuario_id') and not verificar_permissao_admin():
        flash("Você só pode editar seu próprio perfil.", "error")
        return redirect('/usuario')
    
    if request.method == 'POST':
        nome_completo = request.form.get('nome_completo', '').strip()
        email = request.form.get('email', '').strip().lower()
        telefone = request.form.get('telefone', '').strip()
        cpf = request.form.get('cpf', '').strip()
        nascimento = request.form.get('nascimento', '')
        
        # Se for admin editando outro usuário, permite mudar is_admin
        is_admin = request.form.get('is_admin') == 'true' if verificar_permissao_admin() else None

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
                erros.append('É necessário ter 18 anos ou mais.')
        
        if erros:
            for erro in erros:
                flash(erro, 'error')
            return redirect(f'/editar_usuario/{usuario_id}')

        try:
            conexao = conectar()
            cursor = conexao.cursor()

            # Verificar se email já existe em outro usuário
            cursor.execute("SELECT id FROM usuarios WHERE email = %s AND id != %s", (email, usuario_id))
            if cursor.fetchone():
                flash('Este e-mail já está em uso por outro usuário.', 'error')
                return redirect(f'/editar_usuario/{usuario_id}')

            # Verificar se CPF já existe em outro usuário
            cursor.execute("SELECT id FROM usuarios WHERE cpf = %s AND id != %s", (cpf, usuario_id))
            if cursor.fetchone():
                flash('Este CPF já está em uso por outro usuário.', 'error')
                return redirect(f'/editar_usuario/{usuario_id}')

            # Atualizar usuário
            if is_admin is not None and verificar_permissao_admin():
                sql_update = """
                    UPDATE usuarios 
                    SET nome_completo = %s, email = %s, telefone = %s, 
                        cpf = %s, nascimento = %s, is_admin = %s
                    WHERE id = %s
                """
                cursor.execute(sql_update, (nome_completo, email, telefone, cpf, nascimento, is_admin, usuario_id))
            else:
                sql_update = """
                    UPDATE usuarios 
                    SET nome_completo = %s, email = %s, telefone = %s, 
                        cpf = %s, nascimento = %s
                    WHERE id = %s
                """
                cursor.execute(sql_update, (nome_completo, email, telefone, cpf, nascimento, usuario_id))
            
            conexao.commit()
            cursor.close()
            conexao.close()

            # Atualizar sessão se for o próprio usuário
            if usuario_id == session.get('usuario_id'):
                session['usuario_nome'] = nome_completo
                session['usuario_email'] = email
                if is_admin is not None:
                    session['is_admin'] = is_admin

            flash('Informações atualizadas com sucesso!', 'success')
            
            # Redirecionar conforme o tipo de usuário
            if verificar_permissao_admin() and usuario_id != session.get('usuario_id'):
                return redirect('/admin/gerenciar_clientes')
            else:
                return redirect('/usuario')

        except mysql.connector.Error as err:
            flash(f'Erro no banco de dados: {err}', 'error')
            return redirect(f'/editar_usuario/{usuario_id}')
        except Exception as e:
            flash(f'Erro inesperado: {str(e)}', 'error')
            return redirect(f'/editar_usuario/{usuario_id}')
    
    elif request.method == 'GET':
        try:
            conexao = conectar()
            cursor = conexao.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
            usuario = cursor.fetchone()
            
            cursor.close()
            conexao.close()

            if not usuario:
                flash("Usuário não encontrado.", "error")
                return redirect('/usuario' if not verificar_permissao_admin() else '/admin/gerenciar_clientes')
            
            # Verificar permissão para editar
            pode_editar = (usuario_id == session.get('usuario_id')) or verificar_permissao_admin()
            if not pode_editar:
                flash("Você não tem permissão para editar este perfil.", "error")
                return redirect('/')
            
            return render_template("auth/editar_usuario.html", usuario=usuario, is_admin=verificar_permissao_admin())
        
        except Exception as e:
            flash(f"Erro ao carregar usuário: {str(e)}", "error")
            return redirect('/usuario')
    
    return render_template("auth/editar_usuario.html")

# ==================== MIDDLEWARE PARA PROTEGER ROTAS ====================

@app.before_request
def proteger_rotas_admin():
    # Lista de rotas que só admin pode acessar
    rotas_protegidas = [
        '/admin/', '/dashboard', '/estoque', '/novo_produto', '/salvar',
        '/editar_produto/', '/atualizar/', '/desativar_produto/', '/reativar_produto/',
        '/produto/', '/destaque', '/gerenciar_clientes', '/tornar_admin/',
        '/remover_admin/', '/excluir_usuario/', '/pedidos', '/relatorios'
    ]
    
    # Verificar se a rota atual é protegida
    rota_atual = request.path
    precisa_proteger = any(rota_atual.startswith(rota) for rota in rotas_protegidas)
    
    if precisa_proteger:
        # Verificar se o usuário está autenticado e é admin
        if 'usuario_id' not in session:
            flash("Acesso restrito. Faça login como administrador.", "error")
            return redirect('/login')
        
        if not session.get('is_admin'):
            flash("Acesso restrito. Permissões insuficientes.", "error")
            return redirect('/')

# ==================== CARRINHO E CHECKOUT ====================

@app.route("/api/carrinho", methods=['GET'])
def get_carrinho():
    return jsonify({"message": "Carrinho gerenciado no frontend"})

@app.route("/api/carrinho/add", methods=['POST'])
def add_to_carrinho():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    
    required_fields = ['produto_id', 'nome', 'preco']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Campo obrigatório faltando: {field}"}), 400
    
    return jsonify({
        "success": True,
        "message": "Produto adicionado ao carrinho",
        "produto": data
    })

@app.route("/checkout")
@login_required
def checkout():
    return render_template("/pages/checkout.html")

@app.route("/api/produto/<int:produto_id>/estoque")
def get_estoque_produto(produto_id):
    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT e.tamanho_id, e.cor_id, e.quantidade,
                   t.nome as tamanho_nome, c.nome as cor_nome
            FROM estoque e
            JOIN tamanhos t ON e.tamanho_id = t.id
            JOIN cores c ON e.cor_id = c.id
            WHERE e.produto_id = %s AND e.quantidade > 0
            ORDER BY t.id, c.nome
        """, (produto_id,))
        
        estoque = cursor.fetchall()
        cursor.close()
        conexao.close()
        
        return jsonify({
            "success": True,
            "estoque": estoque
        })
        
    except Exception as e:
        print(f"Erro ao buscar estoque: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ==================== ROTA PARA CRIAR ADMIN MANUALMENTE ====================

@app.route("/criar-admin", methods=['GET', 'POST'])
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
        '/gerenciar_clientes': '/admin/gerenciar_clientes',
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

if __name__ == "__main__":
    app.run(debug=True, port=5001)

# http://localhost:5001/admin/login PARA ACESSAR O PAINEL ADMIN 

# http://localhost:5001/criar-admin PARA CRIAR UMA CONTA ADMIN PRIMEIRO CRIE UMA CONTA NORMAL E DEPOIS ACESSE ESSA ROTA

# ADMIN_MAGDA_2025