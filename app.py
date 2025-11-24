from flask import Flask, render_template, request, redirect, session, flash, url_for

import mysql.connector
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'MAGDA_GAE'

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def conectar():
    return mysql.connector.connect(host='localhost', user='root', password='', port='3406', database='madga_crew')

@app.route("/")
def home():
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)

    sql = """
        SELECT p.id, p.nome, p.preco, p.imagem
        FROM produtos p
        WHERE p.destaque = TRUE
    """
    cursor.execute(sql)
    produtos_destaque = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template("/pages/index.html", produtos_destaque=produtos_destaque)

@app.route("/cadastro", methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
         # Coletar dados do formulário
        nome_completo = request.form.get('nome_completo', '').strip()
        email = request.form.get('email', '').strip().lower()
        telefone = request.form.get('telefone', '').strip()
        cpf = request.form.get('cpf', '').strip()
        nascimento = request.form.get('nascimento', '')
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar', '')

        # Validações
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
            # Verificar se é maior de 18 anos
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

            # Verificar se email já existe
            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
            if cursor.fetchone():
                flash('Este e-mail já está cadastrado.', 'error')
                return render_template("auth/cadastro.html")

            # Verificar se CPF já existe
            cursor.execute("SELECT id FROM usuarios WHERE cpf = %s", (cpf,))
            if cursor.fetchone():
                flash('Este CPF já está cadastrado.', 'error')
                return render_template("auth/cadastro.html")

            # Hash da senha
            senha_hash = generate_password_hash(senha)

            # Inserir usuário
            sql_inserir = """
                INSERT INTO usuarios 
                (nome_completo, email, telefone, cpf, nascimento, senha_hash)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_inserir, (nome_completo, email, telefone, cpf, nascimento, senha_hash))
            conexao.commit()

            # Obter o ID do usuário recém-criado
            usuario_id = cursor.lastrowid

            cursor.close()
            conexao.close()

            # Auto-login após cadastro
            session['usuario_id'] = usuario_id
            session['usuario_nome'] = nome_completo
            session['usuario_email'] = email

            flash('Cadastro realizado com sucesso! Bem-vindo(a) à MAGDA.', 'success')
            return redirect('/usuario')

        except mysql.connector.Error as err:
            flash(f'Erro no banco de dados: {err}', 'error')
            return render_template("auth/cadastro.html")
        except Exception as e:
            flash(f'Erro inesperado: {str(e)}', 'error')
            return render_template("auth/cadastro.html")
             # GET request - apenas mostrar o formulário
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

            # Buscar usuário pelo email
            cursor.execute("""
                SELECT id, nome_completo, email, senha_hash 
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

# ... (mantenha as outras rotas)

@app.route("/usuario")
def usuario():
    return render_template("/auth/usuario.html")

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

    sql = """
        SELECT p.id, p.nome, p.preco, p.imagem, p.destaque
        FROM produtos p
        WHERE p.ativo = TRUE
    """
    cursor.execute(sql)
    produtos = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template("/pages/produtos.html", produtos=produtos)

@app.route("/carrinho")
def carrinho():
    return render_template("/pages/carrinho.html")

@app.route("/novo_produto")
def novo_produto():
    return render_template("/pages/novo_produto.html")

@app.route("/salvar", methods=['POST'])
def salvar_produto():
    nome = request.form.get('nome', '')
    descricao = request.form.get('descricao', '')
    preco = request.form.get('preco', '')
    categoria_id = request.form.get('categoria_id', '')
    tamanho_id = request.form.get('tamanho_id', '')
    cor_id = request.form.get('cor_id', '')
    quantidade = request.form.get('quantidade', '')
    destaque = request.form.get('destaque', 'FALSE')
    
    imagem_file = request.files.get("imagem")
    imagem_nome = None
    
    if imagem_file and imagem_file.filename != "":
        imagem_nome = secure_filename(imagem_file.filename)
        imagem_file.save(os.path.join(app.config["UPLOAD_FOLDER"], imagem_nome))

    if nome.strip() == "":
        return "Erro: O nome não pode ser vazio.", 400
    if descricao.strip() == "":
        return "Erro: A descrição não pode ser vazia.", 400

    try:
        preco = float(preco)
        quantidade = int(quantidade)
        categoria_id = int(categoria_id)
        tamanho_id = int(tamanho_id)
        cor_id = int(cor_id)
        destaque = True if destaque == 'TRUE' else False
    except ValueError:
        return "Erro: Tipos inválidos (preço/quantidade/ids).", 400

    conexao = conectar()
    cursor = conexao.cursor()

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
        cursor.execute(sql_estoque_ins, (produto_id, tamanho_id, cor_id, quantidade))
        conexao.commit()

    except Exception as e:
        conexao.rollback()
        return f"Erro interno: {str(e)}", 500
    finally:
        cursor.close()
        conexao.close()

    return redirect("/produtos")

@app.route("/editar_produto/<int:id>")
def editar_produto(id):
    try:
        conexao = mysql.connector.connect()
        cursor = conexao.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT p.*, e.id as estoque_id, e.tamanho_id, e.cor_id, e.quantidade 
            FROM produtos p 
            LEFT JOIN estoque e ON p.id = e.produto_id 
            WHERE p.id = %s
        """, (id,))
        produto = cursor.fetchone()
        
        cursor.close()
        conexao.close()
        
        if not produto:
            return "Produto não encontrado", 404
            
        return render_template("/pages/editar_produto.html", produto=produto)
        
    except Exception as e:
        return f"Erro ao buscar produto: {str(e)}", 500

@app.route("/atualizar/<int:id>", methods=['POST'])
def atualizar_produto(id):
    try:
        nome = request.form["nome"].strip()
        descricao = request.form["descricao"].strip()
        preco = request.form["preco"]
        categoria_id = request.form["categoria_id"]
        destaque = request.form.get('destaque', 'FALSE')
        
        if not nome:
            return "Erro: O nome não pode ser vazio.", 400
        if not descricao:
            return "Erro: A descrição não pode ser vazia.", 400

        try:
            preco = float(preco)
            categoria_id = int(categoria_id)
            tamanho_id = int(request.form.get('tamanho_id', 0)) or None
            cor_id = int(request.form.get('cor_id', 0)) or None
            quantidade = int(request.form.get('quantidade', 0))
            destaque = True if destaque == 'TRUE' else False
        except ValueError:
            return "Erro: Valores numéricos inválidos.", 400

        imagem_nome = None
        imagem_file = request.files.get("imagem")
        
        if imagem_file and imagem_file.filename != "":
            imagem_nome = secure_filename(imagem_file.filename)
            imagem_file.save(os.path.join(app.config["UPLOAD_FOLDER"], imagem_nome))
        
        conexao = mysql.connector.connect()
        cursor = conexao.cursor()

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

        sql_estoque = "UPDATE estoque SET tamanho_id = %s, cor_id = %s, quantidade = %s WHERE produto_id = %s"
        cursor.execute(sql_estoque, (tamanho_id, cor_id, quantidade, id))

        if cursor.rowcount == 0:
            return "Erro: Registro de estoque não encontrado para este produto", 404

        conexao.commit()
        cursor.close()
        conexao.close()
        
        return redirect("/produtos")
        
    except Exception as e:
        if 'conexao' in locals():
            conexao.rollback()
            conexao.close()
        return f"Erro ao atualizar produto: {str(e)}", 500
    
@app.route("/produto/<int:id>/destaque", methods=['POST'])
def toggle_destaque(id):
    # Verificar se é admin (implemente sua lógica de autenticação)
    # if not session.get('admin'):
    #     return redirect('/login')
    
    conexao = conectar()
    cursor = conexao.cursor()
    
    try:
        # Alternar o status de destaque
        sql = "UPDATE produtos SET destaque = NOT destaque WHERE id = %s"
        cursor.execute(sql, (id,))
        conexao.commit()
    except Exception as e:
        conexao.rollback()
        return f"Erro: {str(e)}", 500
    finally:
        cursor.close()
        conexao.close()
    
    return redirect("/produtos")

if __name__ == "__main__":
    app.run(debug=True)
