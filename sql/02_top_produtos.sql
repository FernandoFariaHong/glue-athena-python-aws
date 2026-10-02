-- Ranking de produtos por receita
SELECT produto,
       SUM(quantidade)              AS itens_vendidos,
       ROUND(SUM(valor_total), 2)   AS receita,
       ROUND(AVG(preco_unitario), 2) AS preco_medio
FROM vendas
GROUP BY produto
ORDER BY receita DESC;
