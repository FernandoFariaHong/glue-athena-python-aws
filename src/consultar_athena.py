"""Executa as consultas de sql/*.sql no Athena e imprime os resultados.

Uso:
    python src/consultar_athena.py              # roda todos os arquivos .sql
    python src/consultar_athena.py 02_top_produtos.sql
"""
import sys
import time
from pathlib import Path

import boto3

import config as c

athena = boto3.client("athena", region_name=c.REGION)
SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def executar(sql: str) -> list[list[str]]:
    qid = athena.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={"Database": c.DATABASE},
        ResultConfiguration={"OutputLocation": c.s3_uri(c.ATHENA_PREFIX)},
    )["QueryExecutionId"]

    while True:
        status = athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]["Status"]
        if status["State"] == "SUCCEEDED":
            break
        if status["State"] in ("FAILED", "CANCELLED"):
            raise RuntimeError(status.get("StateChangeReason", status["State"]))
        time.sleep(1)

    linhas = []
    for pagina in athena.get_paginator("get_query_results").paginate(QueryExecutionId=qid):
        for linha in pagina["ResultSet"]["Rows"]:
            linhas.append([col.get("VarCharValue", "") for col in linha["Data"]])
    return linhas


def imprimir(linhas: list[list[str]]) -> None:
    larguras = [max(len(l[i]) for l in linhas) for i in range(len(linhas[0]))]
    for n, linha in enumerate(linhas):
        print("  " + " | ".join(v.ljust(w) for v, w in zip(linha, larguras)))
        if n == 0:
            print("  " + "-+-".join("-" * w for w in larguras))


def main() -> None:
    arquivos = [SQL_DIR / a for a in sys.argv[1:]] or sorted(SQL_DIR.glob("*.sql"))
    for arquivo in arquivos:
        print(f"\n=== {arquivo.name} ===")
        imprimir(executar(arquivo.read_text(encoding="utf-8")))


if __name__ == "__main__":
    main()
