# CI para gerar o .exe sem usar venv local

Este workflow do **GitHub Actions** compila o seu cliente Windows (.exe) automaticamente.
Você NÃO precisa rodar venv/Python na sua máquina.

## Como usar

1) No repositório `MovideskApiBackend`, adicione estes arquivos:
   - `.github/workflows/windows-build.yml` (este arquivo)
   - `backend.json` (com a URL do backend)

2) Ajuste a URL em `backend.json`, por exemplo:
```json
{ "backend_base": "https://web-production-ba1e.up.railway.app" }
```

3) Faça commit e push para a branch `main`.

4) Acesse **Actions** no GitHub do seu repositório e rode o workflow **Build Windows EXE (Movidesk Client)** (ou aguarde o disparo pelo push).

5) Quando terminar, baixe o artefato **MovideskApp_Windows**. Dentro dele terá:
   - `MovideskApp.exe` (executável pronto)
   - `backend.json` (coloque ao lado do .exe para trocar a URL sem recompilar)

## Observações
- O workflow espera que **o seu código fonte** (a pasta `movidesk/` com `main.py`, etc.) já esteja no repositório.
- O ícone usado no exemplo é `app_refactor/icon.ico`. Se não existir, troque ou remova a flag `--icon` no passo do PyInstaller.
- Se quiser alterar o nome do arquivo de entrada, ajuste `movidesk/main.py` no passo `pyinstaller`.
- Para rodar o workflow manualmente, use o botão **Run workflow** em Actions (o gatilho `workflow_dispatch`).

## Dúvidas comuns
- **Erro: arquivo não encontrado** → confirme os caminhos (ex.: `movidesk/main.py`, `app_refactor/icon.ico`, `backend.json`).
- **Quer outro Python?** → mude `python-version` para `3.10` ou `3.12`.
