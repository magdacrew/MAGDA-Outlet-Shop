from flask import Flask, render_template, request, redirect
import mysql.connector

app = Flask(__name__)

def conectar():
    return mysql.connector.connect(host='localhost', user='root', password='', port='3406', database='madga_crew')

@app.route("/")
def home():
    return render_template("/pages/index.html")

@app.route("/cadastro")
def cadastro():
    return render_template("auth/cadastro.html")

@app.route("/login")
def login():
    return render_template("auth/login.html")

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
        SELECT p.id, p.nome, p.preco, p.imagem
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

@app.route("/usuario")
def usuario():
    return render_template("/auth/usuario.html")

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
    imagem = request.form.get('imagem', '')

    if nome.strip() == "":
        return "Erro: O nome não pode ser vazio.", 400
    if descricao.strip() == "":
        return "Erro: A descrição não pode ser vazia.", 400
    if categoria_id.strip() == "" or tamanho_id.strip() == "" or cor_id.strip() == "" or quantidade.strip() == "":
        return "Erro: Campos obrigatórios em branco.", 400

    try:
        preco = float(preco)
        quantidade = int(quantidade)
        categoria_id = int(categoria_id)
        tamanho_id = int(tamanho_id)
        cor_id = int(cor_id)
    except ValueError:
        return "Erro: Tipos inválidos (preço/quantidade/ids).", 400

    if preco <= 0:
        return "Erro: O preço deve ser maior que zero.", 400
    if quantidade < 0:
        return "Erro: A quantidade não pode ser negativa.", 400

    nome_norm = nome.strip().lower()

    conexao = conectar()
    cursor = conexao.cursor()

    try:
        sql_produto_sel = "SELECT id, nome FROM produtos WHERE LOWER(TRIM(nome)) = %s LIMIT 1"
        cursor.execute(sql_produto_sel, (nome_norm,))
        row = cursor.fetchone()

        if row:
            produto_id = row[0]
        else:
            sql_produto_ins = """
                INSERT INTO produtos (nome, descricao, preco, categoria_id, imagem)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql_produto_ins, (nome.strip(), descricao.strip(), preco, categoria_id, imagem))
            conexao.commit()  
            produto_id = getattr(cursor, 'lastrowid', None)
            if not produto_id:
                cursor.execute("SELECT id FROM produtos WHERE nome = %s ORDER BY id DESC LIMIT 1", (nome.strip(),))
                produto_id = cursor.fetchone()[0]

        sql_verifica_estoque = """
            SELECT id FROM estoque
            WHERE produto_id = %s AND tamanho_id = %s AND cor_id = %s
            LIMIT 1
        """
        cursor.execute(sql_verifica_estoque, (produto_id, tamanho_id, cor_id))
        if cursor.fetchone():
            return "Erro: Já existe este produto com a mesma cor e tamanho no estoque.", 400


        sql_estoque_ins = """
            INSERT INTO estoque (produto_id, tamanho_id, cor_id, quantidade)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql_estoque_ins, (produto_id, tamanho_id, cor_id, quantidade))
        conexao.commit()

    except Exception as e:
        try:
            conexao.rollback()
        except:
            pass
        print("Erro ao salvar produto/estoque:", e)
        return f"Erro interno: {str(e)}", 500
    finally:
        try:
            cursor.close()
            conexao.close()
        except:
            pass

    return redirect("/produtos")

@app.route("/editar_produto/<int:id>")
def editar_produto(id):
    conexao = mysql.connector.connect()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT * FROM produtos WHERE id = %s", (id,))
    produto = cursor.fetchone()
    cursor.close()
    conexao.close()
    return render_template("/pages/editar_produto.html", produto=produto)
    
@app.route("/atualizar/<int:id>", methods=['POST'])
def atualizar_produto(id):
    conexao = conectar()
    cursor = conexao.cursor()
    nome = request.form["nome"]
    descricao = request.form["descricao"]
    preco = request.form["preco"]
    categoria_id = request.form["categoria_id"]

    conexao = mysql.connector.connect()
    cursor = conectar.cursor()
    sql = "UPDATE produtos SET nome = %s, descricao = %s, preco = %s, categoria_id = %s WHERE id = %s"
    cursor.execute(sql, (nome, descricao, preco, categoria_id, id))
    conexao.commit()
    cursor.close()
    conexao.close()
    
    return redirect("/produtos")

if __name__ == "__main__":
    app.run(debug=True)
