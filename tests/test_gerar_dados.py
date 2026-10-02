import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from gerar_dados import CAMPOS, gerar_linhas  # noqa: E402


def test_quantidade_e_campos():
    linhas = gerar_linhas(100)
    assert len(linhas) == 100
    assert list(linhas[0]) == CAMPOS


def test_reprodutivel():
    assert gerar_linhas(50, seed=1) == gerar_linhas(50, seed=1)


def test_valores_validos():
    for l in gerar_linhas(200):
        assert l["quantidade"] >= 1
        assert l["preco_unitario"] > 0
