# IKARUS INVENTORY - Controle de Estoque

Sistema completo de inventário com interface gráfica (Tkinter), controle de usuários, exportação de relatórios e funcionalidades de pesquisa.

## Estrutura do Projeto

```
inventario/
├── main.py                 # Ponto de entrada da aplicação
├── config.py              # Configurações globais, logging
├── usuarios.py            # Gerenciamento de usuários (autenticação, cadastro)
├── planilha.py            # Manipulação de planilhas Excel
├── exportacao.py          # Exportação de relatórios (TXT, XLSX, CSV, PDF)
├── gui.py                 # Interface gráfica principal (Tkinter)
├── login_gui.py           # Janela de login e gerenciamento de usuários (GUI)
├── usuarios.json          # Banco de dados de usuários (JSON)
├── Produtos Box.xlsx      # Arquivo de mapeamento de produtos
└── README.md              # Este arquivo
```

## Módulos

### `main.py`
Função principal e ponto de entrada da aplicação. Responsável por:
- Inicializar a interface Tkinter
- Exibir tela de login
- Carregar mapeamento de produtos
- Iniciar a GUI principal

### `config.py`
Configurações globais:
- Caminhos de arquivos (entrada/saída)
- Variáveis de configuração (senhas, intervalos, etc.)
- Sinônimos de colunas para busca automática
- Sistema de logging

### `usuarios.py`
Funções de manipulação de usuários:
- `carregar_usuarios()` - Carrega usuários do JSON
- `cadastrar_usuario()` - Cadastra novo usuário
- `autenticar()` - Valida credenciais
- `alterar_senha()` - Altera senha existente
- `excluir_usuario()` - Remove usuário
- `obter_usuarios()` - Retorna lista de usuários
- `obter_senhas()` - Retorna dicionário com senhas (admin)

### `planilha.py`
Funções de manipulação de dados:
- `normaliza_rotulo()` - Normaliza nomes de colunas
- `encontrar_coluna()` - Busca colunas por sinônimos
- `carregar_mapeamento()` - Carrega dados do Excel
- `construir_dataframes()` - Cria DataFrames com dados mapeados

### `exportacao.py`
Funções de exportação:
- `exportar_txt_formatado()` - Exporta em TXT agregado
- `exportar_detalhado()` - Exporta CSV e XLSX
- `exportar_pdf()` - Exporta em PDF (se FPDF instalado)

### `gui.py`
Classe `InventarioGUI`:
- Interface gráfica completa com Tkinter
- Entrada de códigos de barras
- Pesquisa de produtos
- Gerenciamento de estoque
- Exportação de relatórios
- Menu de contexto
- Autosave automático

### `login_gui.py`
Funções de interface de login:
- `tela_login()` - Janela de login
- `cadastrar_usuario_gui()` - GUI para cadastrar usuário
- `alterar_senha_gui()` - GUI para alterar senha
- `consultar_usuarios_gui()` - Exibe usuários cadastrados
- `excluir_usuario_gui()` - GUI para excluir usuário
- `mostrar_senhas_gui()` - Exibe senhas (admin only)

## Como Usar

### Instalação

1. Instale dependências:
```bash
pip install pandas openpyxl fpdf2
```

Para usar modo mobile (celular), instale tambem:
```bash
pip install Flask
```

2. Execute a aplicação:
```bash
python main.py
```

### Login

- Primeira execução: Crie um usuário de admin
- Usuários admin podem gerenciar outros usuários
- Senha padrão de finalização: `733721`

### Pasta Nomeada no Inicio da Contagem

Ao iniciar a interface premium, o sistema pede o nome da pasta da sessao.

Os arquivos da contagem sao salvos em:
- `sessoes_contagem/<nome_sessao>_<timestamp>/contagem_backup.txt`
- `sessoes_contagem/<nome_sessao>_<timestamp>/contagem.txt`
- `sessoes_contagem/<nome_sessao>_<timestamp>/contagem.xlsx`
- `sessoes_contagem/<nome_sessao>_<timestamp>/contagem_detalhada.csv`
- `sessoes_contagem/<nome_sessao>_<timestamp>/nao_mapeados.csv`

### Salvamento em Nuvem

Defina a variavel de ambiente `IKARUS_NUVEM_DIR` apontando para uma pasta sincronizada (OneDrive, Google Drive, Dropbox etc).

Exemplo no PowerShell:
```powershell
$env:IKARUS_NUVEM_DIR = "C:\Users\SeuUsuario\OneDrive\InventarioNuvem"
python main.py
```

Quando configurada, cada autosave/exportacao copia a pasta da sessao para a nuvem automaticamente.

### Modo Celular (Camera + Codigo de Barras)

Suba o servidor:

```bash
python mobile_server.py --host 0.0.0.0 --port 8000
```

Se a camera nao abrir no celular, rode com HTTPS:

```bash
python mobile_server.py --host 0.0.0.0 --port 8000 --https
```

No celular (mesma rede Wi-Fi), abra:

```text
http://IP_DO_PC:8000
```

Recursos disponiveis no celular:
- Consulta de preco por codigo de barras
- Ajuste de quantidade (delta positivo/negativo)
- Cadastro/atualizacao de produto
- Inventario em tempo real
- Leitura de codigo de barras pela camera (quando o navegador suportar BarcodeDetector)

Notas para camera:
- Em muitos celulares, camera via navegador exige HTTPS (ou localhost)
- Ao usar `--https`, aceite o certificado de desenvolvimento no navegador
- Preferir Chrome/Edge atualizados no Android

### Atalhos de Teclado

| Atalho | Função |
|--------|--------|
| Ctrl+F | Localizar produto contado |
| F1 ou Ctrl+S | Salvar backup parcial |
| Ctrl+F2 | Finalizar e exportar |
| Ctrl+H | Mostrar ajuda |
| * | Pesquisar produto |
| + | Adicionar manualmente |
| - | Subtrair quantidade |

### Arquivo Excel

O arquivo `Produtos Box.xlsx` deve conter as colunas:
- Código de Barras (ou sinônimos: codigobarra, cod_barra, etc.)
- Código Interno (ou sinônimos: codigo, sku, etc.)
- Nome (ou sinônimos: descricao, produto, etc.)
- Grupo (opcional)

## Arquivos de Saída

Após finalizar a contagem, são gerados:
- `contagem.txt` - Relatório TXT simples
- `contagem.xlsx` - Relatório XLSX com abas
- `contagem_detalhada.csv` - Dados mapeados em CSV
- `nao_mapeados.csv` - Produtos não mapeados em CSV
- `relatorio_inventario.pdf` - Relatório em PDF (opcional)

## Logging

Todas as ações são registradas em `contagem.log`:
- Login/logout
- Operações de cadastro
- Contagens e alterações
- Exportações
- Erros

## Configurações

Edite `config.py` para customizar:
- Caminhos de arquivos
- Senha de finalização
- Intervalo de autosave
- Sinônimos de colunas

## Requisitos

- Python 3.7+
- pandas
- openpyxl
- fpdf2 (opcional, para PDF)
- tkinter (incluído com Python)

## Notas

- JSON de usuários é salvo com encoding UTF-8
- Senhas são armazenadas em hash SHA256
- Backup automático a cada 2 minutos (configurável)
- Suporte a múltiplas abas no Excel
- Busca automática de produtos por sinônimos de coluna
