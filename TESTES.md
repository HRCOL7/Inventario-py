# Testes Unitários - IKARUS INVENTORY

## Resumo

✅ **19 testes criados e executados com sucesso**

### Resultado Final
```
Ran 19 tests in 0.568s
OK
```

## Estrutura dos Testes

### 1. TestConfig (3 testes)
Valida funções de configuração e normalização:
- ✅ `test_normaliza_rotulo` - Normaliza rótulos de colunas
- ✅ `test_normaliza_rotulo_espacos` - Trata espaços múltiplos
- ✅ `test_sinonimos_existem` - Verifica sinônimos configurados

### 2. TestPlanilha (6 testes)
Testa manipulação de dados e Excel:
- ✅ `test_encontrar_coluna_exato` - Busca por nome exato
- ✅ `test_encontrar_coluna_sinonimo` - Busca por sinônimos
- ✅ `test_encontrar_coluna_nao_existe` - Coluna inexistente
- ✅ `test_construir_dataframes_mapeados` - Produtos mapeados
- ✅ `test_construir_dataframes_nao_mapeados` - Produtos não mapeados
- ✅ `test_construir_dataframes_ignora_zero` - Ignora quantidade zero

### 3. TestExportacao (2 testes)
Valida exportação de relatórios:
- ✅ `test_exportar_txt_formatado` - Exporta TXT agregado
- ✅ `test_exportar_detalhado` - Exporta CSV e XLSX

### 4. TestUsuarios (6 testes)
Testa gerenciamento de usuários:
- ✅ `test_hash_senha` - Geração de hash
- ✅ `test_hash_senha_formato` - Formato SHA256
- ✅ `test_cadastrar_usuario_novo` - Cadastro de novo usuário
- ✅ `test_cadastrar_usuario_duplicado` - Rejeita duplicados
- ✅ `test_autenticar_correto` - Autenticação bem-sucedida
- ✅ `test_autenticar_incorreto` - Rejeita credenciais erradas

### 5. TestIntegration (2 testes)
Testa fluxos completos:
- ✅ `test_fluxo_cadastro_autenticacao` - Cadastro + login
- ✅ `test_fluxo_alteracao_senha` - Mudança de senha + login

## Como Executar os Testes

### Opção 1: Linha de Comando
```bash
# Todos os testes
python -m unittest discover -s . -p "test_*.py" -v

# Apenas uma classe de testes
python -m unittest test_inventario.TestUsuarios -v

# Um teste específico
python -m unittest test_inventario.TestUsuarios.test_hash_senha -v
```

### Opção 2: Script Batch (Windows)
```bash
run_tests.bat
```

### Opção 3: Com Coverage
```bash
pip install coverage pytest-cov
python -m pytest test_inventario.py --cov=. --cov-report=html
```

## Cobertura de Testes

### Módulos Testados
- ✅ `usuarios.py` - Autenticação e gerenciamento
- ✅ `planilha.py` - Manipulação de dados
- ✅ `exportacao.py` - Exportação de relatórios
- ✅ `config.py` - Configurações

### Linhas de Teste
- Hash e segurança
- Entrada/saída de dados
- Tratamento de erros
- Fluxos de negócio completos
- Casos extremos (duplicatas, valores zero, etc.)

## Padrões Utilizados

### Mocking
- Uso de `@patch` para isolar testes
- Arquivos temporários para I/O

### Fixtures
- `setUp()` e `tearDown()` para preparação/limpeza
- Isolamento de testes com `tempfile`

### Assertions
- `assertTrue()` / `assertFalse()`
- `assertEqual()` / `assertNotEqual()`
- `assertIn()` / `assertIsNone()`

## Próximos Passos

Você pode:

1. **Adicionar mais testes** para a GUI (tkinter)
2. **Testar exportação de PDF** (quando FPDF instalado)
3. **Medir cobertura** com `coverage.py`
4. **Integração CI/CD** (GitHub Actions, GitLab CI)
5. **Testes de carga** para verificar performance

## Executar Testes Agora

```bash
cd c:\Users\Derla\Desktop\inventario
python -m unittest discover -s . -p "test_*.py" -v
```
