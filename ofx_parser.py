"""
Parser para arquivos OFX/SGML (Open Financial Exchange).
Suporta tanto o formato SGML (versão 1.x) quanto XML (versão 2.x).
"""

import re
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Conta:
    bank_id: str
    branch_id: str
    acct_id: str
    acct_type: str


@dataclass
class Lancamento:
    trntype: str
    dtposted: datetime
    trnamt: float
    fitid: str
    memo: str


@dataclass
class Extrato:
    moeda: str
    conta: Conta
    dtstart: datetime
    dtend: datetime
    lancamentos: List[Lancamento] = field(default_factory=list)
    saldo: float = 0.0
    saldo_data: Optional[datetime] = None


def _parse_data(s: str) -> datetime:
    s = s.strip()[:14]
    try:
        if len(s) >= 14:
            return datetime.strptime(s[:14], '%Y%m%d%H%M%S')
        return datetime.strptime(s[:8], '%Y%m%d')
    except ValueError:
        return datetime.now()


def _tag_valor(conteudo: str, tag: str) -> Optional[str]:
    match = re.search(rf'<{tag}>\s*([^\n<]+)', conteudo, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _parse_lancamentos(conteudo: str) -> List[Lancamento]:
    resultado = []
    for m in re.finditer(r'<STMTTRN>(.*?)</STMTTRN>', conteudo, re.DOTALL | re.IGNORECASE):
        bloco = m.group(1)
        trntype  = _tag_valor(bloco, 'TRNTYPE') or 'OTHER'
        dtposted = _parse_data(_tag_valor(bloco, 'DTPOSTED') or '19700101')
        fitid    = _tag_valor(bloco, 'FITID') or ''
        memo     = _tag_valor(bloco, 'MEMO') or ''
        try:
            trnamt = float(_tag_valor(bloco, 'TRNAMT') or '0')
        except ValueError:
            trnamt = 0.0
        resultado.append(Lancamento(trntype, dtposted, trnamt, fitid, memo))
    return resultado


def parse_ofx(conteudo: str) -> Extrato:
    moeda     = _tag_valor(conteudo, 'CURDEF') or 'BRL'
    bank_id   = _tag_valor(conteudo, 'BANKID') or ''
    branch_id = _tag_valor(conteudo, 'BRANCHID') or ''
    acct_id   = _tag_valor(conteudo, 'ACCTID') or ''
    acct_type = _tag_valor(conteudo, 'ACCTTYPE') or ''
    conta = Conta(bank_id, branch_id, acct_id, acct_type)

    dtstart = _parse_data(_tag_valor(conteudo, 'DTSTART') or '19700101')
    dtend   = _parse_data(_tag_valor(conteudo, 'DTEND')   or '19700101')

    lancamentos = _parse_lancamentos(conteudo)

    try:
        saldo = float(_tag_valor(conteudo, 'BALAMT') or '0')
    except ValueError:
        saldo = 0.0
    saldo_data = _parse_data(_tag_valor(conteudo, 'DTASOF') or '19700101')

    return Extrato(moeda, conta, dtstart, dtend, lancamentos, saldo, saldo_data)
