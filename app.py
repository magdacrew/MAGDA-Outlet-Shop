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
                SELECT id, nome_completo, email, senha_hash, is_admin, ativo
                FROM usuarios 
                WHERE email = %s
            """, (email,))
            
            usuario = cursor.fetchone()
            cursor.close()
            conexao.close()

            # ❌ Usuário não existe
            if not usuario:
                flash('E-mail ou senha incorretos.', 'error')
                return render_template("auth/login.html")

            # ❌ Usuário desativado → BLOQUEAR login
            if usuario["ativo"] == 0:
                flash("Sua conta está DESATIVADA. Fale com o suporte.", "error")
                return render_template("auth/login.html")

            # ❌ Senha incorreta
            if not check_password_hash(usuario['senha_hash'], senha):
                flash('E-mail ou senha incorretos.', 'error')
                return render_template("auth/login.html")

            # ✅ LOGIN PERMITIDO
            session['usuario_id'] = usuario['id']
            session['usuario_nome'] = usuario['nome_completo']
            session['usuario_email'] = usuario['email']
            session['is_admin'] = usuario['is_admin']

            flash(f'Bem-vindo(a) de volta, {usuario["nome_completo"]}!', 'success')
            return redirect('/')

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

#/VISUALIZAR CLIENTES/#
@app.route("/admin/visualizar_clientes")
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

    return render_template("/auth/visualizar_clientes.html", clientes=clientes)


#/EDITAR CLIENTE/#
@app.route("/admin/editar_cliente/<int:id>", methods=["GET", "POST"])
@admin_required
def editar_cliente(id):
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)

    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
    cliente = cursor.fetchone()

    if not cliente:
        cursor.close()
        conexao.close()
        return "Cliente não encontrado", 404    

    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        telefone = request.form["telefone"]
        cpf = request.form["cpf"]
        nascimento = request.form["nascimento"]

        cursor.execute("""
            UPDATE usuarios
            SET nome_completo=%s, email=%s, telefone=%s, cpf=%s, nascimento=%s
            WHERE id=%s
        """, (nome, email, telefone, cpf, nascimento, id))

        conexao.commit()
        cursor.close()
        conexao.close()

        return redirect(url_for("gerenciar_clientes"))

    cursor.close()
    conexao.close()
    return render_template("/auth/editar_cliente.html", cliente=cliente)


#/DESATIVAR CLIENTE/#
@app.route("/admin/desativar_cliente/<int:id>")
@admin_required
def desativar_cliente(id):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("UPDATE usuarios SET ativo = FALSE WHERE id = %s", (id,))
    conexao.commit()

    cursor.close()
    conexao.close()

    return redirect("/admin/visualizar_clientes")


#/REATIVAR CLIENTE/#
@app.route("/admin/reativar_cliente/<int:id>")
@admin_required
def reativar_cliente(id):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("UPDATE usuarios SET ativo = TRUE WHERE id = %s", (id,))
    conexao.commit()

    cursor.close()
    conexao.close()

    return redirect("/admin/visualizar_clientes")

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
            
    salvar_carrinho(data)

    return jsonify({
        "success": True,
        "message": "Produto adicionado ao carrinho",
        "produto": data
    })

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
        '/visualizar_clientes': '/admin/visualizar_clientes',
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

# ==================== CARRINHO E CHECKOUT ====================

@app.route("/checkout", methods=['GET', 'POST'])
@login_required
def checkout_dados():
    """Página de checkout com dados do usuário e carrinho"""
    
    # Verificar se tem carrinho na sessão
    carrinho = session.get('carrinho', [])    
    if not carrinho or len(carrinho) == 0:
        flash("Seu carrinho está vazio. Adicione produtos antes de finalizar a compra.", "error")
        return redirect('/produtos')
    
    # Obter usuário do banco de dados
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    
    # Buscar dados do usuário
    cursor.execute("""
        SELECT nome_completo, email, telefone, cpf
        FROM usuarios 
        WHERE id = %s
    """, (session['usuario_id'],))
    usuario = cursor.fetchone()
    
    cursor.close()
    conexao.close()
    
    if not usuario:
        flash("Usuário não encontrado", "error")
        return redirect('/')
    
    # Separar nome e sobrenome
    nome_completo = usuario['nome_completo'].split()
    nome = nome_completo[0] if len(nome_completo) > 0 else ""
    sobrenome = " ".join(nome_completo[1:]) if len(nome_completo) > 1 else ""
    
    # Obter CEP da sessão (se foi informado no carrinho)
    cep = session.get('cep_frete', '')
    endereco = None
    
    # Se tem CEP, buscar endereço via API
    if cep:
        try:
            import requests
            response = requests.get(f"https://viacep.com.br/ws/{cep.replace('-', '')}/json/")
            if response.status_code == 200:
                endereco_data = response.json()
                if 'erro' not in endereco_data:
                    endereco = {
                        'logradouro': endereco_data.get('logradouro', ''),
                        'bairro': endereco_data.get('bairro', ''),
                        'localidade': endereco_data.get('localidade', ''),
                        'uf': endereco_data.get('uf', '')
                    }
        except:
            pass
    
    # Obter carrinho da sessão
    carrinho = session.get('carrinho', [])
    
    # Calcular totais
    subtotal = sum(item.get('preco', 0) * item.get('quantidade', 1) for item in carrinho)
    frete = session.get('frete_selecionado_valor', 0)
    total = subtotal + frete
    
    return render_template("/pages/checkout_dados.html",
                         usuario={
                             'email': usuario['email'],
                             'nome': nome,
                             'sobrenome': sobrenome,
                             'telefone': usuario['telefone'],
                             'cpf': usuario['cpf']
                         },
                         cep=cep,
                         endereco=endereco,
                         carrinho=carrinho,
                         subtotal=subtotal,
                         frete=frete,
                         total=total)

@app.route("/api/carrinho/info", methods=['GET'])
@login_required
def get_carrinho_info():
    """API para obter informações do carrinho"""
    carrinho = session.get('carrinho', [])
    
    # Calcular totais
    subtotal = sum(item.get('preco', 0) * item.get('quantidade', 1) for item in carrinho)
    frete = session.get('frete_selecionado_valor', 0)
    total = subtotal + frete
    
    return jsonify({
        'success': True,
        'carrinho': carrinho,
        'subtotal': subtotal,
        'frete': frete,
        'total': total
    })

@app.route("/api/salvar-frete", methods=['POST'])
@login_required
def salvar_frete():
    """Salvar CEP e frete na sessão"""
    data = request.get_json()
    
    if 'cep' in data:
        session['cep_frete'] = data['cep']
    
    if 'frete' in data:
        session['frete_selecionado'] = data['frete'].get('tipo', '')
        session['frete_selecionado_valor'] = data['frete'].get('valor', 0)
    
    session.modified = True
    return jsonify({'success': True})

@app.route("/processar-pedido", methods=['POST'])
@login_required
def processar_pedido():
    """Processar pedido final"""
    try:
        # Dados do formulário
        dados = request.form
        
        # Obter carrinho da sessão
        carrinho = session.get('carrinho', [])
        if not carrinho:
            flash("Carrinho vazio", "error")
            return redirect('/carrinho')
        
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
        
        # Inserir venda
        valor_total = sum(item.get('preco', 0) * item.get('quantidade', 1) for item in carrinho)
        valor_total += float(dados.get('frete_selecionado_valor', 0))
        
        cursor.execute("""
            INSERT INTO vendas (usuario_id, valor_total, forma_pagamento)
            VALUES (%s, %s, %s)
        """, (session['usuario_id'], valor_total, dados.get('forma_pagamento', 'PIX')))
        
        venda_id = cursor.lastrowid
        
        # Inserir endereço da venda
        cursor.execute("""
            INSERT INTO enderecos_venda 
            (venda_id, cep, logradouro, numero, complemento, bairro, cidade, estado, destinatario)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            venda_id,
            dados.get('cep'),
            dados.get('rua'),
            dados.get('numero'),
            dados.get('complemento'),
            dados.get('bairro'),
            dados.get('cidade'),
            dados.get('estado'),
            f"{dados.get('nome')} {dados.get('sobrenome')}"
        ))
        
        # Inserir itens da venda
        for item in carrinho:
            cursor.execute("""
                INSERT INTO itens_venda 
                (venda_id, produto_id, tamanho_id, cor_id, quantidade, preco_unitario)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                venda_id,
                item.get('id'),
                item.get('tamanho_id'),
                item.get('cor_id'),
                item.get('quantidade', 1),
                item.get('preco', 0)
            ))
            
            # Atualizar estoque (se necessário)
            cursor.execute("""
                UPDATE estoque 
                SET quantidade = quantidade - %s
                WHERE produto_id = %s AND tamanho_id = %s AND cor_id = %s
            """, (
                item.get('quantidade', 1),
                item.get('id'),
                item.get('tamanho_id'),
                item.get('cor_id')
            ))
        
        conexao.commit()
        cursor.close()
        conexao.close()
        
        # Limpar carrinho da sessão
        session.pop('carrinho', None)
        session.pop('cep_frete', None)
        session.pop('frete_selecionado', None)
        session.pop('frete_selecionado_valor', None)
        session.modified = True
        
        flash("Pedido realizado com sucesso!", "success")
        return redirect('/usuario')
        
    except Exception as e:
        print(f"Erro ao processar pedido: {e}")
        flash(f"Erro ao processar pedido: {str(e)}", "error")
        return redirect('/checkout')

@app.route("/pagamento")
def checkout_pagamento():

    return render_template("/pages/checkout_pagamento.html")

def salvar_carrinho(data):
    """Salvar carrinho na sessão do servidor"""
    
    if 'carrinho' in data:
        # Limpar IDs antigos para evitar duplicação
        novo_carrinho = []
        
        for item in data['carrinho']:
            # Garantir que o item tem todas as propriedades necessárias
            item_limpo = {
                'id': item.get('id'),
                'nome': item.get('nome', 'Produto sem nome'),
                'preco': float(item.get('preco', 0)),
                'imagem': item.get('imagem', '/static/images/default.png'),
                'tamanho': item.get('tamanho'),
                'cor': item.get('cor'),
                'quantidade': int(item.get('quantidade', 1)),
                'tamanho_id': item.get('tamanho_id') or 1,  # Valor padrão
                'cor_id': item.get('cor_id') or 1  # Valor padrão
            }
            novo_carrinho.append(item_limpo)
        
        session['carrinho'] = novo_carrinho
        session.modified = True
    
    return jsonify({'success': True})

@app.route("/api/carregar-carrinho", methods=['GET'])
@login_required
def carregar_carrinho():
    """Carregar carrinho da sessão do servidor"""
    carrinho = session.get('carrinho', [])
    
    # Se não tem carrinho na sessão, tentar criar um vazio
    if not carrinho:
        session['carrinho'] = []
        carrinho = []
    
    return jsonify({
        'success': True,
        'carrinho': carrinho
    })

@app.route("/api/limpar-carrinho", methods=['POST'])
@login_required
def limpar_carrinho():
    """Limpar carrinho da sessão"""
    session.pop('carrinho', None)
    session.modified = True
    return jsonify({'success': True})

    
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
