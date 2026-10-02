-- Receita por região no 1º trimestre de 2024 (usa partições ano/mes para ler menos dados)
SELECT regiao,
       ROUND(SUM(valor_total), 2) AS receita
FROM vendas
WHERE ano = 2024
  AND mes BETWEEN 1 AND 3
GROUP BY regiao
ORDER BY receita DESC;
