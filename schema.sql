-- =============================================================
-- UNIFEOB - Integração de Dados - Desafio OFX
-- Grupo PI: Thales, João Miguel, Matheus, Gabriel, Fernando, Kayky
-- =============================================================

CREATE TABLE IF NOT EXISTS contas (
    id          SERIAL PRIMARY KEY,
    bank_id     VARCHAR(20)  NOT NULL,
    branch_id   VARCHAR(20),
    acct_id     VARCHAR(50)  UNIQUE NOT NULL,
    acct_type   VARCHAR(20),
    moeda       VARCHAR(10)  DEFAULT 'BRL',
    saldo       NUMERIC(15,2),
    saldo_data  TIMESTAMP,
    criado_em   TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS categorias (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(100) UNIQUE NOT NULL,
    tipo        VARCHAR(10)  NOT NULL CHECK (tipo IN ('RECEITA', 'DESPESA')),
    descricao   TEXT
);

CREATE TABLE IF NOT EXISTS lancamentos (
    id               SERIAL PRIMARY KEY,
    conta_id         INTEGER      NOT NULL REFERENCES contas(id),
    fitid            VARCHAR(100) NOT NULL,
    trntype          VARCHAR(20),
    data_lancamento  TIMESTAMP,
    valor            NUMERIC(15,2),
    memo             TEXT,
    categoria_id     INTEGER      REFERENCES categorias(id),
    importado_em     TIMESTAMP    DEFAULT NOW(),
    UNIQUE (conta_id, fitid)
);

-- Categorias padrão
INSERT INTO categorias (nome, tipo, descricao) VALUES
    ('Receita de Clientes',    'RECEITA', 'Pagamentos e recebimentos de clientes'),
    ('Receita de Contratos',   'RECEITA', 'Contratos e projetos'),
    ('Receita PIX',            'RECEITA', 'Recebimentos via PIX'),
    ('Aluguel',                'DESPESA', 'Aluguel de escritório ou imóvel'),
    ('Energia Elétrica',       'DESPESA', 'Conta de energia'),
    ('Internet / Telefonia',   'DESPESA', 'Internet e telefone empresarial'),
    ('Folha de Pagamento',     'DESPESA', 'Salários e encargos trabalhistas'),
    ('Material de Escritório', 'DESPESA', 'Materiais e suprimentos de escritório'),
    ('Material de Limpeza',    'DESPESA', 'Materiais de limpeza e higiene'),
    ('Equipamentos TI',        'DESPESA', 'Compra de equipamentos e tecnologia'),
    ('Manutenção',             'DESPESA', 'Manutenção de veículos e ativos'),
    ('Serviços Cloud',         'DESPESA', 'Assinaturas de serviços digitais e cloud'),
    ('Estacionamento',         'DESPESA', 'Estacionamento e mobilidade'),
    ('Outros',                 'DESPESA', 'Despesas diversas não classificadas')
ON CONFLICT (nome) DO NOTHING;
