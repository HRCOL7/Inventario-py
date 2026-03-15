# ===============================
# IKARUS INVENTORY - Controle de Estoque
# Versão personalizada PRO
# ===============================
#
# Este script implementa um sistema de inventário com interface gráfica (Tkinter),
# controle de usuários, exportação de relatórios e funcionalidades de pesquisa.
#
# Estrutura principal:
# 1. Configurações e utilitários
# 2. Funções de manipulação de usuários
# 3. Funções de manipulação de planilhas
# 4. Funções de exportação
# 5. Interface gráfica (classe InventarioGUI)
# 6. Funções auxiliares da GUI
# 7. Função principal (main)
# ===============================



# === 1. IMPORTAÇÕES E CONFIGURAÇÕES ===
import sys
import re
import os
from collections import defaultdict, Counter
from typing import Optional, Tuple
from datetime import datetime
import logging


# Bibliotecas externas
import pandas as pd
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk


# PDF opcional
try:
    from fpdf import FPDF
    PDF_OK = True
except ImportError:
    PDF_OK = False

import json
import hashlib


# === 2. CONFIGURAÇÕES GERAIS ===
ARQUIVO_USUARIOS = "usuarios.json"

"""
Funções de manipulação de usuários (cadastro, autenticação, alteração de senha, etc)
"""
def carregar_usuarios():
    if not os.path.exists(ARQUIVO_USUARIOS):
        return []
    with open(ARQUIVO_USUARIOS, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_usuarios(usuarios):
    with open(ARQUIVO_USUARIOS, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)

def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def cadastrar_usuario(usuario, senha):
    usuarios = carregar_usuarios()
    if any(u["usuario"] == usuario for u in usuarios):
        return False  # já existe
    usuarios.append({"usuario": usuario, "senha": hash_senha(senha), "senha_original": senha})
    salvar_usuarios(usuarios)
    return True

def autenticar(usuario, senha):
    usuarios = carregar_usuarios()
    senha_hash = hash_senha(senha)
    for u in usuarios:
        if u["usuario"] == usuario and u["senha"] == senha_hash:
            return True
    return False


# === 3. CONFIGURAÇÕES DE ARQUIVOS E COLUNAS ===
ARQUIVO_EXCEL_PADRAO = "Produtos Box.xlsx"  # Arquivo principal de produtos
ABA_EXCEL_PADRAO = None
ARQUIVO_TXT_SAIDA = "contagem.txt"
ARQUIVO_XLSX_SAIDA = "contagem.xlsx"
ARQUIVO_CSV_DETALHADO = "contagem_detalhada.csv"
ARQUIVO_CSV_NAO_MAPEADOS = "nao_mapeados.csv"
ARQUIVO_BACKUP = "contagem_backup.txt"
ARQUIVO_LOG = "contagem.log"

MOSTRAR_TOP_N_RESUMO = 10
SENHA_FINALIZAR = "733721"
INTERVALO_AUTOSAVE_MS = 120_000  # 2 minutos

# Sinônimos para identificar colunas no Excel
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

"""
Funções de logging para registrar ações do usuário e eventos do sistema
"""
def configurar_logger():
    logger = logging.getLogger("inventario")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler(ARQUIVO_LOG, encoding="utf-8")
        fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger

LOGGER = configurar_logger()

def log(acao: str, detalhe: str = ""):
    try:
        LOGGER.info(f"{acao} | {detalhe}")
    except Exception:
        pass

# ---------- Utilitários para planilha ----------
"""
Funções utilitárias para manipulação de planilhas e normalização de dados
"""
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
        raise FileNotFoundError(f"Não encontrei o arquivo Excel: {caminho_excel}")

    try:
        df = pd.read_excel(caminho_excel, sheet_name=aba, engine="openpyxl")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao ler o Excel: {e}")
        raise

    if isinstance(df, dict):
        df = next(iter(df.values()))

    col_cb = encontrar_coluna(df, "CodigoBarra")
    col_ci = encontrar_coluna(df, "CodigoInterno")
    col_nm = encontrar_coluna(df, "Nome")
    col_grupo = encontrar_coluna(df, "Grupo")

    if not all([col_cb, col_ci, col_nm]):
        messagebox.showerror("Erro", "Não encontrei todas as colunas necessárias (CodigoBarra, CodigoInterno, Nome)")
        raise Exception("Colunas necessárias não encontradas")

    df[col_cb] = df[col_cb].astype(str).str.strip()
    df[col_ci] = df[col_ci].astype(str).str.strip()
    df[col_nm] = df[col_nm].astype(str).str.strip()
    if col_grupo:
        df[col_grupo] = df[col_grupo].astype(str).str.strip()

    mapeamento = {}
    for _, row in df.iterrows():
        cb, ci, nm = row[col_cb], row[col_ci], row[col_nm]
        grupo = row[col_grupo] if col_grupo else ""
        if cb:
            mapeamento[cb] = (ci, nm, grupo)
    return mapeamento

"""
Funções para emitir sons de feedback (beep) ao usuário
"""
def beep_ok():
    try:
        import winsound
        winsound.Beep(880, 70)
    except Exception:
        print("\a", end="", flush=True)

def beep_erro():
    try:
        import winsound
        winsound.Beep(220, 120)
    except Exception:
        print("\a", end="", flush=True)

"""
Funções de exportação de relatórios (TXT, XLSX, CSV, PDF)
"""
def exportar_txt_formatado(contagem_por_cb: Counter, mapeamento: dict, arquivo: str):
    agreg_interno = defaultdict(int)
    for cb, qtd in contagem_por_cb.items():
        if cb in mapeamento and qtd > 0:
            ci, _ = mapeamento[cb][:2]
            agreg_interno[ci] += qtd
    linhas = [f"{ci} | {agreg_interno[ci]}" for ci in sorted(agreg_interno.keys())]
    with open(arquivo, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + ("\n" if linhas else ""))

def construir_dataframes(contagem_por_cb: Counter, mapeamento: dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    rows_nm = []
    for cb, qtd in contagem_por_cb.items():
        if qtd <= 0:
            continue
        if cb in mapeamento:
            ci, nm, *_ = mapeamento[cb]
            rows.append({
                "codigo_interno": ci,
                "codigo_barras": cb,
                "nome": nm,
                "quantidade": qtd,
            })
        else:
            rows_nm.append({
                "codigo_interno": "",
                "codigo_barras": cb,
                "nome": "(NÃO MAPEADO)",
                "quantidade": qtd,
            })
    df = pd.DataFrame(rows)
    df_nm = pd.DataFrame(rows_nm)
    return df, df_nm

def exportar_detalhado(contagem_por_cb: Counter, mapeamento: dict):
    df, df_nm = construir_dataframes(contagem_por_cb, mapeamento)
    df.to_csv(ARQUIVO_CSV_DETALHADO, index=False, encoding="utf-8")
    df_nm.to_csv(ARQUIVO_CSV_NAO_MAPEADOS, index=False, encoding="utf-8")
    with pd.ExcelWriter(ARQUIVO_XLSX_SAIDA, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Mapeados")
        df_nm.to_excel(writer, index=False, sheet_name="NaoMapeados")

# ---------- GUI ----------
"""
Classe principal da interface gráfica (Tkinter)
Responsável por toda a interação com o usuário, exibição de dados e comandos da aplicação.
"""
class InventarioGUI:
    def __init__(self, root: tk.Tk, mapeamento: dict):
        self.root = root
        self.mapeamento = mapeamento
        self.contagem_por_cb = Counter()
        self.nao_mapeados_tmp = Counter()

        self.codigo_atual = tk.StringVar()
        self.quantidade_atual = tk.IntVar(value=0)
        self.nome_produto = tk.StringVar()
        self.status_text = tk.StringVar(value="Pronto")
        self.ultimo_backup_hora = "—"

        self.root.title("IKARUS INVENTORY - Controle de Estoque")
        try:
            self.root.iconbitmap("pena.ico")
        except Exception:
            pass

        top = tk.Frame(root, padx=8, pady=8)
        top.pack(fill=tk.X)

        tk.Label(top, text="CÓDIGO DE BARRAS:").grid(row=0, column=0, sticky="w")
        vcmd = (root.register(self._validate_cb), "%P")
        self.entrada_cb = tk.Entry(top, textvariable=self.codigo_atual, width=40, font=("TkDefaultFont", 12),
                                   validate="key", validatecommand=vcmd)
        self.entrada_cb.grid(row=0, column=1, sticky="w")
        self.entrada_cb.focus()
        self.entrada_cb.bind("<KeyRelease>", self.autopreencher_nome)

        tk.Label(top, text="NOME:").grid(row=1, column=0, sticky="w")
        tk.Label(top, textvariable=self.nome_produto, fg="blue").grid(row=1, column=1, sticky="w")

        tk.Label(top, text="QTD:").grid(row=2, column=0, sticky="w")
        tk.Label(top, textvariable=self.quantidade_atual, font=("Arial", 24, "bold"))\
            .grid(row=2, column=1, sticky="w")

        mid = tk.Frame(root, padx=8, pady=6)
        mid.pack(fill=tk.BOTH, expand=True)

        columns = ("interno", "barra", "nome", "qtd")
        self.tree = ttk.Treeview(mid, columns=columns, show="headings")
        for col, txt, w in [("interno", "Código Interno", 140),
                            ("barra", "Código de Barras", 180),
                            ("nome", "Nome", 420),
                            ("qtd", "Qtd", 80)]:
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=w, anchor="w")

        vsb = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        self.tree.pack(side="left", fill=tk.BOTH, expand=True)
        vsb.pack(side="right", fill="y")

        bot = tk.Frame(root, pady=6)
        bot.pack(fill=tk.X)
        tk.Button(bot, text="Salvar Parcial (F1)", command=self.salvar_parcial).pack(side="left", padx=6)
        tk.Button(bot, text="Finalizar (Ctrl+F2)", command=self.finalizar).pack(side="left", padx=6)
        tk.Button(bot, text="Configurar Autosave", command=self.configurar_autosave).pack(side="left", padx=6)
        tk.Button(bot, text="Exportar Relatório", command=self.exportar_relatorio).pack(side="left", padx=6)
        tk.Button(bot, text="Imprimir Relatório", command=self.imprimir_relatorio).pack(side="left", padx=6)

        status_bar = tk.Label(root, textvariable=self.status_text, anchor="w", bd=1, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        root.bind("<Return>", self.processar_cb)
        root.bind("<F1>", lambda e: self.salvar_parcial())
        root.bind("<Control-s>", lambda e: self.salvar_parcial())
        root.bind("<Control-F2>", lambda e: self.finalizar())
        root.bind("<Control-f>", lambda e: self.localizar_produto_contado_dialog())
        # Atalhos para o campo de código de barras
        self.entrada_cb.bind("<asterisk>", lambda e: self.pesquisar_item())
        self.entrada_cb.bind("<KP_Multiply>", lambda e: self.pesquisar_item())
        self.entrada_cb.bind("<plus>", lambda e: self.adicionar_manual())
        self.entrada_cb.bind("-", lambda e: self.subtrair_item())

        root.protocol("WM_DELETE_WINDOW", self.on_close)

        self._agendar_autosave()
        self.atualizar_lista()
        self._update_status()

        self.menu_popup = tk.Menu(self.root, tearoff=0)
        self.menu_popup.add_command(label="Salvar Parcial", command=self.salvar_parcial)
        self.menu_popup.add_command(label="Finalizar", command=self.finalizar)
        self.menu_popup.add_command(label="Configurar Autosave", command=self.configurar_autosave)
        self.menu_popup.add_command(label="Exportar Relatório", command=self.exportar_relatorio)
        self.menu_popup.add_command(label="Imprimir Relatório", command=self.imprimir_relatorio)
        self.menu_popup.add_separator()
        self.menu_popup.add_command(label="Zerar Estoque", command=self.zerar_estoque_dialog)
        self.tree.bind("<Button-3>", self.mostrar_menu_popup)

    def _validate_cb(self, new_value):
        if len(new_value) > 13:
            return False
        if not new_value.isdigit() and new_value != "":
            return False
        return True

    def autopreencher_nome(self, event=None):
        cb = self.codigo_atual.get().strip()
        if cb in self.mapeamento:
            _, nm, *_ = self.mapeamento[cb]
            self.nome_produto.set(nm)
        else:
            for k_cb, (k_ci, nm, *_) in self.mapeamento.items():
                if cb == k_ci:
                    self.nome_produto.set(nm)
                    return
            self.nome_produto.set("")

    def salvar_parcial(self):
        exportar_txt_formatado(self.contagem_por_cb, self.mapeamento, ARQUIVO_BACKUP)
        self.ultimo_backup_hora = datetime.now().strftime("%H:%M:%S")
        self._update_status()
        log("SALVAR_PARCIAL", f"arquivo={ARQUIVO_BACKUP}")
        messagebox.showinfo("Backup", f"Parcial salvo em {ARQUIVO_BACKUP}")

    def finalizar(self):
        senha = simpledialog.askstring("Finalizar", "Digite a senha de 6 dígitos:", show="*")
        if senha != SENHA_FINALIZAR:
            messagebox.showerror("Erro", "Senha incorreta. Finalização cancelada.")
            log("FINALIZAR_FALHA_SENHA", "senha_incorreta")
            return
        if not messagebox.askyesno("Finalizar", "Deseja finalizar e exportar os arquivos?"):
            return
        exportar_txt_formatado(self.contagem_por_cb, self.mapeamento, ARQUIVO_TXT_SAIDA)
        exportar_detalhado(self.contagem_por_cb, self.mapeamento)
        log("FINALIZAR_OK", f"txt={ARQUIVO_TXT_SAIDA} xlsx={ARQUIVO_XLSX_SAIDA}")
        messagebox.showinfo(
            "Finalizado",
            f"Exportado:\n- {ARQUIVO_TXT_SAIDA}\n- {ARQUIVO_XLSX_SAIDA}\n- {ARQUIVO_CSV_DETALHADO}\n- {ARQUIVO_CSV_NAO_MAPEADOS}"
        )
        self.root.quit()

    def configurar_autosave(self):
        try:
            minutos = simpledialog.askinteger("Configurar Autosave", "Intervalo em minutos:", minvalue=1, parent=self.root)
            if minutos:
                global INTERVALO_AUTOSAVE_MS
                INTERVALO_AUTOSAVE_MS = minutos * 60_000
                self._agendar_autosave()
                messagebox.showinfo("Configuração", f"Autosave ajustado para cada {minutos} minutos.", parent=self.root)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao configurar autosave: {e}", parent=self.root)

    def exportar_relatorio(self):
        formatos = ["TXT", "XLSX", "CSV"]
        if PDF_OK:
            formatos.append("PDF")
        formato = simpledialog.askstring("Exportar", f"Escolha o formato ({', '.join(formatos)}):", parent=self.root)
        if not formato:
            return
        formato = formato.strip().upper()
        try:
            if formato == "TXT":
                exportar_txt_formatado(self.contagem_por_cb, self.mapeamento, ARQUIVO_TXT_SAIDA)
                messagebox.showinfo("Exportação", f"Exportado para {ARQUIVO_TXT_SAIDA}", parent=self.root)
            elif formato == "XLSX":
                exportar_detalhado(self.contagem_por_cb, self.mapeamento)
                messagebox.showinfo("Exportação", f"Exportado para {ARQUIVO_XLSX_SAIDA}", parent=self.root)
            elif formato == "CSV":
                df, df_nm = construir_dataframes(self.contagem_por_cb, self.mapeamento)
                df.to_csv(ARQUIVO_CSV_DETALHADO, index=False, encoding="utf-8")
                df_nm.to_csv(ARQUIVO_CSV_NAO_MAPEADOS, index=False, encoding="utf-8")
                messagebox.showinfo("Exportação", f"Exportado para {ARQUIVO_CSV_DETALHADO} e {ARQUIVO_CSV_NAO_MAPEADOS}", parent=self.root)
            elif formato == "PDF" and PDF_OK:
                self.exportar_pdf()
            else:
                messagebox.showerror("Erro", "Formato não suportado ou biblioteca PDF não instalada.", parent=self.root)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na exportação: {e}", parent=self.root)

    def exportar_pdf(self):
        df, df_nm = construir_dataframes(self.contagem_por_cb, self.mapeamento)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Relatório de Inventário", ln=True, align="C")
        pdf.ln(10)
        for idx, row in df.iterrows():
            pdf.cell(0, 10, txt=f"{row['codigo_interno']} | {row['codigo_barras']} | {row['nome']} | {row['quantidade']}", ln=True)
        if not df_nm.empty:
            pdf.add_page()
            pdf.cell(200, 10, txt="Não Mapeados", ln=True, align="C")
            pdf.ln(10)
            for idx, row in df_nm.iterrows():
                pdf.cell(0, 10, txt=f"{row['codigo_barras']} | {row['quantidade']}", ln=True)
        pdf.output("relatorio_inventario.pdf")
        messagebox.showinfo("Exportação", "Relatório PDF gerado: relatorio_inventario.pdf", parent=self.root)

    def imprimir_relatorio(self):
        try:
            relatorio = "relatorio_inventario.pdf"
            if not os.path.exists(relatorio):
                self.exportar_pdf()
            os.startfile(relatorio, "print")
            messagebox.showinfo("Impressão", "Relatório enviado para impressão.", parent=self.root)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao imprimir: {e}", parent=self.root)

    def processar_cb(self, event=None):
        cb = self.codigo_atual.get().strip()
        if not cb or len(cb) != 13 or not cb.isdigit():
            beep_erro()
            self.codigo_atual.set("")
            return "break"

        if cb in self.mapeamento:
            self.contagem_por_cb[cb] += 1
            ci, nm, *_ = self.mapeamento[cb]
            self.nome_produto.set(nm)
            self.quantidade_atual.set(self.contagem_por_cb[cb])
            log("BIP_OK", f"cb={cb} ci={ci} qtd={self.contagem_por_cb[cb]}")
            beep_ok()
        else:
            self.contagem_por_cb[cb] += 1
            self.nome_produto.set("NÃO MAPEADO!")
            self.quantidade_atual.set(self.contagem_por_cb[cb])
            log("BIP_NAO_MAPEADO", f"cb={cb} qtd={self.contagem_por_cb[cb]}")
            beep_erro()
        self.codigo_atual.set("")
        self.atualizar_lista(focus_cb=cb)
        self._update_status()
        return "break"

    def adicionar_manual(self):
        entrada = simpledialog.askstring(
            "Adicionar produto",
            "Digite o código de barras (13 dígitos) ou o código interno:",
            parent=self.root
        )
        if not entrada:
            return

        cb = None
        if len(entrada) == 13 and entrada.isdigit():
            cb = entrada
        else:
            for k_cb, (k_ci, *_) in self.mapeamento.items():
                if entrada.strip().lower() == k_ci.strip().lower():
                    cb = k_cb
                    break

        if not cb:
            messagebox.showinfo("Inválido", "Código não encontrado ou inválido.", parent=self.root)
            return

        qtd = simpledialog.askinteger(
            "Adicionar quantidade",
            f"Quantidade para {cb}:",
            minvalue=1,
            parent=self.root
        )
        if qtd is None:
            return
        self.contagem_por_cb[cb] += qtd
        if cb in self.mapeamento:
            ci, nm, *_ = self.mapeamento[cb]
            self.nome_produto.set(nm)
            log("ADD_MANUAL_OK", f"cb={cb} ci={ci} +{qtd} total={self.contagem_por_cb[cb]}")
            beep_ok()
        else:
            self.nome_produto.set("NÃO MAPEADO!")
            log("ADD_MANUAL_NAO_MAPEADO", f"cb={cb} +{qtd} total={self.contagem_por_cb[cb]}")
            beep_erro()
        self.quantidade_atual.set(self.contagem_por_cb[cb])
        self.codigo_atual.set("")
        self.atualizar_lista(focus_cb=cb)
        self._update_status()
        # Salva imediatamente no Excel após adicionar manualmente
        try:
            exportar_detalhado(self.contagem_por_cb, self.mapeamento)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar no Excel: {e}", parent=self.root)

    def pesquisar_item(self):
        """
        Abre uma janela para pesquisar produtos pelo código interno, código de barras ou descrição.
        Permite adicionar quantidade ao produto selecionado.
        """
        def filtrar_produtos(termo, campo):
            termo = termo.strip().lower()
            resultados = []
            for cb, (ci, nm, grupo) in self.mapeamento.items():
                if campo == "interno":
                    alvo = ci
                elif campo == "barra":
                    alvo = cb
                elif campo == "nome":
                    alvo = nm
                else:
                    alvo = ci
                if termo in str(alvo).lower():
                    resultados.append((cb, ci, nm, grupo))
            return resultados

        pesquisa_win = tk.Toplevel(self.root)
        pesquisa_win.title("Pesquisar Produto")
        pesquisa_win.geometry("600x400")
        tk.Label(pesquisa_win, text="Selecione o campo de pesquisa:").pack(pady=(8,2))
        campo_var = tk.StringVar(value="interno")
        campos = [("Código Interno", "interno"), ("Código de Barras", "barra"), ("Descrição", "nome")]
        campo_menu = ttk.Combobox(pesquisa_win, textvariable=campo_var, values=[c[0] for c in campos], state="readonly")
        campo_menu.pack(pady=2)
        tk.Label(pesquisa_win, text="Digite para pesquisar:").pack(pady=(8,2))
        entry = tk.Entry(pesquisa_win, width=40)
        entry.pack(pady=4)
        listbox = tk.Listbox(pesquisa_win, width=80, height=14)
        listbox.pack(pady=8)

        def atualizar_lista_sugestoes(event=None):
            termo = entry.get()
            campo_nome = campo_var.get()
            if campo_nome == "Código Interno":
                campo = "interno"
            elif campo_nome == "Código de Barras":
                campo = "barra"
            else:
                campo = "nome"
            resultados = filtrar_produtos(termo, campo)
            listbox.delete(0, tk.END)
            for cb, ci, nm, grupo in resultados:
                listbox.insert(tk.END, f"{cb} | {ci} | {nm} | {grupo}")

        def selecionar_nome(event=None):
            if listbox.curselection():
                linha = listbox.get(listbox.curselection()[0])
                cb, ci, nm, grupo = linha.split(" | ", 3)
                self.codigo_atual.set(cb)
                self.nome_produto.set(nm)
                qtd = simpledialog.askinteger("Adicionar", f"Quantidade para '{nm}' ({cb}):", minvalue=1, parent=pesquisa_win)
                if qtd:
                    self.contagem_por_cb[cb] += qtd
                    self.atualizar_lista(focus_cb=cb)
                    self._update_status()
                pesquisa_win.destroy()

        campo_menu.bind("<<ComboboxSelected>>", atualizar_lista_sugestoes)
        entry.bind("<KeyRelease>", atualizar_lista_sugestoes)
        listbox.bind("<Double-1>", selecionar_nome)
        entry.focus()
        atualizar_lista_sugestoes()

        pesquisa_win.transient(self.root)
        pesquisa_win.grab_set()
        self.root.wait_window(pesquisa_win)

    def localizar_produto_contado_dialog(self):
        """
        Abre uma janela de busca (Ctrl+F) para localizar item contado por descrição, código de barras ou código interno.
        Ao localizar, seleciona e foca o item na lista.
        """
        def filtrar_contados(termo, campo):
            termo = termo.strip().lower()
            resultados = []
            for cb, qtd in self.contagem_por_cb.items():
                if qtd <= 0:
                    continue
                ci, nm, *_ = self.mapeamento.get(cb, ("", "(NÃO MAPEADO)", ""))
                if campo == "nome":
                    alvo = nm
                elif campo == "interno":
                    alvo = ci
                elif campo == "barra":
                    alvo = cb
                else:
                    alvo = nm
                if termo in str(alvo).lower():
                    resultados.append((cb, ci, nm, qtd))
            return resultados

        busca_win = tk.Toplevel(self.root)
        busca_win.title("Localizar Produto Contado")
        busca_win.geometry("600x400")
        tk.Label(busca_win, text="Selecione o campo de pesquisa:").pack(pady=(8,2))
        campo_var = tk.StringVar(value="nome")
        campos = [("Descrição", "nome"), ("Código Interno", "interno"), ("Código de Barras", "barra")]
        campo_menu = ttk.Combobox(busca_win, textvariable=campo_var, values=[c[0] for c in campos], state="readonly")
        campo_menu.pack(pady=2)
        tk.Label(busca_win, text="Digite para pesquisar:").pack(pady=(8,2))
        entry = tk.Entry(busca_win, width=40)
        entry.pack(pady=4)
        listbox = tk.Listbox(busca_win, width=80, height=14)
        listbox.pack(pady=8)

        def atualizar_lista(event=None):
            termo = entry.get()
            campo_nome = campo_var.get()
            if campo_nome == "Descrição":
                campo = "nome"
            elif campo_nome == "Código Interno":
                campo = "interno"
            else:
                campo = "barra"
            resultados = filtrar_contados(termo, campo)
            listbox.delete(0, tk.END)
            for cb, ci, nm, qtd in resultados:
                listbox.insert(tk.END, f"{cb} | {ci} | {nm} | {qtd}")

        def selecionar_item(event=None):
            if listbox.curselection():
                linha = listbox.get(listbox.curselection()[0])
                cb, ci, nm, qtd = linha.split(" | ", 3)
                # Seleciona e foca o item na treeview
                for iid in self.tree.get_children():
                    vals = self.tree.item(iid, "values")
                    if vals and vals[1] == cb:
                        self.tree.selection_set(iid)
                        self.tree.focus(iid)
                        self.tree.see(iid)
                        break
                busca_win.destroy()

        campo_menu.bind("<<ComboboxSelected>>", atualizar_lista)
        entry.bind("<KeyRelease>", atualizar_lista)
        listbox.bind("<Double-1>", selecionar_item)
        entry.focus()
        atualizar_lista()

        busca_win.transient(self.root)
        busca_win.grab_set()
        self.root.wait_window(busca_win)

    def atualizar_lista(self, focus_cb: Optional[str] = None):
        for r in self.tree.get_children():
            self.tree.delete(r)
        for cb, qtd in sorted(self.contagem_por_cb.items(), key=lambda x: x[0]):
            if qtd <= 0:
                continue
            ci, nm, *_ = self.mapeamento.get(cb, ("", "(NÃO MAPEADO)", ""))
            if ci == "":
                tag = "nao_mapeado"
            else:
                tag = "mapeado"
            self.tree.insert("", tk.END, values=(ci, cb, nm, qtd), tags=(tag,))
        self.tree.tag_configure("nao_mapeado", background="#FFD2D2")
        self.tree.tag_configure("mapeado", background="#C8F7C5")
        if focus_cb is not None:
            for iid in self.tree.get_children():
                vals = self.tree.item(iid, "values")
                if vals and vals[1] == focus_cb:
                    self.tree.selection_set(iid)
                    self.tree.focus(iid)
                    self.tree.see(iid)
                    break

    def zerar_estoque_dialog(self):
        opcoes = ["Total", "Por Grupo", "Por Fabricante"]
        escolha = simpledialog.askstring("Zerar Estoque", f"Escolha: {', '.join(opcoes)}")
        if not escolha:
            return
        escolha = escolha.strip().lower()
        if escolha == "total":
            for cb in list(self.contagem_por_cb.keys()):
                self.contagem_por_cb[cb] = 0
        elif escolha == "por grupo":
            grupo = simpledialog.askstring("Grupo", "Digite o nome do grupo:")
            if not grupo:
                return
            for cb, (ci, nm, grupo_prod, *resto) in self.mapeamento.items():
                if grupo_prod.lower() == grupo.lower():
                    self.contagem_por_cb[cb] = 0
        elif escolha == "por fabricante":
            fabricante = simpledialog.askstring("Fabricante", "Digite o nome do fabricante:")
            if not fabricante:
                return
            for cb, (ci, nm, grupo_prod, fabricante_prod, *resto) in self.mapeamento.items():
                if fabricante_prod.lower() == fabricante.lower():
                    self.contagem_por_cb[cb] = 0
        self.atualizar_lista()
        self._update_status()
        messagebox.showinfo("Zerar Estoque", "Estoque zerado conforme seleção.")

    def mostrar_menu_popup(self, event):
        self.menu_popup.delete(0, 'end')
        self.menu_popup.add_command(label="Salvar Parcial", command=self.salvar_parcial)
        self.menu_popup.add_command(label="Finalizar", command=self.finalizar)
        self.menu_popup.add_command(label="Configurar Autosave", command=self.configurar_autosave)
        self.menu_popup.add_command(label="Exportar Relatório", command=self.exportar_relatorio)
        self.menu_popup.add_command(label="Imprimir Relatório", command=self.imprimir_relatorio)
        self.menu_popup.add_separator()
        self.menu_popup.add_command(label="Zerar Estoque", command=self.zerar_estoque_dialog)
        # Adiciona opção de cadastrar não mapeado se clicou em um item não mapeado
        iid = self.tree.identify_row(event.y)
        if iid:
            vals = self.tree.item(iid, "values")
            ci = vals[0]
            if ci == "":
                self.menu_popup.add_separator()
                self.menu_popup.add_command(label="Cadastrar Produto Não Mapeado", command=lambda: self.cadastrar_nao_mapeado(iid))
        self.menu_popup.tk_popup(event.x_root, event.y_root)

    def cadastrar_nao_mapeado(self, iid):
        vals = self.tree.item(iid, "values")
        cb = vals[1]
        # Solicita dados do novo produto
        codigo_interno = simpledialog.askstring("Cadastro Manual", "Código Interno:", parent=self.root)
        if not codigo_interno:
            return
        descricao = simpledialog.askstring("Cadastro Manual", "Descrição:", parent=self.root)
        if not descricao:
            return
        grupo = simpledialog.askstring("Cadastro Manual", "Grupo (opcional):", parent=self.root)
        # Adiciona ao mapeamento
        self.mapeamento[cb] = (codigo_interno, descricao, grupo or "")
        self.atualizar_lista(focus_cb=cb)
        try:
            exportar_detalhado(self.contagem_por_cb, self.mapeamento)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar no Excel: {e}", parent=self.root)
        messagebox.showinfo("Cadastro", "Produto cadastrado manualmente!", parent=self.root)

    def _totais(self) -> Tuple[int, int, int]:
        total = sum(q for q in self.contagem_por_cb.values() if q > 0)
        map_total = sum(q for cb, q in self.contagem_por_cb.items() if q > 0 and cb in self.mapeamento)
        nm_total = total - map_total
        return total, map_total, nm_total

    def _update_status(self):
        total, map_total, nm_total = self._totais()
        self.status_text.set(
            f"Total: {total} | Mapeados: {map_total} | Não mapeados: {nm_total} | Último backup: {self.ultimo_backup_hora}"
        )

    def _agendar_autosave(self):
        self.root.after(INTERVALO_AUTOSAVE_MS, self._autosave_tick)

    def _autosave_tick(self):
        try:
            exportar_txt_formatado(self.contagem_por_cb, self.mapeamento, ARQUIVO_BACKUP)
            self.ultimo_backup_hora = datetime.now().strftime("%H:%M:%S")
            self._update_status()
            log("AUTOSAVE", f"arquivo={ARQUIVO_BACKUP}")
        finally:
            self._agendar_autosave()

    def on_close(self):
        resp = messagebox.askyesnocancel("Sair", "Deseja salvar antes de sair?\n(YES = salvar backup, NO = sair sem salvar, CANCEL = voltar)")
        if resp is None:
            return  # cancelar
        if resp:
            try:
                exportar_txt_formatado(self.contagem_por_cb, self.mapeamento, ARQUIVO_BACKUP)
                self.ultimo_backup_hora = datetime.now().strftime("%H:%M:%S")
                log("SALVAR_AO_FECHAR", f"arquivo={ARQUIVO_BACKUP}")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao salvar: {e}")
        self.root.destroy()

    def subtrair_item(self, event=None):
        item = self.tree.focus()
        if not item:
            messagebox.showinfo("Info", "Selecione um item para subtrair.")
            return
        vals = self.tree.item(item, "values")
        cb = vals[1]
        qtd = simpledialog.askinteger("Subtrair", f"Quantidade a subtrair de {cb}:", minvalue=1)
        if qtd is None:
            return
        anterior = self.contagem_por_cb.get(cb, 0)
        self.contagem_por_cb[cb] = max(0, anterior - qtd)
        log("SUBTRAIR", f"cb={cb} -{qtd} antes={anterior} depois={self.contagem_por_cb[cb]}")
        self.atualizar_lista(focus_cb=cb)
        self._update_status()

# ... (as funções auxiliares e main devem continuar aqui, como você já tinha no seu código) ...

# (Funções cadastrar_usuario_gui, tela_login, main, alterar_senha_gui, mostrar_senhas_gui, center_window, consultar_usuarios_gui, excluir_usuario_gui)
# ... [mantidas do seu código anterior, igual você já tem] ...

def cadastrar_usuario_gui(root):
    from tkinter import simpledialog, messagebox
    usuario = simpledialog.askstring("Cadastro", "Novo usuário:", parent=root)
    if not usuario:
        return
    senha = simpledialog.askstring("Cadastro", "Nova senha:", show="*", parent=root)
    if not senha:
        return
    senha2 = simpledialog.askstring("Cadastro", "Repita a senha:", show="*", parent=root)
    if senha != senha2:
        messagebox.showerror("Erro", "As senhas não coincidem.", parent=root)
        return
    if cadastrar_usuario(usuario, senha):
        messagebox.showinfo("Cadastro", "Usuário cadastrado com sucesso!", parent=root)
        log("CADASTRO_OK", f"usuario={usuario}")
    else:
        messagebox.showerror("Erro", "Usuário já existe!", parent=root)
        for widget in root.winfo_children():
            if isinstance(widget, tk.Entry):
                widget.delete(0, tk.END)
                widget.focus()

def tela_login(root) -> Optional[str]:
    import tkinter as tk
    from tkinter import simpledialog, messagebox, ttk

    log_frame = tk.Toplevel(root)
    log_frame.title("Login - IKARUS INVENTORY")
    log_frame.geometry("350x340")
    log_frame.grab_set()
    log_frame.resizable(False, False)

    try:
        logo_img = tk.PhotoImage(file="pena.png")
        logo_label = tk.Label(log_frame, image=logo_img)
        logo_label.image = logo_img
        logo_label.pack(pady=(10, 2))
    except Exception:
        pass

    tk.Label(log_frame, text="IKARUS INVENTORY", font=("Arial", 15, "bold")).pack(pady=(0, 10))

    form = tk.Frame(log_frame)
    form.pack(pady=4)

    usuarios_cadastrados = [u["usuario"] for u in carregar_usuarios()]

    tk.Label(form, text="Usuário:").grid(row=0, column=0, sticky="e", padx=4, pady=2)
    ent_user = ttk.Combobox(form, values=usuarios_cadastrados)
    ent_user.grid(row=0, column=1, padx=4, pady=2)

    tk.Label(form, text="Senha:").grid(row=1, column=0, sticky="e", padx=4, pady=2)
    ent_pass = tk.Entry(form, show="*")
    ent_pass.grid(row=1, column=1, padx=4, pady=2)

    def focar_senha(event=None):
        ent_pass.focus()
    ent_user.bind("<<ComboboxSelected>>", focar_senha)

    status = tk.StringVar()
    tk.Label(log_frame, textvariable=status, fg="red").pack(pady=2)

    usuario = None

    def do_login():
        user = ent_user.get()
        pwd = ent_pass.get()
        if not user or not pwd:
            status.set("Preencha usuário e senha.")
            return
        if autenticar(user, pwd):
            log("LOGIN_OK", f"usuario={user}")
            messagebox.showinfo("Login", f"Bem-vindo, {user}!", parent=log_frame)
            nonlocal usuario
            usuario = user
            log_frame.destroy()
        else:
            status.set("Usuário ou senha inválidos.")

    def do_cadastro():
        cadastrar_usuario_gui(log_frame)

    btn_frame = tk.Frame(log_frame)
    btn_frame.pack(pady=8)

    btn_login = tk.Button(btn_frame, text="Entrar", width=12, command=do_login)
    btn_login.grid(row=0, column=0, padx=4)
    btn_cadastrar = tk.Button(btn_frame, text="Cadastrar novo usuário", width=18, command=do_cadastro)
    btn_cadastrar.grid(row=0, column=1, padx=4)
    btn_alterar = tk.Button(btn_frame, text="Alterar senha", width=12, command=lambda: alterar_senha_gui(log_frame, ent_user.get()))
    btn_alterar.grid(row=1, column=0, padx=4, pady=2)

    def atualizar_botoes_admin(event=None):
        user = ent_user.get().lower()
        if user == "admin" or user == "adm":
            btn_ver_senhas.grid(row=1, column=1, padx=4, pady=2)
            btn_consultar.grid(row=2, column=0, padx=4, pady=2)
            btn_excluir.grid(row=2, column=1, padx=4, pady=2)
        else:
            btn_ver_senhas.grid_remove()
            btn_consultar.grid_remove()
            btn_excluir.grid_remove()

    btn_ver_senhas = tk.Button(btn_frame, text="Ver senhas (admin)", width=18, command=lambda: mostrar_senhas_gui(log_frame))
    btn_consultar = tk.Button(btn_frame, text="Consultar cadastros", width=18, command=lambda: consultar_usuarios_gui(log_frame))
    btn_excluir = tk.Button(btn_frame, text="Excluir cadastro", width=18, command=lambda: excluir_usuario_gui(log_frame))

    ent_user.bind("<<ComboboxSelected>>", atualizar_botoes_admin)
    ent_user.bind("<KeyRelease>", atualizar_botoes_admin)
    atualizar_botoes_admin()

    ent_user.focus()
    log_frame.bind("<Return>", lambda e: do_login())

    ent_user.bind("<<ComboboxSelected>>", focar_senha)

    root.wait_window(log_frame)
    return usuario


# === 8. FUNÇÃO PRINCIPAL ===
def main():
    """
    Função principal: inicializa a aplicação, faz login e carrega a interface gráfica.
    """
    caminho_excel, aba = ARQUIVO_EXCEL_PADRAO, ABA_EXCEL_PADRAO
    args = sys.argv[1:]
    if len(args) >= 1:
        caminho_excel = args[0]
    if len(args) >= 2:
        aba = args[1]

    root = tk.Tk()
    root.withdraw()  # esconde janela enquanto faz login
    usuario = tela_login(root)
    if not usuario:
        sys.exit(0)  # saiu sem logar
    root.deiconify()  # mostra janela depois do login

    mapeamento = carregar_mapeamento(caminho_excel, aba)
    app = InventarioGUI(root, mapeamento)
    root.mainloop()

if __name__ == "__main__":
    main()

def alterar_senha_gui(root, usuario):
    from tkinter import simpledialog, messagebox
    usuarios = carregar_usuarios()
    if not usuario:
        messagebox.showerror("Erro", "Digite o usuário antes de alterar a senha.", parent=root)
        return
    senha_atual = simpledialog.askstring("Alterar Senha", "Digite a senha atual:", show="*", parent=root)
    if not senha_atual:
        return
    if not autenticar(usuario, senha_atual):
        messagebox.showerror("Erro", "Senha atual incorreta.", parent=root)
        return
    nova = simpledialog.askstring("Alterar Senha", "Nova senha:", show="*", parent=root)
    if not nova:
        return
    nova2 = simpledialog.askstring("Alterar Senha", "Repita a nova senha:", show="*", parent=root)
    if nova != nova2:
        messagebox.showerror("Erro", "As senhas não coincidem.", parent=root)
        return
    for u in usuarios:
        if u["usuario"] == usuario:
            u["senha"] = hash_senha(nova)
            u["senha_original"] = nova
    salvar_usuarios(usuarios)
    messagebox.showinfo("Alterar Senha", "Senha alterada com sucesso!", parent=root)
    log("ALTERAR_SENHA", f"usuario={usuario}")

def mostrar_senhas_gui(root):
    from tkinter import messagebox
    usuarios = carregar_usuarios()
    texto = "\n".join([f'{u["usuario"]}: {u.get("senha_original", "(não disponível)")}' for u in usuarios])
    messagebox.showinfo("Senhas dos usuários", texto, parent=root)

def center_window(win):
    win.update_idletasks()
    w = win.winfo_width()
    h = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (w // 2)
    y = (win.winfo_screenheight() // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")

def consultar_usuarios_gui(root):
    from tkinter import messagebox
    usuarios = carregar_usuarios()
    texto = "\n".join([f'{u["usuario"]}' for u in usuarios])
    messagebox.showinfo("Usuários cadastrados", texto or "Nenhum usuário cadastrado.", parent=root)

def excluir_usuario_gui(root):
    from tkinter import messagebox, simpledialog, Toplevel, Listbox, Button, END

    usuarios = carregar_usuarios()
    nomes = [u["usuario"] for u in usuarios if u["usuario"] != "admin"]
    if not nomes:
        messagebox.showinfo("Excluir Usuário", "Nenhum usuário para excluir.", parent=root)
        return

    win = Toplevel(root)
    win.title("Excluir Usuário")
    win.geometry("300x250")
    win.grab_set()

    lb = Listbox(win)
    for nome in nomes:
        lb.insert(END, nome)
    lb.pack(padx=10, pady=10, fill="both", expand=True)

    def excluir():
        sel = lb.curselection()
        if not sel:
            messagebox.showerror("Erro", "Selecione um usuário.", parent=win)
            return
        usuario = lb.get(sel[0])
        if messagebox.askyesno("Confirmar", f"Excluir usuário '{usuario}'?", parent=win):
            novos = [u for u in usuarios if u["usuario"] != usuario]
            salvar_usuarios(novos)
            messagebox.showinfo("Excluir Usuário", f"Usuário '{usuario}' excluído.", parent=win)
            win.destroy()

    btn = Button(win, text="Excluir", command=excluir)
    btn.pack(pady=8)
