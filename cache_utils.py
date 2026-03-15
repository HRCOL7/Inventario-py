# ===============================
# IKARUS INVENTORY - Cache e Busca Otimizada
# ===============================

import re
from typing import Dict, List, Tuple
from functools import lru_cache
from difflib import SequenceMatcher

class CacheProducts:
    """Cache simples para produtos com busca otimizada"""
    
    def __init__(self, mapeamento: dict):
        self.mapeamento = mapeamento
        self._cache_indices = {}
        self._build_indices()
    
    def _build_indices(self):
        """Constrói índices para busca rápida"""
        self._cache_indices = {
            'codigo_barra': {},
            'codigo_interno': {},
            'nome': {},
            'full': []
        }
        
        for cb, (ci, nm, grupo) in self.mapeamento.items():
            # Índice por código de barras
            self._cache_indices['codigo_barra'][cb.lower()] = (cb, ci, nm, grupo)
            
            # Índice por código interno
            self._cache_indices['codigo_interno'][ci.lower()] = (cb, ci, nm, grupo)
            
            # Índice por nome
            nome_norm = nm.lower()
            if nome_norm not in self._cache_indices['nome']:
                self._cache_indices['nome'][nome_norm] = []
            self._cache_indices['nome'][nome_norm].append((cb, ci, nm, grupo))
            
            # Lista completa para busca fuzzy
            self._cache_indices['full'].append((cb, ci, nm, grupo))
    
    def busca_exata(self, termo: str, campo: str = 'interno') -> List[Tuple]:
        """Busca exata rápida usando índices"""
        termo = termo.strip().lower()
        if not termo:
            return []
        
        if campo == 'codigo_barra':
            if termo in self._cache_indices['codigo_barra']:
                return [self._cache_indices['codigo_barra'][termo]]
        elif campo == 'codigo_interno':
            if termo in self._cache_indices['codigo_interno']:
                return [self._cache_indices['codigo_interno'][termo]]
        elif campo == 'nome':
            resultados = []
            for nome_idx, produtos in self._cache_indices['nome'].items():
                if termo in nome_idx:
                    resultados.extend(produtos)
            return resultados[:50]
        
        return []
    
    def busca_fuzzy(self, termo: str, campo: str = 'nome', limiar: float = 0.6) -> List[Tuple]:
        """Busca fuzzy com correspondência aproximada"""
        termo = termo.strip().lower()
        if not termo:
            return []
        resultados = []

        def _tokenize(text: str) -> List[str]:
            return [t for t in re.split(r"[^0-9a-zA-Z]+", text) if t]

        def _normalize(text: str) -> str:
            return text.lower().strip()

        def _score_similarity(a: str, b: str) -> float:
            """Calcula uma pontuação de similaridade mais robusta, com atenção a tokens.

            Mistura SequenceMatcher com matching por tokens e Jaccard para favorecer
            correspondências parciais por palavras (útil para descrições).
            """
            a_n = _normalize(a)
            b_n = _normalize(b)

            # sequência pura
            seq = SequenceMatcher(None, a_n, b_n).ratio()

            # tokens
            tokens_a = set(_tokenize(a_n))
            tokens_b = set(_tokenize(b_n))
            if tokens_a or tokens_b:
                inter = tokens_a.intersection(tokens_b)
                union = tokens_a.union(tokens_b)
                jaccard = len(inter) / len(union) if union else 0.0
            else:
                jaccard = 0.0

            # melhor score com qualquer token individual
            token_max = 0.0
            for t in tokens_b:
                token_max = max(token_max, SequenceMatcher(None, a_n, t).ratio())

            # combinar métricas - damos mais peso a matches por token para nomes
            score = max(seq, token_max * 0.9 + jaccard * 0.4, 0.6 * jaccard + 0.4 * seq)
            return score

        # Ajuste de limiar um pouco mais permissivo para nome/descrição
        if campo == 'nome' and limiar < 0.45:
            limiar = 0.45

        for cb, ci, nm, grupo in self._cache_indices['full']:
            if campo == 'nome':
                alvo = nm.lower()
            elif campo == 'codigo_interno':
                alvo = ci.lower()
            elif campo == 'codigo_barra':
                alvo = cb.lower()
            else:
                alvo = nm.lower()

            similaridade = _score_similarity(termo, alvo)

            if similaridade >= limiar:
                resultados.append((similaridade, cb, ci, nm, grupo))

        # Ordenar por similaridade decrescente
        resultados.sort(key=lambda x: x[0], reverse=True)

        # Retornar apenas os dados sem a pontuação
        return [(cb, ci, nm, grupo) for _, cb, ci, nm, grupo in resultados[:50]]
    
    def busca_prefixo(self, termo: str, campo: str = 'nome') -> List[Tuple]:
        """Busca por prefixo (primeira letra/caracteres)"""
        termo = termo.strip().lower()
        if not termo:
            return []
        
        resultados = []
        
        for cb, ci, nm, grupo in self._cache_indices['full']:
            if campo == 'nome':
                alvo = nm.lower()
            elif campo == 'codigo_interno':
                alvo = ci.lower()
            elif campo == 'codigo_barra':
                alvo = cb.lower()
            else:
                alvo = nm.lower()
            
            if alvo.startswith(termo):
                resultados.append((cb, ci, nm, grupo))
        
        return resultados[:50]
    
    def busca_combinada(self, termo: str, campo: str = 'nome') -> List[Tuple]:
        """Busca combinada: prefixo + fuzzy + substring"""
        termo = termo.strip().lower()
        if not termo:
            return []
        # Priorizar correspondência exata quando for código interno ou de barras
        resultado = []
        seen = set()

        if campo in ('codigo_interno', 'codigo_barra'):
            # verificar correspondência exata no índice
            idx_key = 'codigo_interno' if campo == 'codigo_interno' else 'codigo_barra'
            exact = self._cache_indices.get(idx_key, {}).get(termo)
            if exact:
                # exact é um único tuple (cb, ci, nm, grupo)
                key = (exact[0], exact[1])
                resultado.append(exact)
                seen.add(key)

        # Primeiro: prefixo (mais relevante)
        prefixo = self.busca_prefixo(termo, campo)
        # Segundo: fuzzy (aproximado) - para nomes reduzimos limiar para pegar aproximações
        fuzzy_limiar = 0.6 if campo != 'nome' else 0.45
        fuzzy = self.busca_fuzzy(termo, campo, limiar=fuzzy_limiar)

        # Se o termo contiver múltiplas palavras, priorizar itens que contenham
        # todas as tokens (mesmo fora de ordem) — útil para descrições.
        multi_tokens = [t for t in re.split(r"[^0-9a-zA-Z]+", termo) if t]
        exact_tokens_matches = []
        if campo == 'nome' and len(multi_tokens) > 1:
            for cb, ci, nm, grupo in self._cache_indices['full']:
                nome_tokens = set([t for t in re.split(r"[^0-9a-zA-Z]+", nm.lower()) if t])
                if all(tok in nome_tokens for tok in multi_tokens):
                    key = (cb, ci)
                    if key not in seen:
                        exact_tokens_matches.append((cb, ci, nm, grupo))
                        seen.add(key)

        # Combinar sem duplicatas, mantendo ordem: exact, prefixo, fuzzy
        # Inserir antes do prefixo os matches por tokens completos (mais relevantes)
        for item in exact_tokens_matches:
            resultado.append(item)

        # Combinar sem duplicatas, mantendo ordem: exact, prefixo, fuzzy
        for cb, ci, nm, grupo in prefixo:
            key = (cb, ci)
            if key not in seen:
                resultado.append((cb, ci, nm, grupo))
                seen.add(key)

        for cb, ci, nm, grupo in fuzzy:
            key = (cb, ci)
            if key not in seen:
                resultado.append((cb, ci, nm, grupo))
                seen.add(key)

        return resultado[:50]


class KeyboardShortcuts:
    """Gerenciador de atalhos de teclado com exibição visual"""
    
    SHORTCUTS = {
        'ctrl+s': ('Salvar', 'Ctrl+S'),
        'ctrl+q': ('Sair', 'Ctrl+Q'),
        'ctrl+f': ('Buscar', 'Ctrl+F'),
        'ctrl+n': ('Novo Produto', 'Ctrl+N'),
        'ctrl+e': ('Exportar', 'Ctrl+E'),
        'ctrl+l': ('Limpar', 'Ctrl+L'),
        'f1': ('Ajuda', 'F1'),
        'f5': ('Atualizar', 'F5'),
        'tab': ('Próximo Campo', 'Tab'),
        'shift+tab': ('Campo Anterior', 'Shift+Tab'),
        'enter': ('Confirmar', 'Enter'),
        'esc': ('Cancelar', 'Esc'),
    }
    
    @staticmethod
    def get_shortcut_text(acao: str) -> str:
        """Retorna o texto do atalho para uma ação"""
        for key, (desc, display) in KeyboardShortcuts.SHORTCUTS.items():
            if desc.lower() == acao.lower():
                return display
        return ""
    
    @staticmethod
    def get_all_shortcuts() -> Dict[str, str]:
        """Retorna todos os atalhos formatados"""
        return {desc: display for _, (desc, display) in KeyboardShortcuts.SHORTCUTS.items()}
    
    @staticmethod
    def format_shortcuts_help() -> str:
        """Formata lista de atalhos para exibir na tela"""
        shortcuts_text = "Atalhos de Teclado:\n\n"
        for desc, display in KeyboardShortcuts.SHORTCUTS.items():
            shortcuts_text += f"  {display:15} → {desc}\n"
        return shortcuts_text
