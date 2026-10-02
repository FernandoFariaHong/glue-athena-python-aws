"""Gera um CSV de vendas fictícias em data/vendas.csv (reprodutível via seed)."""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

PRODUTOS = {
    "Notebook": 3500.00,
    "Mouse": 80.00,
    "Teclado": 150.00,
    "Monitor": 900.00,
    "Headset": 220.00,
    "Webcam": 180.00,
}
REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
CAMPOS = ["id_venda", "data_venda", "produto", "regiao", "quantidade", "preco_unitario"]


def gerar_linhas(n: int = 5000, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    inicio = date(2024, 1, 1)
    linhas = []
    for i in range(1, n + 1):
        produto = rng.choice(list(PRODUTOS))
        linhas.append(
            {
                "id_venda": i,
                "data_venda": (inicio + timedelta(days=rng.randint(0, 364))).isoformat(),
                "produto": produto,
                "regiao": rng.choice(REGIOES),
                "quantidade": rng.randint(1, 5),
                "preco_unitario": round(PRODUTOS[produto] * rng.uniform(0.9, 1.1), 2),
            }
        )
    return linhas


def main(destino: Path = Path("data/vendas.csv")) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    linhas = gerar_linhas()
    with destino.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS)
        writer.writeheader()
        writer.writerows(linhas)
    print(f"{len(linhas)} linhas gravadas em {destino}")


if __name__ == "__main__":
    main()
