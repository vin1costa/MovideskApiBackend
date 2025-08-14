
Como executar (mantendo a mesma interface):
1) Coloque a pasta 'app_refactor' no mesmo diretório do seu projeto.
2) Instale dependências: pip install ttkbootstrap requests
3) Defina o token por variável de ambiente para segurança (recomendado):
   - Windows (PowerShell):  $env:MOVIDESK_TOKEN="SEU_TOKEN"
   - Linux/macOS (bash):    export MOVIDESK_TOKEN="SEU_TOKEN"
   Se não definir, o app usa o 'token' do config.json.
4) Rode:  python -m app_refactor.main   (ou python app_refactor/main.py)

Principais mudanças (sem alterar estrutura visual/fluxo):
- Validações de entrada (data/hora/ticket) em validators.py.
- Tratamento de erros centralizado via AppError (mensagens amigáveis).
- Senhas com hash sha256 (migração automática ao carregar/salvar).
- Token via variável de ambiente MOVIDESK_TOKEN (fallback para config.json).
- Separação em módulos: ui_main (GUI), api_client (rede), validators, security, config_store, i18n, constants.
- UX: botão 'Apontar' desabilita e mostra 'Enviando...' durante requisição; login com mostrar/ocultar senha.
- i18n: textos centralizados em i18n.TEXTS (Português por padrão).
- Boas práticas: with open, os.path, constants centralizadas.

Observações:
- A tela de Administração já possui o botão '💾 Salvar' conforme solicitado.
- O layout e os textos exibidos foram mantidos, apenas extraídos para i18n e constantes.
