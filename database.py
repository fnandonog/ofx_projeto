"""
Módulo de acesso ao banco de dados PostgreSQL.
"""

import os
import psycopg2
import psycopg2.extras


def get_connection():
    return psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=int(os.environ.get('DB_PORT', 5432)),
        dbname=os.environ.get('DB_NAME', 'ofx_db'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'postgres'),
    )


def init_db():
    """Cria as tabelas se não existirem e insere categorias padrão."""
    schema = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema, 'r', encoding='utf-8') as f:
        sql = f.read()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()


def salvar_extrato(extrato):
    """
    Persiste conta e lançamentos no banco.
    Retorna (importados, duplicatas).
    """
    from ofx_parser import Extrato
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO contas (bank_id, branch_id, acct_id, acct_type, moeda, saldo, saldo_data)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (acct_id) DO UPDATE SET
            saldo      = EXCLUDED.saldo,
            saldo_data = EXCLUDED.saldo_data
        RETURNING id
    """, (
        extrato.conta.bank_id, extrato.conta.branch_id,
        extrato.conta.acct_id, extrato.conta.acct_type,
        extrato.moeda, extrato.saldo, extrato.saldo_data,
    ))
    conta_id = cur.fetchone()[0]

    importados = 0
    duplicatas = 0
    for t in extrato.lancamentos:
        cur.execute("""
            INSERT INTO lancamentos (conta_id, fitid, trntype, data_lancamento, valor, memo)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (conta_id, fitid) DO NOTHING
        """, (conta_id, t.fitid, t.trntype, t.dtposted, t.trnamt, t.memo))
        if cur.rowcount:
            importados += 1
        else:
            duplicatas += 1

    conn.commit()
    cur.close()
    conn.close()
    return importados, duplicatas


def listar_lancamentos(apenas_sem_categoria=False):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    filtro = "WHERE l.categoria_id IS NULL" if apenas_sem_categoria else ""
    cur.execute(f"""
        SELECT l.id, l.fitid, l.trntype, l.data_lancamento, l.valor, l.memo,
               l.categoria_id, cat.nome AS categoria_nome, cat.tipo AS categoria_tipo,
               ct.acct_id, l.importado_em
        FROM lancamentos l
        JOIN contas ct ON ct.id = l.conta_id
        LEFT JOIN categorias cat ON cat.id = l.categoria_id
        {filtro}
        ORDER BY l.data_lancamento DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def listar_categorias():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM categorias ORDER BY tipo, nome")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def classificar(lancamento_id: int, categoria_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE lancamentos SET categoria_id = %s WHERE id = %s",
                (categoria_id, lancamento_id))
    conn.commit()
    cur.close()
    conn.close()


def resumo():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT COUNT(*) AS total FROM lancamentos")
    total = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) AS sem FROM lancamentos WHERE categoria_id IS NULL")
    sem_cat = cur.fetchone()['sem']
    cur.execute("SELECT COALESCE(SUM(valor),0) AS v FROM lancamentos WHERE valor > 0")
    receitas = float(cur.fetchone()['v'])
    cur.execute("SELECT COALESCE(SUM(ABS(valor)),0) AS v FROM lancamentos WHERE valor < 0")
    despesas = float(cur.fetchone()['v'])
    cur.close()
    conn.close()
    return {'total': total, 'sem_categoria': sem_cat,
            'receitas': receitas, 'despesas': despesas}


def relatorio_por_categoria():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT cat.nome, cat.tipo, COUNT(*) AS qtd, SUM(l.valor) AS total
        FROM lancamentos l
        JOIN categorias cat ON cat.id = l.categoria_id
        GROUP BY cat.id, cat.nome, cat.tipo
        ORDER BY cat.tipo, total DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
