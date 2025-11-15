from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/Cadastro")
def cadastro():
    return render_template("cadastro.html")

@app.route("/Login")
def login():
    return render_template("login.html")

@app.route("/about")
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

if __name__ == "__main__":
    app.run(debug=True)