# Guia de criação do repositório novo e importação segura da base

**Estado local verificado — SET-01, 16/10/2026:** este workspace já contém a base ativa, snapshot histórico (36 arquivos), Git/histórico e remoto configurado. SHA-256: 34 correspondências exatas, diferenças esperadas em `README.md` e `.gitignore`, nenhum ausente. **Não executar nova importação ou inicialização Git aqui.** As seções de criação abaixo se aplicam somente a uma estrutura nova ainda sem a base. Evidências: [`auditorias/SET-01_VALIDACAO_ESTRUTURAL.md`](auditorias/SET-01_VALIDACAO_ESTRUTURAL.md).

## 1. Decisão estrutural

O trio terá **repositório novo**, inicialmente recomendado **privado**:

- **Raiz:** projeto MiniPar **2026.2 ativo**, começando por cópia do 2026.1.
- **`legacy/minipar-2026.1/`:** snapshot completo e **imutável** do projeto anterior, para comparação e atribuição.
- **`docs/`:** planejamento, contrato, decisões, backlog e documentação.
- **`runtime/` (C)** e **`web_didatica/` (B)**: implementações futuras isoladas.
- **`tests/2026_2/`**: novos programas 8–11. Os testes anteriores ficam em `tests/` do código ativo após importação.

**Neste workspace o código Python herdado já está copiado.** A orientação anterior de que o pacote continha somente planejamento/importador ficou desatualizada. O método e a data da cópia anterior não foram comprovados; o manifesto que o importador atual produziria não está presente. Não reconstruir metadados dentro de `legacy/` nem repetir a cópia para tentar suprir essa lacuna.

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

Somente numa estrutura nova, extrair todo o ZIP para uma pasta de trabalho, por exemplo `MINIPAR_2026_2`, e verificar que a base ainda não existe. Simular primeiro:

Windows PowerShell:
```powershell
py scripts/importar_base.py --source "C:\CAMINHO\minipar-base-2026-1"
```
Se o alias `py` falhar, usar caminho absoluto do Python 3.12 que funcionou na auditoria:
```powershell
& "C:\CAMINHO\Python312\python.exe" scripts/importar_base.py --source "C:\CAMINHO\minipar-base-2026-1"
```
Substituir **ambos** os caminhos pelo seu ambiente real.

Linux/macOS:
```bash
python3 scripts/importar_base.py --source ../minipar-base-2026-1
```

Somente após conferir caminhos, exclusões e ausência de destinos existentes numa estrutura nova, acrescentar `--apply` para copiar. O script bloqueia substituição de arquivos existentes; não edita documentos `docs/` nem `AGENTS.md`. No SET-01 atual nenhum comando `--apply` foi executado.

## 5. Verificações após importação

Confira:
- `legacy/minipar-2026.1/src/lexer.py` existe.
- `src/lexer.py` existe na **raiz** ativa.
- `main.py`, `app.py`, `tests/`, `templates/` e outros componentes antigos ativos estão presentes.
- `legacy/minipar-2026.1/` contém o snapshot; o importador atual também gera `ORIGEM_SNAPSHOT.json` com hashes, data UTC e commit quando a fonte é a raiz de um repositório Git. Neste workspace esse manifesto está ausente e o commit de origem permanece desconhecido. O histórico do novo repositório não comprova o commit antigo.
- `README.md` da raiz continua este guia inicial.
- `python scripts/validar_planejamento.py` retorna sem erros.
- `git status` não inclui `.exe`, `.env`, `venv`, logs, tokens ou artefatos gerados.

Se o script reportar conflito, **não force nem apague o snapshot**. Verifique primeiro se a importação já está completa; se estiver, não a repita. Uma importação parcial exige diagnóstico e correção revisada, preservando os arquivos existentes.

## 6. Inicializar repositório local

Somente para uma estrutura nova que ainda não possua `.git`. Não executar estes comandos no workspace já auditado:

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

O arquivo de dependências presente na raiz e no snapshot chama-se **`requeriments.txt`** (`Flask==3.0.0`); o README histórico cita `requirements.txt`, que não existe nesta cópia. SET-02 deve usar o nome real ao definir instalação em ambiente isolado; nenhum arquivo herdado foi renomeado neste card.

No SET-01, o alias `python` do Windows falhou; o validador rodou com `C:\Users\victo\AppData\Local\Programs\Python\Python312\python.exe` (Python 3.12.4). Trata-se de evidência desta máquina, não padronização de ambiente ou smoke do compilador. Não foi alterado o PATH.

## 9. Próximo passo após push

1. Reunião G0 para nomear B/C e confirmar disponibilidade.
2. Congelar contratos técnicos.
3. Marcar cards READY.
4. Criar GitHub Issues/Project a partir do backlog revisado, sem duplicar fonte de verdade.
5. Começar implementação de acordo com ownership.

**A pasta `legacy/` jamais é o local de desenvolvimento da versão 2026.2.**
