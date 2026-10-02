"""Glue Job (PySpark): CSV bruto -> Parquet particionado por ano/mes.

Executa dentro do AWS Glue, não localmente.
Argumentos: --RAW_PATH  s3://.../raw/vendas/
            --CURATED_PATH s3://.../curated/vendas/
"""
import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F

args = getResolvedOptions(sys.argv, ["JOB_NAME", "RAW_PATH", "CURATED_PATH"])

sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session
job = Job(glue_context)
job.init(args["JOB_NAME"], args)

# 1. Extract: lê o CSV bruto
bruto = spark.read.option("header", True).csv(args["RAW_PATH"])

# 2. Transform: tipagem, limpeza, coluna derivada e colunas de partição
tratado = (
    bruto.select(
        F.col("id_venda").cast("int"),
        F.to_date("data_venda").alias("data_venda"),
        F.initcap(F.trim("produto")).alias("produto"),
        F.trim("regiao").alias("regiao"),
        F.col("quantidade").cast("int"),
        F.col("preco_unitario").cast("double"),
    )
    .dropna()
    .dropDuplicates(["id_venda"])
    .filter((F.col("quantidade") > 0) & (F.col("preco_unitario") > 0))
    .withColumn("valor_total", F.round(F.col("quantidade") * F.col("preco_unitario"), 2))
    .withColumn("ano", F.year("data_venda"))
    .withColumn("mes", F.month("data_venda"))
)

# 3. Load: Parquet particionado (barato de consultar no Athena)
(
    tratado.write.mode("overwrite")
    .partitionBy("ano", "mes")
    .parquet(args["CURATED_PATH"])
)

job.commit()
