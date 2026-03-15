# ===============================
# IKARUS INVENTORY - Testes Unitários
# ===============================

import unittest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from collections import Counter

# Imports dos módulos a testar
from usuarios import (
    carregar_usuarios, salvar_usuarios, hash_senha, cadastrar_usuario,
    autenticar, alterar_senha, excluir_usuario, obter_usuarios, obter_senhas
)
from config import SINONIMOS_COLUNAS
from planilha import normaliza_rotulo, encontrar_coluna, construir_dataframes
import pandas as pd


class TestUsuarios(unittest.TestCase):
    """Testes para o módulo usuarios.py"""
    
    def setUp(self):
        """Cria um arquivo temporário para testes"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_usuarios_file = os.path.join(self.temp_dir, "usuarios_test.json")
        
    def tearDown(self):
        """Limpa arquivos temporários"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_hash_senha(self):
        """Testa geração de hash de senha"""
        senha = "test123"
        hash1 = hash_senha(senha)
        hash2 = hash_senha(senha)
        
        # Mesmo hash para mesma senha
        self.assertEqual(hash1, hash2)
        
        # Hash diferente para senha diferente
        self.assertNotEqual(hash1, hash_senha("different"))
    
    def test_hash_senha_formato(self):
        """Testa se o hash tem formato SHA256"""
        hash_result = hash_senha("test")
        # SHA256 produz 64 caracteres hexadecimais
        self.assertEqual(len(hash_result), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in hash_result))
    
    def test_cadastrar_usuario_novo(self):
        """Testa cadastro de novo usuário"""
        with patch('usuarios.ARQUIVO_USUARIOS', self.temp_usuarios_file):
            resultado = cadastrar_usuario("testuser", "testpass")
            self.assertTrue(resultado)
            
            usuarios = carregar_usuarios()
            self.assertEqual(len(usuarios), 1)
            self.assertEqual(usuarios[0]["usuario"], "testuser")
    
    def test_cadastrar_usuario_duplicado(self):
        """Testa que não permite cadastrar usuário duplicado"""
        with patch('usuarios.ARQUIVO_USUARIOS', self.temp_usuarios_file):
            cadastrar_usuario("testuser", "pass1")
            resultado = cadastrar_usuario("testuser", "pass2")
            self.assertFalse(resultado)
    
    def test_autenticar_correto(self):
        """Testa autenticação com credenciais corretas"""
        with patch('usuarios.ARQUIVO_USUARIOS', self.temp_usuarios_file):
            cadastrar_usuario("testuser", "testpass")
            resultado = autenticar("testuser", "testpass")
            self.assertTrue(resultado)
    
    def test_autenticar_incorreto(self):
        """Testa autenticação com credenciais incorretas"""
        with patch('usuarios.ARQUIVO_USUARIOS', self.temp_usuarios_file):
            cadastrar_usuario("testuser", "testpass")
            resultado = autenticar("testuser", "wrongpass")
            self.assertFalse(resultado)


class TestConfig(unittest.TestCase):
    """Testes para o módulo config.py"""
    
    def test_normaliza_rotulo(self):
        """Testa normalização de rótulos"""
        self.assertEqual(normaliza_rotulo("Código_De_Barras"), "código de barras")
        self.assertEqual(normaliza_rotulo("CODIGO-BARRAS"), "codigo barras")
        self.assertEqual(normaliza_rotulo("código_barra-123"), "código barra 123")
    
    def test_normaliza_rotulo_espacos(self):
        """Testa normalização com espaços múltiplos"""
        self.assertEqual(normaliza_rotulo("  código   barra  "), "código barra")
    
    def test_sinonimos_existem(self):
        """Testa se sinônimos estão configurados"""
        self.assertIn("CodigoBarra", SINONIMOS_COLUNAS)
        self.assertIn("CodigoInterno", SINONIMOS_COLUNAS)
        self.assertIn("Nome", SINONIMOS_COLUNAS)


class TestPlanilha(unittest.TestCase):
    """Testes para o módulo planilha.py"""
    
    def test_encontrar_coluna_exato(self):
        """Testa busca de coluna com nome exato"""
        df = pd.DataFrame({
            "CodigoBarra": [1, 2, 3],
            "CodigoInterno": ["A", "B", "C"],
            "Nome": ["Prod1", "Prod2", "Prod3"]
        })
        
        resultado = encontrar_coluna(df, "CodigoBarra")
        self.assertEqual(resultado, "CodigoBarra")
    
    def test_encontrar_coluna_sinonimo(self):
        """Testa busca de coluna usando sinônimos"""
        df = pd.DataFrame({
            "codigo_barra": [1, 2, 3],
            "codigo_interno": ["A", "B", "C"],
            "nome": ["Prod1", "Prod2", "Prod3"]
        })
        
        resultado = encontrar_coluna(df, "CodigoBarra")
        self.assertEqual(resultado, "codigo_barra")
    
    def test_encontrar_coluna_nao_existe(self):
        """Testa busca de coluna inexistente"""
        df = pd.DataFrame({
            "A": [1, 2, 3],
            "B": ["X", "Y", "Z"]
        })
        
        resultado = encontrar_coluna(df, "CodigoBarra")
        self.assertIsNone(resultado)
    
    def test_construir_dataframes_mapeados(self):
        """Testa construção de dataframes com produtos mapeados"""
        contagem = Counter({"1234567890123": 5, "9876543210987": 3})
        mapeamento = {
            "1234567890123": ("P001", "Produto 1", "Grupo A"),
            "9876543210987": ("P002", "Produto 2", "Grupo B")
        }
        
        df, df_nm = construir_dataframes(contagem, mapeamento)
        
        self.assertEqual(len(df), 2)
        self.assertEqual(len(df_nm), 0)
        self.assertEqual(df.iloc[0]["quantidade"], 5)
        self.assertEqual(df.iloc[1]["quantidade"], 3)
    
    def test_construir_dataframes_nao_mapeados(self):
        """Testa construção de dataframes com produtos não mapeados"""
        contagem = Counter({"1111111111111": 2, "2222222222222": 4})
        mapeamento = {"1111111111111": ("P001", "Produto 1", "Grupo A")}
        
        df, df_nm = construir_dataframes(contagem, mapeamento)
        
        self.assertEqual(len(df), 1)
        self.assertEqual(len(df_nm), 1)
        self.assertEqual(df_nm.iloc[0]["quantidade"], 4)
    
    def test_construir_dataframes_ignora_zero(self):
        """Testa que ignora produtos com quantidade zero"""
        contagem = Counter({"1111111111111": 0, "2222222222222": 5})
        mapeamento = {
            "1111111111111": ("P001", "Produto 1", "Grupo A"),
            "2222222222222": ("P002", "Produto 2", "Grupo B")
        }
        
        df, df_nm = construir_dataframes(contagem, mapeamento)
        
        self.assertEqual(len(df), 1)


class TestExportacao(unittest.TestCase):
    """Testes para o módulo exportacao.py"""
    
    def setUp(self):
        """Cria diretório temporário"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Limpa diretório temporário"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_exportar_txt_formatado(self):
        """Testa exportação em formato TXT"""
        from exportacao import exportar_txt_formatado
        
        contagem = Counter({"1234567890123": 5, "9876543210987": 3})
        mapeamento = {
            "1234567890123": ("P001", "Produto 1", "Grupo A"),
            "9876543210987": ("P002", "Produto 2", "Grupo B")
        }
        
        arquivo = os.path.join(self.temp_dir, "test.txt")
        exportar_txt_formatado(contagem, mapeamento, arquivo)
        
        self.assertTrue(os.path.exists(arquivo))
        
        with open(arquivo, "r", encoding="utf-8") as f:
            conteudo = f.read()
        
        self.assertIn("P001", conteudo)
        self.assertIn("P002", conteudo)
        self.assertIn("5", conteudo)
        self.assertIn("3", conteudo)
    
    def test_exportar_detalhado(self):
        """Testa exportação detalhada (CSV e XLSX)"""
        from exportacao import exportar_detalhado
        import pandas as pd
        
        contagem = Counter({"1111111111111": 10})
        mapeamento = {"1111111111111": ("P001", "Test Product", "TestGroup")}
        
        # Mock dos arquivos de saída
        with patch('exportacao.ARQUIVO_CSV_DETALHADO', 
                   os.path.join(self.temp_dir, 'detalhado.csv')):
            with patch('exportacao.ARQUIVO_CSV_NAO_MAPEADOS',
                       os.path.join(self.temp_dir, 'nao_mapeados.csv')):
                with patch('exportacao.ARQUIVO_XLSX_SAIDA',
                           os.path.join(self.temp_dir, 'output.xlsx')):
                    exportar_detalhado(contagem, mapeamento)


class TestIntegration(unittest.TestCase):
    """Testes de integração entre módulos"""
    
    def setUp(self):
        """Cria um arquivo temporário para testes"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_usuarios_file = os.path.join(self.temp_dir, "usuarios_test.json")
    
    def tearDown(self):
        """Limpa arquivos temporários"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_fluxo_cadastro_autenticacao(self):
        """Testa fluxo completo: cadastro -> autenticação"""
        with patch('usuarios.ARQUIVO_USUARIOS', self.temp_usuarios_file):
            # Cadastrar
            self.assertTrue(cadastrar_usuario("user1", "pass1"))
            
            # Autenticar
            self.assertTrue(autenticar("user1", "pass1"))
            
            # Obter usuários
            usuarios = obter_usuarios()
            self.assertIn("user1", usuarios)
    
    def test_fluxo_alteracao_senha(self):
        """Testa fluxo: cadastro -> alteração de senha -> autenticação"""
        with patch('usuarios.ARQUIVO_USUARIOS', self.temp_usuarios_file):
            # Cadastrar
            cadastrar_usuario("user2", "oldpass")
            
            # Alterar senha
            self.assertTrue(alterar_senha("user2", "oldpass", "newpass"))
            
            # Autenticar com nova senha
            self.assertTrue(autenticar("user2", "newpass"))
            
            # Falhar com senha antiga
            self.assertFalse(autenticar("user2", "oldpass"))


# ===============================
# EXECUTAR TESTES
# ===============================

if __name__ == "__main__":
    # Executar com verbosidade
    unittest.main(verbosity=2)
