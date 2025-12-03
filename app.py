from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify

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

def conectar():
    return mysql.connector.connect(host='localhost', user='root', port='3406', database='crew_magda')

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

@app.route("/produto/<int:id>/destaque", methods=['POST'])
def toggle_destaque(id):
    
    conexao = conectar()
    cursor = conexao.cursor()
    
    try:
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

@app.route("/dashboard")
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
        
        # Vendas últimos 7 dias - CORRIGIDO
        cursor.execute("""
            SELECT DATE(data_venda) as data, COALESCE(SUM(valor_total), 0) as total 
            FROM vendas 
            WHERE data_venda >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(data_venda) 
            ORDER BY data
        """)
        vendas_db = cursor.fetchall()
        
        # Preencher datas faltantes - CORRIGIDO
        datas_completas = []
        datas_labels = []  # Labels formatados para o gráfico
        
        for i in range(7):
            data_alvo = (datetime.now() - timedelta(days=6-i)).date()
            total = 0
            
            # Buscar valor para esta data
            for venda in vendas_db:
                venda_data = venda['data']
                if venda_data == data_alvo:
                    total = float(venda['total'])
                    break
            
            # Formatar data para exibição
            data_formatada = data_alvo.strftime('%d/%m')
            datas_completas.append(total)  # Apenas os valores
            datas_labels.append(data_formatada)  # Labels separados
        
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
        
        # Atividades recentes (vendas) - CORRIGIDO
        cursor.execute("""
            SELECT v.data_venda as data, v.forma_pagamento, v.valor_total as valor
            FROM vendas v
            ORDER BY v.data_venda DESC
            LIMIT 5
        """)
        atividades_recentes_raw = cursor.fetchall()
        
        # Processar atividades para formato adequado
        atividades_recentes = []
        for atividade in atividades_recentes_raw:
            atividades_recentes.append({
                'data': atividade['data'],
                'forma_pagamento': atividade['forma_pagamento'],
                'valor': float(atividade['valor'])
            })

        cursor.close()
        conn.close()

        # Calcular crescimento (exemplo simplificado)
        crescimento = 12.5

        return render_template(
            "/pages/dashboard.html",
            vendas_hoje=float(vendas_hoje),
            total_produtos=total_produtos,
            novos_usuarios=novos_usuarios,
            estoque_baixo=estoque_baixo,
            vendas_7_dias=datas_completas,  # Apenas valores
            vendas_labels=datas_labels,     # Labels separados
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
        
        # Retornar dados de exemplo em caso de erro
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
    
@app.route("/gerenciar_clientes")
def clientes():   
   return render_template("/auth/gerenciar_clientes.html")

@app.route("/estoque")
def estoque():
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)

    # Coletar parâmetros de filtro da URL
    categorias_filtro = request.args.getlist('categoria')
    tamanhos_filtro = request.args.getlist('tamanho')
    cores_filtro = request.args.getlist('cor')
    precos_filtro = request.args.getlist('preco')

    # Query base para produtos ATIVOS
    sql_ativos = """
        SELECT DISTINCT p.id, p.nome, p.preco, p.imagem, p.destaque, p.categoria_id, p.ativo
        FROM produtos p
        WHERE p.ativo = TRUE
    """
    
    # Query base para produtos DESATIVADOS
    sql_desativados = """
        SELECT DISTINCT p.id, p.nome, p.preco, p.imagem, p.destaque, p.categoria_id, p.ativo
        FROM produtos p
        WHERE p.ativo = FALSE
    """
    
    # Função auxiliar para aplicar filtros
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
        
        return sql, local_params

    # Aplicar filtros para ativos e desativados
    sql_ativos_filtrado, params_ativos = aplicar_filtros(sql_ativos, [])
    sql_desativados_filtrado, params_desativados = aplicar_filtros(sql_desativados, [])

    # Executar queries
    cursor.execute(sql_ativos_filtrado, params_ativos)
    produtos_ativos = cursor.fetchall()

    cursor.execute(sql_desativados_filtrado, params_desativados)
    produtos_desativados = cursor.fetchall()

    # Buscar categorias, tamanhos e cores para o filtro
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

@app.route("/novo_produto")
def novo_produto():
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT c.id, c.nome FROM cores c")
    cores = cursor.fetchall()
    cursor.close()
    conexao.close()

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT t.id, t.nome FROM tamanhos t")
    tamanhos = cursor.fetchall()
    cursor.close()
    conexao.close()

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT c.id, c.nome FROM categorias c")
    categorias = cursor.fetchall()
    cursor.close()
    conexao.close()

    return render_template("/pages/novo_produto.html", produtos=produtos, cores=cores, tamanhos=tamanhos, categorias=categorias)

@app.route("/salvar", methods=['POST'])
def salvar_produto():
    nome = request.form.get('nome', '')
    descricao = request.form.get('descricao', '')
    preco = request.form.get('preco', '')
    categoria_id = request.form.get('categoria_id', '')
    destaque = request.form.get('destaque', 'FALSE')
    
    # Receber múltiplos valores como listas
    tamanhos_ids = request.form.getlist('tamanho_id[]')
    cores_ids = request.form.getlist('cor_id[]')
    quantidades = request.form.getlist('quantidade[]')
    
    imagem_file = request.files.get("imagem")
    imagem_nome = None
    
    if imagem_file and imagem_file.filename != "":
        imagem_nome = secure_filename(imagem_file.filename)
        imagem_file.save(os.path.join(app.config["UPLOAD_FOLDER"], imagem_nome))

    if nome.strip() == "":
        return "Erro: O nome não pode ser vazio.", 400
    if descricao.strip() == "":
        return "Erro: A descrição não pode ser vazia.", 400
    if not tamanhos_ids or not cores_ids or not quantidades:
        return "Erro: É necessário informar pelo menos um tamanho, cor e quantidade.", 400

    try:
        preco = float(preco)
        categoria_id = int(categoria_id)
        destaque = True if destaque == 'TRUE' else False
        
        # Converter listas para inteiros
        tamanhos_ids = [int(t) for t in tamanhos_ids]
        cores_ids = [int(c) for c in cores_ids]
        quantidades = [int(q) for q in quantidades]
        
    except ValueError:
        return "Erro: Tipos inválidos (preço/quantidade/ids).", 400

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)

    try:
        # Inserir o produto principal
        sql_produto_ins = """
            INSERT INTO produtos (nome, descricao, preco, categoria_id, imagem, destaque)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql_produto_ins, (nome, descricao, preco, categoria_id, imagem_nome, destaque))
        conexao.commit()
        produto_id = cursor.lastrowid

        # Inserir múltiplos registros no estoque
        sql_estoque_ins = """
            INSERT INTO estoque (produto_id, tamanho_id, cor_id, quantidade)
            VALUES (%s, %s, %s, %s)
        """
        
        # Para cada combinação de tamanho, cor e quantidade
        for i in range(len(tamanhos_ids)):
            cursor.execute(sql_estoque_ins, (produto_id, tamanhos_ids[i], cores_ids[i], quantidades[i]))
        
        conexao.commit()

    except Exception as e:
        conexao.rollback()
        return f"Erro interno: {str(e)}", 500
    finally:
        cursor.close()
        conexao.close()

    return redirect("/estoque")

@app.route("/editar_produto/<int:id>")
def editar_produto(id):
    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
        
        # Buscar cores, tamanhos e categorias
        cursor.execute("SELECT c.id, c.nome FROM cores c")
        cores = cursor.fetchall()
        
        cursor.execute("SELECT t.id, t.nome FROM tamanhos t")
        tamanhos = cursor.fetchall()
        
        cursor.execute("SELECT c.id, c.nome FROM categorias c")
        categorias = cursor.fetchall()
        
        # Buscar produto e TODAS as variações do estoque
        cursor.execute("""
            SELECT p.* 
            FROM produtos p 
            WHERE p.id = %s
        """, (id,))
        produto = cursor.fetchone()
        
        if not produto:
            cursor.close()
            conexao.close()
            return "Produto não encontrado", 404
        
        # Buscar todas as variações do estoque
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
        return f"Erro ao buscar produto: {str(e)}", 500

@app.route("/atualizar/<int:id>", methods=['POST'])
def atualizar_produto(id):
    try:
        nome = request.form["nome"].strip()
        descricao = request.form["descricao"].strip()
        preco = request.form["preco"]
        categoria_id = request.form["categoria_id"]
        destaque = request.form.get('destaque', 'FALSE')
        
        # Receber múltiplos valores como listas
        tamanhos_ids = request.form.getlist('tamanho_id[]')
        cores_ids = request.form.getlist('cor_id[]')
        quantidades = request.form.getlist('quantidade[]')
        estoque_ids = request.form.getlist('estoque_id[]')
        
        if not nome:
            return "Erro: O nome não pode ser vazio.", 400
        if not descricao:
            return "Erro: A descrição não pode ser vazia.", 400
        if not tamanhos_ids or not cores_ids or not quantidades:
            return "Erro: É necessário informar pelo menos um tamanho, cor e quantidade.", 400

        try:
            preco = float(preco)
            categoria_id = int(categoria_id)
            destaque = True if destaque == 'TRUE' else False
            
            # Converter listas para inteiros
            tamanhos_ids = [int(t) for t in tamanhos_ids]
            cores_ids = [int(c) for c in cores_ids]
            quantidades = [int(q) for q in quantidades]
            estoque_ids = [int(e) if e else None for e in estoque_ids]
            
        except ValueError:
            return "Erro: Valores numéricos inválidos.", 400

        imagem_nome = None
        imagem_file = request.files.get("imagem")
        
        if imagem_file and imagem_file.filename != "":
            imagem_nome = secure_filename(imagem_file.filename)
            imagem_file.save(os.path.join(app.config["UPLOAD_FOLDER"], imagem_nome))
        
        conexao = conectar()
        cursor = conexao.cursor()

        try:
            # Atualizar produto
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

            # Primeiro, remover todas as variações existentes
            cursor.execute("DELETE FROM estoque WHERE produto_id = %s", (id,))
            
            # Inserir as novas variações
            sql_estoque = """
                INSERT INTO estoque (id, produto_id, tamanho_id, cor_id, quantidade)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            for i in range(len(tamanhos_ids)):
                # Se estoque_id existe (atualização), senão None (novo)
                estoque_id = estoque_ids[i] if i < len(estoque_ids) else None
                cursor.execute(sql_estoque, (estoque_id, id, tamanhos_ids[i], cores_ids[i], quantidades[i]))
            
            conexao.commit()
            cursor.close()
            conexao.close()
            
            return redirect("/produtos")
            
        except Exception as e:
            conexao.rollback()
            raise e
            
    except Exception as e:
        if 'conexao' in locals():
            conexao.rollback()
            conexao.close()
        return f"Erro ao atualizar produto: {str(e)}", 500
    
@app.route("/desativar_produto/<int:id>")
def desativar_produto(id):
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    
    try:
        sql_produto = "UPDATE produtos SET ativo = FALSE WHERE id = %s"
        cursor.execute(sql_produto, (id,))
        
        conexao.commit()
    except Exception as e:
        conexao.rollback()
        return f"Erro ao desativar produto: {str(e)}", 500
    finally:
        cursor.close()
        conexao.close()  
    return redirect("/estoque")

@app.route("/reativar_produto/<int:id>")
def reativar_produto(id):
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    
    try:
        sql_produto = "UPDATE produtos SET ativo = TRUE WHERE id = %s"
        cursor.execute(sql_produto, (id,))
        conexao.commit()
    except Exception as e:
        conexao.rollback()
        return f"Erro ao reativar produto: {str(e)}", 500
    finally:
        cursor.close()
        conexao.close()
    
    return redirect("/estoque")

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

    print(tamanhos)
    print(cores)

    cursor.close()
    conexao.close()

    print(cores)
    print(tamanhos)
    
    if produto:
        return render_template("/pages/visualizacao.html", produto=produto, produtos_relacionados=produtos_relacionados, cores=cores, tamanhos=tamanhos)
    else:
        return "Produto não encontrado", 404

#CARRINHO

@app.route("/api/carrinho", methods=['GET'])
def get_carrinho():
    # Em uma implementação real, você buscaria do banco de dados
    # Por enquanto, vamos usar session/localStorage no frontend
    return jsonify({"message": "Carrinho gerenciado no frontend"})

@app.route("/api/carrinho/add", methods=['POST'])
def add_to_carrinho():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    
    # Validação básica
    required_fields = ['produto_id', 'nome', 'preco']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Campo obrigatório faltando: {field}"}), 400
    
    # Aqui você poderia adicionar lógica para salvar no banco de dados
    # Para o carrinho baseado em sessão, o frontend gerencia
    
    return jsonify({
        "success": True,
        "message": "Produto adicionado ao carrinho",
        "produto": data
    })

@app.route("/checkout")
def checkout():
    if "usuario_id" not in session:
        flash("Você precisa fazer login para finalizar a compra", "error")
        return redirect("/login")
    
    return render_template("/pages/checkout.html")

@app.route("/api/produto/<int:produto_id>/estoque")
def get_estoque_produto(produto_id):
    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
        
        # Buscar estoque com nomes de tamanho e cor
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

# CADASTRO DE USUÁRIO
    
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
                (nome_completo, email, telefone, cpf, nascimento, senha_hash)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_inserir, (nome_completo, email, telefone, cpf, nascimento, senha_hash))
            conexao.commit()

            usuario_id = cursor.lastrowid

            cursor.close()
            conexao.close()

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

@app.route("/usuario")
def usuario():
    if "usuario_id" not in session:
        flash("Você precisa estar logado para acessar sua conta.", "error")
        return redirect("/login")
    
    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, nome_completo, email, telefone, cpf, nascimento, data_cadastro
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

@app.route("/editar_usuario/<int:usuario_id>", methods=['GET', 'POST'])
def editar_usuario(usuario_id):
    if request.method == 'POST':
        nome_completo = request.form.get('nome_completo', '').strip()
        email = request.form.get('email', '').strip().lower()
        telefone = request.form.get('telefone', '').strip()
        cpf = request.form.get('cpf', '').strip()
        nascimento = request.form.get('nascimento', '')

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
        
        if erros:
            for erro in erros:
                flash(erro, 'error')
            return render_template("auth/usuario.html")

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

            sql_inserir = """
                INSERT INTO usuarios 
                (nome_completo, email, telefone, cpf, nascimento)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql_inserir, (nome_completo, email, telefone, cpf, nascimento))
            conexao.commit()

            usuario_id = cursor.lastrowid

            cursor.close()
            conexao.close()

            session['usuario_id'] = usuario_id
            session['usuario_nome'] = nome_completo
            session['usuario_email'] = email

            flash('Edição realizada com sucesso! Bem-vindo(a) novamente à MAGDA.', 'success')
            return redirect('/usuario')

        except mysql.connector.Error as err:
            flash(f'Erro no banco de dados: {err}', 'error')
            return render_template("auth/editar_usuario.html")
        except Exception as e:
            flash(f'Erro inesperado: {str(e)}', 'error')
            return render_template("auth/editar_usuario.html")
    elif request.method == 'GET':
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
        usuario = cursor.fetchone()
        nome_completo = usuario["nome_completo"]
        email = usuario["email"]
        telefone = usuario["telefone"]
        cpf = usuario["cpf"]
        nascimento = usuario["nascimento"]

        return render_template("auth/editar_usuario.html", nome_completo=nome_completo, cpf=cpf, email=email, telefone=telefone, nascimento=nascimento)
    return render_template("auth/editar_usuario.html")
   
if __name__ == "__main__":
    app.run(debug=True)
