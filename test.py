#!/usr/bin/env python3
"""
Inventário - GUI + Exportação
Unifica leitura do Excel (mapeamento), contagem por bip (scanner), listagem em tela,
e exportação final para:
 - contagem.txt       (CodigoInterno|Quantidade)n
 - contagem_detalhada.csv (CodigoInterno,Quantidade,Nome)
 - nao_mapeados.csv   (CodigoBarra,Quantidade)  -- se houver

Salvar como: inventario_gui.py
Uso:
  python inventario_gui.py                # usa produtos.xlsx (1ª aba)
  python inventario_gui.py arquivo.xlsx   # usa arquivo.xlsx (1ª aba)
  python inventario_gui.py arquivo.xlsx AbaNome
"""

import sys
import re
import os
from collections import defaultdict, Counter
from typing import Optional
import pandas as pd
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

# ---------- Configurações ----------
ARQUIVO_EXCEL_PADRAO = "produtos.xlsx"
ABA_EXCEL_PADRAO = None
ARQUIVO_TXT_SAIDA = "contagem.txt"
ARQUIVO_CSV_DETALHADO = "contagem_detalhada.csv"
ARQUIVO_CSV_NAO_MAPEADOS = "nao_mapeados.csv"

MOSTRAR_TOP_N_RESUMO = 10

SINONIMOS_COLUNAS = {
    "CodigoBarra": [
        "codigobarra", "codigo_barra", "cod_barra", "cod_barras", "codigo de barras",
        "codbarras", "código de barras", "barcode", "ean", "codigo_barras", "codigo barras",
        "codigo de barra"
    ],
    "CodigoInterno": [
        "codigointerno", "codigo_interno", "codinterno", "codigo", "sku", "código interno",
        "ref interna"
    ],
    "Nome": [
        "nome", "descricao", "descrição", "produto", "nome_produto", "nome produto"
    ],
}


# ---------- Utilitários para planilha / mapeamento ----------
def normaliza_rotulo(s: str) -> str:
    return re.sub(r"[\W_]+", " ", str(s).strip().lower())


def encontrar_coluna(df: pd.DataFrame, alvo: str) -> Optional[str]:
    candidatos = [alvo.lower()] + SINONIMOS_COLUNAS.get(alvo, [])
    candidatos = [normaliza_rotulo(x) for x in candidatos]
    normal_por_original = {normaliza_rotulo(col): col for col in df.columns}
    for cand in candidatos:
        if cand in normal_por_original:
            return normal_por_original[cand]
    return None


def carregar_mapeamento(caminho_excel: str, aba: Optional[str] = None):
    if not os.path.exists(caminho_excel):
        messagebox.showerror("Erro", f"Não encontrei o arquivo Excel: {caminho_excel}")
        sys.exit(1)

    try:
        # engine openpyxl é recomendado para xlsx
        df = pd.read_excel(caminho_excel, sheet_name=aba, engine="openpyxl")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao ler o Excel: {e}")
        sys.exit(1)

    if isinstance(df, dict):
        # pegar primeira aba
        df = next(iter(df.values()))

    col_cb = encontrar_coluna(df, "CodigoBarra")
    col_ci = encontrar_coluna(df, "CodigoInterno")
    col_nm = encontrar_coluna(df, "Nome")

    faltando = [lab for lab, col in [("CodigoBarra", col_cb), ("CodigoInterno", col_ci), ("Nome", col_nm)] if col is None]
    if faltando:
        messagebox.showerror(
            "Erro",
            "Não encontrei as seguintes colunas na planilha: " + ", ".join(faltando) +
            "\nVerifique os cabeçalhos ou use nomes/sinônimos esperados."
        )
        sys.exit(1)

    # garantir string e strip
    df[col_cb] = df[col_cb].astype(str).str.strip()
    df[col_ci] = df[col_ci].astype(str).str.strip()
    df[col_nm] = df[col_nm].astype(str).str.strip()

    mapeamento = {}
    duplicados = []
    for _, row in df.iterrows():
        cb = row[col_cb]
        ci = row[col_ci]
        nm = row[col_nm]
        if not cb or cb.lower() in ("nan", "none"):
            continue
        if cb in mapeamento:
            if mapeamento[cb][0] != ci:
                duplicados.append((cb, mapeamento[cb][0], ci))
            # mantemos o primeiro
        else:
            mapeamento[cb] = (ci, nm)

    if duplicados:
        # exibir um aviso simples (não bloqueante)
        msg = "Existem códigos de barras repetidos apontando para códigos internos diferentes.\nForam mantidos os primeiros encontrados.\nExemplos:\n"
        msg += "\n".join([f"{cb}: {old} vs {new}" for cb, old, new in duplicados[:10]])
        if len(duplicados) > 10:
            msg += f"\n(+ {len(duplicados)-10} ocorrências adicionais...)"
        messagebox.showwarning("Aviso - duplicados", msg)

    return mapeamento


# ---------- Sons simples (Windows winsound fallback para bell) ----------
def beep_ok():
    try:
        import winsound
        winsound.Beep(880, 70)
    except Exception:
        try:
            # fallback: terminal bell
            print("\a", end="", flush=True)
        except Exception:
            pass


def beep_erro():
    try:
        import winsound
        winsound.Beep(220, 120)
    except Exception:
        try:
            print("\a", end="", flush=True)
        except Exception:
            pass


# ---------- Exportação ----------
def exportar(contagem_por_cb: Counter, nao_mapeados: Counter, mapeamento: dict):
    agreg_interno = defaultdict(int)
    nome_por_interno = {}
    for cb, qtd in contagem_por_cb.items():
        if cb in mapeamento and qtd > 0:
            ci, nm = mapeamento[cb]
            agreg_interno[ci] += qtd
            if ci not in nome_por_interno:
                nome_por_interno[ci] = nm

    # TXT: CodigoInterno|Quantidade
    linhas_txt = [f"{ci}|{agreg_interno[ci]}" for ci in sorted(agreg_interno.keys())]
    with open(ARQUIVO_TXT_SAIDA, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_txt) + ("\n" if linhas_txt else ""))

    # CSV detalhado
    df_detalhe = pd.DataFrame(
        [{"CodigoInterno": ci, "Quantidade": qtd, "Nome": nome_por_interno.get(ci, "")}
         for ci, qtd in sorted(agreg_interno.items())]
    )
    df_detalhe.to_csv(ARQUIVO_CSV_DETALHADO, index=False, encoding="utf-8")

    # Não mapeados
    if nao_mapeados:
        df_nao = pd.DataFrame(
            [{"CodigoBarra": cb, "Quantidade": qtd} for cb, qtd in sorted(nao_mapeados.items())]
        )
        df_nao.to_csv(ARQUIVO_CSV_NAO_MAPEADOS, index=False, encoding="utf-8")


# ---------- Interface gráfica ----------
class InventarioGUI:
    def __init__(self, root: tk.Tk, mapeamento: dict):
        self.root = root
        self.mapeamento = mapeamento

        self.contagem_por_cb = Counter()
        self.nao_mapeados = Counter()
        self.cbs_ordem = []  # ordem de aparecimento para "Próximo"

        # Variáveis Tk
        self.codigo_atual = tk.StringVar()
        self.quantidade_atual = tk.IntVar(value=0)
        self.nome_produto = tk.StringVar()

        # --- Layout ---
        self.root.title("Inventário - Contagem de Produtos")
        self.root.geometry("820x560")

        # Top frame: entrada + info
        top = tk.Frame(root, padx=8, pady=8)
        top.pack(fill=tk.X)

        lbl_cb = tk.Label(top, text="CÓDIGO DE BARRAS:", anchor="w")
        lbl_cb.grid(row=0, column=0, sticky="w")
        self.entrada_cb = tk.Entry(top, textvariable=self.codigo_atual, width=40, font=("TkDefaultFont", 12))
        self.entrada_cb.grid(row=0, column=1, sticky="w")
        self.entrada_cb.focus()

        btn_proximo = tk.Button(top, text="Próximo (Tab)", command=self.proximo_cb)
        btn_proximo.grid(row=0, column=2, padx=6)

        lbl_nome = tk.Label(top, text="NOME DO PRODUTO:", anchor="w")
        lbl_nome.grid(row=1, column=0, sticky="w", pady=(8, 0))
        lbl_nome_val = tk.Label(top, textvariable=self.nome_produto, anchor="w", fg="blue")
        lbl_nome_val.grid(row=1, column=1, sticky="w", columnspan=2, pady=(8, 0))

        lbl_qtd = tk.Label(top, text="QUANTIDADE:", anchor="w")
        lbl_qtd.grid(row=2, column=0, sticky="w", pady=(8, 0))
        lbl_qtd_val = tk.Label(top, textvariable=self.quantidade_atual, font=("Arial", 28, "bold"))
        lbl_qtd_val.grid(row=2, column=1, sticky="w", pady=(8, 0))

        # Middle: listagem com cabeçalho
        mid = tk.Frame(root, padx=8, pady=6)
        mid.pack(fill=tk.BOTH, expand=True)

        lbl_lista = tk.Label(mid, text="Produtos Contados (clicar para editar/remover):")
        lbl_lista.pack(anchor="w")

        # Treeview para melhor apresentação (colunas: Código Interno/Barra, Nome, Quantidade)
        columns = ("interno", "barra", "nome", "qtd")
        self.tree = ttk.Treeview(mid, columns=columns, show="headings", height=18)
        self.tree.heading("interno", text="Código Interno")
        self.tree.heading("barra", text="Código de Barras")
        self.tree.heading("nome", text="Nome do Produto")
        self.tree.heading("qtd", text="Quantidade")
        self.tree.column("interno", width=130, anchor="w")
        self.tree.column("barra", width=170, anchor="w")
        self.tree.column("nome", width=380, anchor="w")
        self.tree.column("qtd", width=80, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True, pady=(4, 8))

        # Bind duplo clique para ajustar (set/remove)
        self.tree.bind("<Double-1>", self._on_tree_double_click)

        # Bottom: botões
        bot = tk.Frame(root, pady=8)
        bot.pack(fill=tk.X)

        tk.Button(bot, text="+ Adicionar (Enter)", command=self.adicionar).grid(row=0, column=0, padx=6)
        tk.Button(bot, text="- Remover", command=self.remover).grid(row=0, column=1, padx=6)
        tk.Button(bot, text="Resumo (Ctrl+F1)", command=self.mostrar_resumo).grid(row=0, column=2, padx=6)
        tk.Button(bot, text="Total (Ctrl+F2)", command=self.mostrar_total).grid(row=0, column=3, padx=6)
        tk.Button(bot, text="Finalizar (Ctrl+F3)", command=self.finalizar).grid(row=0, column=4, padx=6)
        tk.Button(bot, text="Limpar Lista", command=self.limpar_contagem).grid(row=0, column=5, padx=6)

        # Atalhos - scanner geralmente envia Enter ao final do código
        root.bind("<Return>", self.processar_cb)  # soma automático ao bipar (ou Enter)
        root.bind("<Tab>", lambda e: self.proximo_cb())
        root.bind("<Control-F1>", lambda e: self.mostrar_resumo())
        root.bind("<Control-F2>", lambda e: self.mostrar_total())
        root.bind("<Control-F3>", lambda e: self.finalizar())

        # inicialização da tree (vazia)
        self.atualizar_lista()

    # -------------------- funcionalidades --------------------
    def processar_cb(self, event=None):
        """
        Chamado ao pressionar Enter (scanner normalmente envia Enter).
        Faz +1 automático e atualiza interface.
        """
        cb = self.codigo_atual.get().strip()
        if not cb:
            return "break"  # evita navegação de foco pelo Tk
        if cb in self.mapeamento:
            self.contagem_por_cb[cb] += 1
            ci, nm = self.mapeamento[cb]
            if cb not in self.cbs_ordem:
                self.cbs_ordem.append(cb)
            self.nome_produto.set(nm)
            self.quantidade_atual.set(self.contagem_por_cb[cb])
            beep_ok()
        else:
            self.nao_mapeados[cb] += 1
            self.nome_produto.set("NÃO MAPEADO!")
            self.quantidade_atual.set(self.nao_mapeados[cb])
            beep_erro()
        self.codigo_atual.set("")  # limpa campo para próximo bip
        self.atualizar_lista()
        return "break"

    def adicionar(self):
        """Botão manual +1"""
        cb = self.codigo_atual.get().strip()
        if not cb:
            messagebox.showinfo("Info", "Digite ou bipes um código primeiro.")
            return
        if cb in self.mapeamento:
            self.contagem_por_cb[cb] += 1
            ci, nm = self.mapeamento[cb]
            self.nome_produto.set(nm)
            self.quantidade_atual.set(self.contagem_por_cb[cb])
            beep_ok()
        else:
            self.nao_mapeados[cb] += 1
            self.nome_produto.set("NÃO MAPEADO!")
            self.quantidade_atual.set(self.nao_mapeados[cb])
            beep_erro()
        if cb not in self.cbs_ordem:
            self.cbs_ordem.append(cb)
        self.codigo_atual.set("")
        self.atualizar_lista()

    def remover(self):
        """Botão manual -1 no código atual"""
        cb = self.codigo_atual.get().strip()
        if not cb:
            messagebox.showinfo("Info", "Digite ou selecione um código para remover.")
            return
        if cb in self.mapeamento and self.contagem_por_cb[cb] > 0:
            self.contagem_por_cb[cb] -= 1
            self.quantidade_atual.set(self.contagem_por_cb[cb])
            beep_ok()
        elif cb not in self.mapeamento and self.nao_mapeados[cb] > 0:
            self.nao_mapeados[cb] -= 1
            self.quantidade_atual.set(self.nao_mapeados[cb])
            beep_erro()
        else:
            messagebox.showinfo("Info", "Nada para remover nesse código.")
        self.atualizar_lista()

    def proximo_cb(self):
        """Avança para o próximo CB já registrado"""
        if not self.cbs_ordem:
            return
        atual = self.codigo_atual.get().strip()
        try:
            idx = self.cbs_ordem.index(atual)
            idx = (idx + 1) % len(self.cbs_ordem)
        except ValueError:
            idx = 0
        self.codigo_atual.set(self.cbs_ordem[idx])
        # atualiza nome/qtd exibidos
        self.buscar_cb()

    def buscar_cb(self, event=None):
        cb = self.codigo_atual.get().strip()
        if not cb:
            self.nome_produto.set("")
            self.quantidade_atual.set(0)
            return
        if cb in self.mapeamento:
            self.nome_produto.set(self.mapeamento[cb][1])
            self.quantidade_atual.set(self.contagem_por_cb[cb])
        else:
            self.nome_produto.set("NÃO MAPEADO!")
            self.quantidade_atual.set(self.nao_mapeados[cb])

    def atualizar_lista(self):
        """Atualiza o Treeview com todos os itens contados (mapeados + não mapeados)"""
        # limpar
        for r in self.tree.get_children():
            self.tree.delete(r)
        # mapeados (ordenados por CodigoInterno)
        # organizar map: interno -> list of barras (mas exibiremos por barra)
        # exibiremos cada barra em linha (útil para inspeção)
        for cb, qtd in sorted(self.contagem_por_cb.items(), key=lambda x: (-x[1], x[0])):
            if qtd <= 0:
                continue
            if cb in self.mapeamento:
                ci, nm = self.mapeamento[cb]
                self.tree.insert("", tk.END, values=(ci, cb, nm, qtd))
            else:
                # no improbable case, contagem_por_cb only contains mapped normally
                self.tree.insert("", tk.END, values=("", cb, "(SEM MAPEAMENTO)", qtd))
        # não mapeados
        for cb, qtd in sorted(self.nao_mapeados.items(), key=lambda x: (-x[1], x[0])):
            if qtd <= 0:
                continue
            self.tree.insert("", tk.END, values=("", cb, "(NÃO MAPEADO)", qtd))

    def mostrar_resumo(self):
        por_interno = defaultdict(int)
        for cb, qtd in self.contagem_por_cb.items():
            if cb in self.mapeamento:
                ci, _ = self.mapeamento[cb]
                por_interno[ci] += qtd
        top = sorted(por_interno.items(), key=lambda x: x[1], reverse=True)[:MOSTRAR_TOP_N_RESUMO]
        if not top:
            messagebox.showinfo("Resumo", "(vazio)")
            return
        mensagem = "\n".join([f"{ci}: {qtd}" for ci, qtd in top])
        messagebox.showinfo("Resumo - TOP itens (por Código Interno)", mensagem)

    def mostrar_total(self):
        total = sum(self.contagem_por_cb.values()) + sum(self.nao_mapeados.values())
        messagebox.showinfo("Total de Unidades", f"Total: {total}")

    def limpar_contagem(self):
        if messagebox.askyesno("Confirmar", "Limpar todas as contagens atuais?"):
            self.contagem_por_cb.clear()
            self.nao_mapeados.clear()
            self.cbs_ordem.clear()
            self.codigo_atual.set("")
            self.nome_produto.set("")
            self.quantidade_atual.set(0)
            self.atualizar_lista()

    def _on_tree_double_click(self, event):
        """
        Ao dar duplo clique numa linha, permitir:
         - setar uma quantidade
         - decrementar 1
         - remover o registro
        """
        item = self.tree.identify_row(event.y)
        if not item:
            return
        vals = self.tree.item(item, "values")
        # (interno, barra, nome, qtd)
        barra = vals[1]
        if not barra:
            messagebox.showinfo("Editar", "Não foi possível identificar o código de barras nessa linha.")
            return

        opc = simpledialog.askstring("Editar item",
                                     f"Opções para {barra}:\n  digite 'del' para -1\n  digite um número para SETAR quantidade\n  ou deixe em branco para cancelar\n\nDigite aqui:")
        if opc is None or opc.strip() == "":
            return
        opc = opc.strip()
        if opc.lower() == "del":
            # remover 1
            if barra in self.mapeamento:
                if self.contagem_por_cb[barra] > 0:
                    self.contagem_por_cb[barra] -= 1
            else:
                if self.nao_mapeados[barra] > 0:
                    self.nao_mapeados[barra] -= 1
            self.atualizar_lista()
            return
        # tentar interpretar como inteiro ->
        try:
            v = int(opc)
            if v < 0:
                messagebox.showinfo("Inválido", "Quantidade deve ser >= 0")
                return
            if barra in self.mapeamento:
                self.contagem_por_cb[barra] = v
            else:
                self.nao_mapeados[barra] = v
            self.atualizar_lista()
        except ValueError:
            messagebox.showinfo("Inválido", "Entrada inválida. Use 'del' ou número inteiro.")

    def finalizar(self):
        if not messagebox.askyesno("Finalizar", "Finalizar e exportar arquivos?"):
            return
        exportar(self.contagem_por_cb, self.nao_mapeados, self.mapeamento)
        msg = "Exportação concluída.\nArquivos gerados:\n - " + ARQUIVO_TXT_SAIDA + "\n - " + ARQUIVO_CSV_DETALHADO
        if self.nao_mapeados:
            msg += "\n - " + ARQUIVO_CSV_NAO_MAPEADOS
        messagebox.showinfo("Finalizado", msg)
        self.root.quit()


# ---------- Modo CLI (opcional) ----------
def modo_cli(mapeamento):
    """
    Mantive também a versão CLI (derivado do seu script original),
    caso queira rodar em terminal. Não necessário se você quer só GUI.
    """
    print("Modo CLI iniciado. Digite 'help' para comandos, 'fim' para exportar.")
    contagem_por_cb = Counter()
    nao_mapeados = Counter()

    def imprimir_ajuda():
        print("""
Comandos:
  resumo           - mostra TOP itens (por código interno)
  total            - mostra total geral
  del <cb>         - remove 1 unidade desse codigo de barras
  set <cb> <q>     - define qtde daquele codigo de barras
  help             - mostra esta ajuda
  fim              - finaliza e exporta
""".strip())

    while True:
        try:
            entrada = input("Bipe/Comando: ").strip()
        except (EOFError, KeyboardInterrupt):
            entrada = "fim"
        if not entrada:
            continue
        if entrada.lower() == "help":
            imprimir_ajuda()
            continue
        if entrada.lower() == "resumo":
            por_interno = defaultdict(int)
            for cb, qtd in contagem_por_cb.items():
                if cb in mapeamento:
                    ci, _ = mapeamento[cb]
                    por_interno[ci] += qtd
            top = sorted(por_interno.items(), key=lambda x: x[1], reverse=True)[:MOSTRAR_TOP_N_RESUMO]
            print("TOP itens:")
            for ci, qtd in top:
                print(f"  {ci}: {qtd}")
            continue
        if entrada.lower() == "total":
            print("Total:", sum(contagem_por_cb.values()) + sum(nao_mapeados.values()))
            continue
        if entrada.lower().startswith("del "):
            cb = entrada[4:].strip()
            if cb in contagem_por_cb and contagem_por_cb[cb] > 0:
                contagem_por_cb[cb] -= 1
                print(f"Removido 1 de {cb}. Agora: {contagem_por_cb[cb]}")
                beep_ok()
            else:
                print("Nada para remover.")
                beep_erro()
            continue
        if entrada.lower().startswith("set "):
            partes = entrada.split()
            if len(partes) != 3:
                print("Uso: set <codigo> <quantidade>")
                continue
            cb, qtd_txt = partes[1], partes[2]
            try:
                qtd = int(qtd_txt)
                if qtd < 0:
                    raise ValueError()
            except ValueError:
                print("Quantidade inválida.")
                continue
            contagem_por_cb[cb] = qtd
            if cb not in mapeamento:
                nao_mapeados[cb] += 0
                print(f"Atenção: {cb} não está mapeado.")
                beep_erro()
            else:
                ci, nm = mapeamento[cb]
                print(f"Definido: {nm} ({ci}) = {qtd}")
                beep_ok()
            continue
        if entrada.lower() == "fim":
            break

        # tratar como barcode
        codigo_barras = entrada
        if codigo_barras in mapeamento:
            contagem_por_cb[codigo_barras] += 1
            ci, nm = mapeamento[codigo_barras]
            print(f"+1  {nm}  ({ci})  -> total desse CB: {contagem_por_cb[codigo_barras]}")
            beep_ok()
        else:
            nao_mapeados[codigo_barras] += 1
            print(f"⚠️ Não mapeado: {codigo_barras}")
            beep_erro()

    # exportar
    exportar(contagem_por_cb, nao_mapeados, mapeamento)
    print("Exportado. Arquivos gerados:")
    print(" -", ARQUIVO_TXT_SAIDA)
    print(" -", ARQUIVO_CSV_DETALHADO)
    if nao_mapeados:
        print(" -", ARQUIVO_CSV_NAO_MAPEADOS)


# ---------- Main ----------
def main():
    # argumentos: [arquivo.xlsx] [aba] [--cli]
    caminho_excel = ARQUIVO_EXCEL_PADRAO
    aba = ABA_EXCEL_PADRAO
    usar_cli = False

    args = sys.argv[1:]
    # detectar --cli
    if "--cli" in args:
        usar_cli = True
        args.remove("--cli")

    if len(args) >= 1:
        caminho_excel = args[0]
    if len(args) >= 2:
        aba = args[1]

    mapeamento = carregar_mapeamento(caminho_excel, aba)
    if usar_cli:
        modo_cli(mapeamento)
    else:
        root = tk.Tk()
        app = InventarioGUI(root, mapeamento)
        root.mainloop()


if __name__ == "__main__":
    main()
