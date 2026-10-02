-- Receita e volume de vendas por mês (filtra partições: barato no Athena)
SELECT ano,
       mes,
       COUNT(*)                     AS vendas,
       SUM(quantidade)              AS itens,
       ROUND(SUM(valor_total), 2)   AS receita
FROM vendas
GROUP BY ano, mes
ORDER BY ano, mes;
