"""
UNIFEOB - Integração de Dados - Desafio OFX
Aplicação Flask para importação, armazenamento e classificação de extratos OFX.

Grupo PI:
  RA 25000071 - Thales Vasconcellos Tardelli Sabbag de Paula
  RA 25001039 - João Miguel da Silva Calvacante
  RA 25001528 - Matheus Barrense Mendes dos Santos
  RA 25000700 - Gabriel Henrique Sartório
  RA 25000171 - Fernando Nogueira da Silva
  RA 25000079 - Kayky Juan Tavares dos Reis
"""

import os
from flask import (Flask, render_template, request, redirect,
                   url_for, flash, jsonify)
from werkzeug.utils import secure_filename

from ofx_parser import parse_ofx
import database as db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'unifeob-pi-ofx-2026')

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'ofx', 'qfx'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    stats = db.resumo()
    lancamentos = db.listar_lancamentos()
    return render_template('index.html', stats=stats, lancamentos=lancamentos)


# ---------------------------------------------------------------------------
# Upload de arquivo OFX
# ---------------------------------------------------------------------------

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'arquivo' not in request.files:
            flash('Nenhum arquivo enviado.', 'danger')
            return redirect(request.url)

        arquivo = request.files['arquivo']
        if arquivo.filename == '':
            flash('Selecione um arquivo .ofx.', 'danger')
            return redirect(request.url)

        if not allowed_file(arquivo.filename):
            flash('Tipo não suportado. Envie um arquivo .ofx ou .qfx.', 'danger')
            return redirect(request.url)

        nome = secure_filename(arquivo.filename)
        caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome)
        arquivo.save(caminho)

        try:
            with open(caminho, 'r', encoding='latin-1', errors='replace') as f:
                conteudo = f.read()

            extrato = parse_ofx(conteudo)
            if not extrato.lancamentos:
                flash('Nenhum lançamento encontrado no arquivo.', 'warning')
                return redirect(request.url)

            importados, duplicatas = db.salvar_extrato(extrato)
            flash(
                f'Importação concluída! '
                f'{importados} novo(s) lançamento(s) | {duplicatas} duplicata(s) ignorada(s).',
                'success',
            )
            return redirect(url_for('index'))

        except Exception as e:
            flash(f'Erro ao processar o arquivo: {e}', 'danger')
            return redirect(request.url)

    return render_template('upload.html')


# ---------------------------------------------------------------------------
# Classificação de lançamentos
# ---------------------------------------------------------------------------

@app.route('/classificar')
def classificar():
    pendentes   = db.listar_lancamentos(apenas_sem_categoria=True)
    categorias  = db.listar_categorias()
    todos       = db.listar_lancamentos()
    return render_template('classificar.html',
                           pendentes=pendentes,
                           categorias=categorias,
                           todos=todos)


@app.route('/classificar/<int:lancamento_id>', methods=['POST'])
def classificar_post(lancamento_id):
    categoria_id = request.form.get('categoria_id')
    if categoria_id:
        db.classificar(lancamento_id, int(categoria_id))
        flash('Lançamento classificado com sucesso.', 'success')
    return redirect(url_for('classificar'))


@app.route('/api/classificar/<int:lancamento_id>', methods=['POST'])
def api_classificar(lancamento_id):
    """Endpoint JSON para classificação via AJAX."""
    data = request.get_json(silent=True) or {}
    categoria_id = data.get('categoria_id')
    if not categoria_id:
        return jsonify({'erro': 'categoria_id obrigatório'}), 400
    db.classificar(lancamento_id, int(categoria_id))
    return jsonify({'ok': True})


# ---------------------------------------------------------------------------
# Relatório
# ---------------------------------------------------------------------------

@app.route('/relatorio')
def relatorio():
    dados = db.relatorio_por_categoria()
    return render_template('relatorio.html', dados=dados)


# ---------------------------------------------------------------------------
# Inicialização
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    db.init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
