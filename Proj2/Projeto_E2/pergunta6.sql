%%sql
REFRESH MATERIALIZED VIEW estatisticas_voos;
DROP INDEX IF EXISTS idx_estatisticas_voos_hora_partida;
DROP INDEX IF EXISTS idx_estatisticas_voos_cidade_partida;
DROP INDEX IF EXISTS idx_estatisticas_voos_cidade_chegada;
-- Sem índices
-- Por intervalo de tempo
EXPLAIN ANALYZE SELECT * FROM estatisticas_voos WHERE hora_partida BETWEEN '2025-01-01 00:00:00' AND '2025-01-31 23:59:59';

-- Por cidade de partida
EXPLAIN ANALYZE SELECT * FROM estatisticas_voos WHERE cidade_partida = 'Lisboa';

-- Combinada
EXPLAIN ANALYZE SELECT * FROM estatisticas_voos WHERE cidade_partida = 'Lisboa' AND hora_partida BETWEEN '2025-01-01 00:00:00' AND '2025-01-31 23:59:59';

-- Com índices
 CREATE INDEX idx_estatisticas_voos_hora_partida ON estatisticas_voos (hora_partida DESC);
 CREATE INDEX idx_estatisticas_voos_cidade_partida ON estatisticas_voos (cidade_partida);
 CREATE INDEX idx_estatisticas_voos_cidade_chegada ON estatisticas_voos (cidade_chegada);

-- Por intervalo de tempo
 EXPLAIN ANALYZE SELECT * FROM estatisticas_voos WHERE hora_partida BETWEEN '2025-01-01 00:00:00' AND '2025-01-31 23:59:59';

-- Por cidade de partida
 EXPLAIN ANALYZE SELECT * FROM estatisticas_voos WHERE cidade_partida = 'Lisboa';

-- Combinada
 EXPLAIN ANALYZE SELECT * FROM estatisticas_voos WHERE cidade_partida = 'Lisboa' AND hora_partida BETWEEN '2025-01-01 00:00:00' AND '2025-01-31 23:59:59';
