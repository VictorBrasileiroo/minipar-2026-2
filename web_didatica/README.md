# Web didática

Área do Eixo B. Desenvolver separada da Web original, integrando pela API acordada (contrato C-WEB-v1, `docs/02_CONTRATOS_TECNICOS.md` §1). Sem aplicação funcional nesta versão.

- `fixtures/`: respostas mock no formato do contrato, usadas enquanto o serviço do Eixo A (`CORE-08`) não existe. Ver [fixtures/README.md](fixtures/README.md).
- `tools/`: `gerar_fixtures.py` gera as fixtures a partir das fases reais de `src/` (só leitura) e `validar_fixtures.py` as confere contra o contrato. A Web não usa esses scripts em tempo de execução.
