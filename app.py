from flask import Flask, render_template, request, redirect
import mysql.connector

app = Flask(__name__)

def conectar():
    return mysql.connector.connect(host='localhost', user='root', password='', port='3406', database='madga_crew')

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/cadastro")
def cadastro():
    return render_template("auth/cadastro.html")

@app.route("/login")
def login():
    return render_template("auth/login.html")

@app.route("/sobre")
def about():
    return render_template("sobre.html")

@app.route("/contato")
def contato():
    return render_template("contato.html")

@app.route("/produtos")
def produtos():
    return render_template("produtos.html")

@app.route("/carrinho")
def carrinho():
    return render_template("carrinho.html")

@app.route("/usuario")
def usuario():
    return render_template("usuario.html")

@app.route("/novo_produto")
def novo_produto():
    return render_template("novo_produto.html")

@app.route("/salvar", methods=['POST'])
def salvar_produto():
    nome = request.form['nome']
    descricao = request.form['descricao']
    preco = request.form['preco']
    categoria_id = request.form['categoria_id']

    if preco <= 0:
        return "Erro: O preço deve ser maior que zero.", 400
    
    if nome == '':
        return "Erro: O nome não pode ser vazio.", 400


    conexao = conectar()
    cursor = conexao.cursor()
    sql_produto = "INSERT INTO produtos (nome, descricao, preco, categoria_id) VALUES (%s, %s, %s, %s)"
    valores_produto = (nome, descricao, preco, categoria_id)
    cursor.execute(sql_produto, valores_produto)
    conexao.commit()
    
    tamanho_id = request.form['tamanho_id']
    cor_id = request.form['cor_id']
    quantidade = request.form['quantidade']

    produto_id = cursor.lastrowid
    sql_estoque = "INSERT INTO estoque (produto_id, tamanho_id, cor_id ,quantidade) VALUES (%s, %s, %s, %s)"
    valores_estoque = (produto_id, tamanho_id, cor_id, quantidade)
    cursor.execute(sql_estoque, valores_estoque)
    conexao.commit()

    return redirect("/produtos")

if __name__ == "__main__":
    app.run(debug=True)