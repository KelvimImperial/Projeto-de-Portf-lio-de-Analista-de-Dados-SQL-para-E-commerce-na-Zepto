/*Primeiro Passo: devemos veridicar se ja existe uma tabela chamada zepto, caso existir
devemos elimina-la Está é uma boa pratica */

DROP TABLE IF EXISTS zepto
--TRUNCATE public.zepto RESTART IDENTITY;
/*
 Segundo passo: Os nossos dados estão em um arquivo excel, primeiramente oque faremos é criar uma tabela na minha base de dados
onde armazenaremos os nossos dados
*/

CREATE TABLE zepto(
sku_id SERIAL PRIMARY KEY,--O sku_id é o meu identificador ou seja o meu ID e ela será a chave primaria, O SERIAL:O que ele faz: Ele instrui o banco de dados a criar automaticamente uma sequência numérica (um contador) e usar esse contador para preencher os valores da coluna.Em termos simples: SERIAL é uma maneira eficiente de criar uma coluna que se auto-incrementa. Sempre que você insere um novo registro na tabela, o banco de dados garante que a próxima linha receberá um número sequencial automaticamente (1, 2, 3, 4...).
categoria VARCHAR(120),
nome VARCHAR(150) NOT NULL,--O NOT NULL estamos garantindo que a coluna nome não seja Nula
precoMaximo NUMERIC(8,2),
percentualDesconto NUMERIC(5,2),
quantidadeDisponivel INTEGER,
precoComDesconto NUMERIC(8,2),
pesoEmGramas INTEGER,
foraDeEstoque BOOLEAN,
quantidade INTEGER
);

-- DATA EXPLORATION

--Vamos ver se todos as linhas foram importados
SELECT COUNT(*)

FROM zepto;

-- Visualizando os dados
SELECT *
FROM zepto
LIMIT 10;

-- Agora Vamos Procurar valores nulos

SELECT *
FROM zepto
WHERE nome IS NULL 
OR 
precomaximo IS NULL
OR
percentualdesconto IS NULL 
OR 
quantidadedisponivel IS NULL 
OR 
precocomdesconto IS NULL 
OR 
pesoemgramas IS NULL 
OR 
foradeestoque IS NULL 
OR 
quantidade IS NULL ;

--Vamos ver os diferentes produtos por categorias
SELECT DISTINCT categoria
FROM zepto
ORDER BY categoria

--Vendo quantos produtos estão em estoque e quantos estão faltando
SELECT foradeestoque, COUNT(sku_id)
FROM zepto
GROUP BY foradeestoque

--Verificando quais nomes de produtos aparecem mais de uma vez
SELECT nome, COUNT(sku_id) AS "unidade de manutencao de estoque"
FROM zepto
GROUP BY nome
HAVING COUNT(sku_id) > 1
ORDER BY COUNT(sku_id) DESC;

--LIMPEZA DOS DADOS


--Vamos verificar se há um produto cuja o preço e o preco com desconto  é zero
SELECT *
FROM zepto
WHERE precomaximo=0 OR precocomdesconto=0;

--Excluindo a linha com produto cuja o preco e o preco com desconto é zero

DELETE FROM zepto
WHERE precomaximo=0;

--Converter rupees em kwanza
/*UPDATE zepto
SET precomaximo = precomaximo/100.0,
precocomdesconto = precocomdesconto/100.0;

SELECT precomaximo, precocomdesconto
FROM zepto*/
UPDATE zepto
SET precomaximo = (precomaximo / 100.0) * 10.66,
    precocomdesconto = (precocomdesconto / 100.0) * 10.66;

SELECT precomaximo, precocomdesconto
FROM zepto;

/*Agora que exploramos os dados e limpamos os dados é Hora de começarmos a responder
algumas perguntas de negocios e usar SQL para descobrirmos informacões valiosas */

--Perguntas De Negocios

--1 - Encontre os 10 produtos com melhor custo-benefício com base na porcentagem de desconto.

SELECT DISTINCT nome, precomaximo, percentualdesconto
FROM zepto
ORDER BY percentualdesconto DESC
LIMIT 10;

--2 - Quais são os produtos com alto MRP (Preço de Varejo Máximo) mas fora de estoque?

SELECT DISTINCT nome, precomaximo
FROM zepto
WHERE foradeestoque = true AND precomaximo > 300
ORDER BY precomaximo DESC;
--3 - Calcule a receita estimada para cada categoria.

SELECT categoria,
SUM(precocomdesconto * quantidadedisponivel) AS receita_total
FROM zepto
GROUP BY categoria
ORDER BY receita_total;
--4 - Encontre todos os produtos onde o precomaximo é maior que 500 e o desconto é menor que 10%.

SELECT DISTINCT nome, precomaximo, percentualdesconto
FROM zepto
WHERE precomaximo > 500 AND percentualdesconto < 10
ORDER BY precomaximo DESC, percentualdesconto DESC
--5 - Identifique as 5 categorias que oferecem a maior porcentagem média de desconto.

SELECT categoria,
ROUND(AVG(percentualdesconto), 2) AS desconto_medio
FROM  zepto
GROUP BY categoria
ORDER BY desconto_medio DESC
LIMIT 5;
--6 - Encontre o preço por grama para produtos acima de 100g e ordene pelo melhor custo-benefício (melhor valor).
SELECT DISTINCT nome, pesoemgramas, precocomdesconto,
ROUND(precocomdesconto/pesoemgramas,2) AS preco_por_grama
FROM zepto
WHERE pesoemgramas >=100
ORDER BY preco_por_grama;

--7 - Agrupe os produtos em categorias como baixo, médio, alto.
SELECT DISTINCT nome, pesoemgramas,
CASE WHEN pesoemgramas < 1000 THEN 'BAIXO'
	WHEN pesoemgramas < 5000 THEN 'MEDIO'
	ELSE 'ALTO' 
	END AS peso_por_categoria
FROM zepto
ORDER BY pesoemgramas;

--8 - Qual é o peso total do estoque por categoria?
SELECT categoria,
SUM(pesoemgramas * quantidadedisponivel) AS peso_total
FROM zepto
GROUP BY categoria
ORDER BY peso_total;