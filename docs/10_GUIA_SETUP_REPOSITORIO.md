# Guia de criação do repositório novo e importação segura da base

## 1. Decisão estrutural

O trio terá **repositório novo**, inicialmente recomendado **privado**:

- **Raiz:** projeto MiniPar **2026.2 ativo**, começando por cópia do 2026.1.
- **`legacy/minipar-2026.1/`:** snapshot completo e **imutável** do projeto anterior, para comparação e atribuição.
- **`docs/`:** planejamento, contrato, decisões, backlog e documentação.
- **`runtime/` (C)** e **`web_didatica/` (B)**: implementações futuras isoladas.
- **`tests/2026_2/`**: novos programas 8–11. Os testes anteriores ficam em `tests/` do código ativo após importação.

**Este ZIP contém planejamento e ferramentas, não o código Python original.** O motivo é técnico (não há cópia montada da base), além de não haver licença de redistribuição declarada no repositório público anterior. A importação é uma ação expressa feita localmente pelo usuário.

## 2. Criar repositório vazio no GitHub

1. GitHub → New repository.
2. Nome sugerido: `minipar-2026-2` (ou nome escolhido pelo trio).
3. Visibilidade: **Private** inicialmente, até confirmar os direitos de redistribuição da base anterior.
4. **Não** marcar criação automática de README, `.gitignore` ou LICENSE: o pacote já contém README e ignore.
5. Criar. Convidar os outros dois com permissão apropriada depois do primeiro push.

## 3. Obter o MiniPar 2026.1

Fonte: https://github.com/luizwhirl/minipar-improvement .

Pode clonar na sua máquina:
```bash
git clone https://github.com/luizwhirl/minipar-improvement.git minipar-base-2026-1
```

Ou baixar ZIP pelo próprio GitHub e extrair para uma pasta local. **Não** copiar a pasta `.git` da origem para dentro do novo repositório.

Antes de publicar, manter os créditos e verificar as condições de reutilização. Repositório público sem LICENSE **não garante** redistribuição livre.

## 4. Descompactar o pacote deste chat

Extrair todo o ZIP para uma pasta de trabalho, por exemplo `MINIPAR_2026_2`. Dentro dela, executar:

Windows PowerShell:
```powershell
py scripts/importar_base.py --source "C:\CAMINHO\minipar-base-2026-1" --apply
```
Se o alias `py` falhar, usar caminho absoluto do Python 3.12 que funcionou na auditoria:
```powershell
& "C:\CAMINHO\Python312\python.exe" scripts/importar_base.py --source "C:\CAMINHO\minipar-base-2026-1" --apply
```
Substituir **ambos** os caminhos pelo seu ambiente real.

Linux/macOS:
```bash
python3 scripts/importar_base.py --source ../minipar-base-2026-1 --apply
```

Primeiro execute **sem `--apply`** para ver o plano de cópia; depois rode com `--apply` quando conferir os caminhos. O script bloqueia substituição de arquivos existentes; não edita documentos `docs/` nem `AGENTS.md`.

## 5. Verificações após importação

Confira:
- `legacy/minipar-2026.1/src/lexer.py` existe.
- `src/lexer.py` existe na **raiz** ativa.
- `main.py`, `app.py`, `tests/`, `templates/` e outros componentes antigos ativos estão presentes.
- `legacy/minipar-2026.1/` tem histórico/snapshot de origem.
- `README.md` da raiz continua este guia inicial.
- `python scripts/validar_planejamento.py` retorna sem erros.
- `git status` não inclui `.exe`, `.env`, `venv`, logs, tokens ou artefatos gerados.

Se o script reportar conflito, **não force**: remova importação parcial após inspecionar cuidadosamente, ou faça cópia para nova pasta e repita.

## 6. Inicializar repositório local

```bash
git init
git branch -M main
git add .
git commit -m "chore: bootstrap MiniPar 2026.2 with legacy snapshot and project plan"
git remote add origin URL_DO_REPO_NOVO
git push -u origin main
```

**Nunca executar `git push --force`** no início. Se o remoto já tiver commits, conciliar antes.

## 7. Proteções básicas no GitHub

- Convidar os outros dois.
- Preferir PR para `main` com revisão, não commits diretos.
- Prefixos de branch por eixo (`eixo-a/`, `eixo-b/`, `eixo-c/`).
- Não criar GitHub Issues ainda; primeiro revisar `docs/01..07` e `planning/cards.json`.
- Evitar upload de segredos e dados pessoais; conferir `git status` antes de commit.
- Se algum recurso de branch protection exigir plano/permite gestão, registrar limitação e usar revisão de PR disciplinada.

## 8. Preparar toolchain

**Problema conhecido:** auditoria encontrou GCC 6.3.0, que não aceita `-std=c++20`. O codegen anterior usa C++20, e a cópia experimental C++14 **não** equivale à correção final da base original.

Definir Python, dependências Web e G++20+ suportado; documentar versões e comandos por plataforma. Não modificar `PATH` global sem autorização; preferir ambiente isolado e script local de compilação. Registrar T01–T07 com resultados nativos reais.

O repositório original chama dependências `requeriments.txt`, enquanto README cita `requirements.txt`: confirmar/corrigir no eixo A depois da importação.

## 9. Próximo passo após push

1. Reunião G0 para nomear B/C e confirmar disponibilidade.
2. Congelar contratos técnicos.
3. Marcar cards READY.
4. Criar GitHub Issues/Project a partir do backlog revisado, sem duplicar fonte de verdade.
5. Começar implementação de acordo com ownership.

**A pasta `legacy/` jamais é o local de desenvolvimento da versão 2026.2.**
