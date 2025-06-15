%%sql
DROP MATERIALIZED VIEW IF EXISTS estatisticas_voos;
CREATE MATERIALIZED VIEW estatisticas_voos AS
WITH AssentosPorAviao AS (
    SELECT
        no_serie,
        SUM(CASE WHEN prim_classe = TRUE THEN 1 ELSE 0 END) AS total_assentos_1c,
        SUM(CASE WHEN prim_classe = FALSE THEN 1 ELSE 0 END) AS total_assentos_2c
    FROM
        assento
    GROUP BY
        no_serie
),
BilhetesEVendasPorVoo AS (
    SELECT
        voo_id,
        COUNT(CASE WHEN prim_classe = TRUE THEN 1 END) AS passageiros_1c_agg,
        COUNT(CASE WHEN prim_classe = FALSE THEN 1 END) AS passageiros_2c_agg,
        SUM(CASE WHEN prim_classe = TRUE THEN preco ELSE 0 END) AS vendas_1c_agg,
        SUM(CASE WHEN prim_classe = FALSE THEN preco ELSE 0 END) AS vendas_2c_agg
    FROM
        bilhete
    GROUP BY
        voo_id
)
SELECT
    voo.no_serie,
    voo.hora_partida,
    aeroportoPartida.cidade AS cidade_partida,
    aeroportoPartida.pais AS pais_partida,
    aeroportoChegada.cidade AS cidade_chegada,
    aeroportoChegada.pais AS pais_chegada,
    EXTRACT(YEAR FROM voo.hora_partida) AS ano,
    EXTRACT(MONTH FROM voo.hora_partida) AS mes,
    EXTRACT(DAY FROM voo.hora_partida) AS dia_do_mes,
    EXTRACT(DOW FROM voo.hora_partida) AS dia_da_semana,

    COALESCE(bilhetesVoo.passageiros_1c_agg, 0) AS passageiros_1c,
    COALESCE(bilhetesVoo.passageiros_2c_agg, 0) AS passageiros_2c,

    COALESCE(assentosAviao.total_assentos_1c, 0) AS assentos_1c,
    COALESCE(assentosAviao.total_assentos_2c, 0) AS assentos_2c,

    COALESCE(bilhetesVoo.vendas_1c_agg, 0) AS vendas_1c,
    COALESCE(bilhetesVoo.vendas_2c_agg, 0) AS vendas_2c
    
FROM
    voo
JOIN
    aeroporto aeroportoPartida ON voo.partida = aeroportoPartida.codigo 
JOIN
    aeroporto aeroportoChegada ON voo.chegada = aeroportoChegada.codigo
LEFT JOIN
    BilhetesEVendasPorVoo bilhetesVoo ON voo.id = bilhetesVoo.voo_id
LEFT JOIN
    AssentosPorAviao assentosAviao ON voo.no_serie = assentosAviao.no_serie
ORDER BY
    voo.hora_partida DESC;