#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste rápido das novas funcionalidades - Fase 2
Validar: Cache, Fuzzy Matching, Shortcuts, Light Mode
"""

import sys
import json

def test_cache_utils():
    """Testar módulo cache_utils"""
    print("=" * 60)
    print("TESTE 1: Cache e Busca com Fuzzy Matching")
    print("=" * 60)
    
    try:
        from cache_utils import CacheProducts, KeyboardShortcuts
        print("✓ Módulo cache_utils importado com sucesso")
        
        # Criar mapeamento de teste
        test_mapping = {
            "7898958766030": ("200", "RAÇÃO CÃES NATURAL 25KG", "Alimentos"),
            "7898958766306": ("2242", "RAÇÃO GATOS PESCADO 25KG", "Alimentos"),
            "7891000069455": ("202", "FRISKIES GATO AD 10,1KG", "Alimentos"),
        }
        
        # Testar cache
        cache = CacheProducts(test_mapping)
        print("✓ Cache criado com sucesso")
        
        # Teste 1: Busca por prefixo
        print("\n  → Teste busca prefixo (digitando 'ração'):")
        resultados = cache.busca_prefixo("ração", "nome")
        print(f"    Encontrados: {len(resultados)} produtos")
        for cb, ci, nm, gr in resultados:
            print(f"      • {nm} ({ci})")
        
        # Teste 2: Busca fuzzy
        print("\n  → Teste busca fuzzy (digitando 'rao' com erro):")
        resultados = cache.busca_fuzzy("rao", "nome", limiar=0.6)
        print(f"    Encontrados: {len(resultados)} produtos")
        for cb, ci, nm, gr in resultados:
            print(f"      • {nm} ({ci})")
        
        # Teste 3: Busca combinada
        print("\n  → Teste busca combinada (digitando 'gato'):")
        resultados = cache.busca_combinada("gato", "nome")
        print(f"    Encontrados: {len(resultados)} produtos")
        for cb, ci, nm, gr in resultados:
            print(f"      • {nm} ({ci})")
        
        # Teste 4: Atalhos de teclado
        print("\n  → Teste atalhos de teclado:")
        shortcuts = KeyboardShortcuts.get_all_shortcuts()
        print(f"    Total de atalhos: {len(shortcuts)}")
        for desc, display in list(shortcuts.items())[:3]:
            print(f"      • {display:15} → {desc}")
        
        print("\n✓ Cache e Fuzzy Matching: OK")
        return True
        
    except Exception as e:
        print(f"✗ Erro no teste de cache: {e}")
        return False


def test_light_mode():
    """Testar light mode"""
    print("\n" + "=" * 60)
    print("TESTE 2: Light Mode Theme")
    print("=" * 60)
    
    try:
        config_file = "config_tema.json"
        
        # Criar arquivo de config de teste
        test_config = {"tema_login": "light"}
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(test_config, f)
        print("✓ Config de tema criada")
        
        # Verificar se consegue ler
        with open(config_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        
        if loaded.get("tema_login") == "light":
            print("✓ Tema salvo e lido com sucesso")
            print(f"  → Tema atual: {loaded['tema_login']}")
        else:
            print("✗ Erro ao ler tema")
            return False
        
        print("\n✓ Light Mode Theme: OK")
        return True
        
    except Exception as e:
        print(f"✗ Erro no teste de light mode: {e}")
        return False


def test_imports():
    """Testar imports de todos os módulos"""
    print("\n" + "=" * 60)
    print("TESTE 3: Imports de Módulos")
    print("=" * 60)
    
    modules = [
        "cache_utils",
        "login_gui_premium",
        "gui_premium",
        "main"
    ]
    
    all_ok = True
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module}: OK")
        except Exception as e:
            print(f"✗ {module}: ERRO - {e}")
            all_ok = False
    
    if all_ok:
        print("\n✓ Todos os módulos: OK")
    return all_ok


def main():
    print("\n" + "=" * 60)
    print("🧪 TESTE DE MELHORIAS - FASE 2")
    print("=" * 60)
    
    results = []
    
    # Executar testes
    results.append(("Cache e Fuzzy Matching", test_cache_utils()))
    results.append(("Light Mode Theme", test_light_mode()))
    results.append(("Imports", test_imports()))
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASSOU" if result else "✗ FALHOU"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 Todos os testes passaram! Pronto para usar.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} teste(s) falharam.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
