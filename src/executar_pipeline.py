"""Executa o pipeline: Glue Job (CSV -> Parquet) e depois o Crawler (cataloga a tabela)."""
import time

import boto3

import config as c

glue = boto3.client("glue", region_name=c.REGION)
INTERVALO = 15  # segundos entre consultas de status


def rodar_job() -> None:
    run_id = glue.start_job_run(JobName=c.JOB_NAME)["JobRunId"]
    print(f"Job iniciado: {run_id}")
    while True:
        run = glue.get_job_run(JobName=c.JOB_NAME, RunId=run_id)["JobRun"]
        estado = run["JobRunState"]
        print(f"  job: {estado}")
        if estado == "SUCCEEDED":
            return
        if estado in ("FAILED", "ERROR", "TIMEOUT", "STOPPED"):
            raise SystemExit(f"Job terminou em {estado}: {run.get('ErrorMessage', '')}")
        time.sleep(INTERVALO)


def rodar_crawler() -> None:
    glue.start_crawler(Name=c.CRAWLER_NAME)
    print("Crawler iniciado")
    while True:
        estado = glue.get_crawler(Name=c.CRAWLER_NAME)["Crawler"]["State"]
        print(f"  crawler: {estado}")
        if estado == "READY":
            return
        time.sleep(INTERVALO)


def main() -> None:
    rodar_job()
    rodar_crawler()
    print(f"\nPronto! Tabela disponível em {c.DATABASE}.vendas. Próximo: python src/consultar_athena.py")


if __name__ == "__main__":
    main()
