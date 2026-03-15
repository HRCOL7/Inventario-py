# Ikarus Inventory - Versão corrigida e completa
# Mantém login/usuarios, import Excel, abas: inventário, avaria, recebimento
# + / - usam diálogos: pede código de barras -> pede quantidade -> registra

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import os
import json
import hashlib
import pandas as pd
from PIL import Image, ImageTk
import sys

# winsound só existe no Windows, usar fallback genérico
try:
    import winsound
except Exception:
    winsound = None

ARQUIVO_USUARIOS = "usuarios.json"
DB_FILE = "app_inventario.db"

# ----------------- Helpers de som -----------------
def beep_ok():
    try:
        if winsound:
            winsound.Beep(880, 70)
        else:
            print("\a", end="", flush=True)
    except Exception:
        print("\a", end="", flush=True)

def beep_erro():
    try:
        if winsound:
            winsound.Beep(220, 120)
        else:
            print("\a", end="", flush=True)
    except Exception:
        print("\a", end="", flush=True)

# ----------------- Sistema de usuários -----------------
def carregar_usuarios():
    if not os.path.exists(ARQUIVO_USUARIOS):
        return []
    try:
        with open(ARQUIVO_USUARIOS, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def salvar_usuarios(usuarios):
    with open(ARQUIVO_USUARIOS, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)

def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def autenticar(usuario, senha):
    usuarios = carregar_usuarios()
    senha_hash = hash_senha(senha)
    for u in usuarios:
        if u.get("usuario") == usuario and u.get("senha") == senha_hash:
            return True
    return False

def cadastrar_usuario_gui(parent):
    usuario = simpledialog.askstring("Cadastro", "Novo usuário:", parent=parent)
    if not usuario:
        return
    senha = simpledialog.askstring("Cadastro", "Nova senha:", show="*", parent=parent)
    if not senha:
        return
    senha2 = simpledialog.askstring("Cadastro", "Repita a senha:", show="*", parent=parent)
    if senha != senha2:
        messagebox.showerror("Erro", "As senhas não coincidem.", parent=parent)
        return
    usuarios = carregar_usuarios()
    if any(u["usuario"] == usuario for u in usuarios):
        messagebox.showerror("Erro", "Usuário já existe!", parent=parent)
        return
    usuarios.append({"usuario": usuario, "senha": hash_senha(senha), "senha_original": senha})
    salvar_usuarios(usuarios)
    messagebox.showinfo("Cadastro", "Usuário cadastrado com sucesso!", parent=parent)

def tela_login(root) -> str:
    login_win = tk.Toplevel(root)
    login_win.title("Login - IKARUS INVENTORY")
    login_win.geometry("360x270")
    login_win.grab_set()
    login_win.resizable(False, False)

    tk.Label(login_win, text="IKARUS INVENTORY", font=("Arial", 15, "bold")).pack(pady=(10, 8))

    usuarios_cadastrados = [u["usuario"] for u in carregar_usuarios()]
    frame = tk.Frame(login_win)
    frame.pack(pady=6, padx=8, fill="x")

    tk.Label(frame, text="Usuário:").grid(row=0, column=0, sticky="w")
    ent_user = ttk.Combobox(frame, values=usuarios_cadastrados)
    ent_user.grid(row=0, column=1, sticky="we", padx=(6,0))

    tk.Label(frame, text="Senha:").grid(row=1, column=0, sticky="w", pady=(8,0))
    ent_pass = tk.Entry(frame, show="*")
    ent_pass.grid(row=1, column=1, sticky="we", padx=(6,0), pady=(8,0))

    frame.grid_columnconfigure(1, weight=1)

    status = tk.StringVar()
    tk.Label(login_win, textvariable=status, fg="red").pack(pady=4)

    usuario = None
    def do_login(event=None):
        nonlocal usuario
        user = ent_user.get().strip()
        pwd = ent_pass.get() or ""
        if not user or not pwd:
            status.set("Preencha usuário e senha.")
            return
        if autenticar(user, pwd):
            usuario = user
            login_win.destroy()
        else:
            status.set("Usuário ou senha inválidos.")

    btn_frame = tk.Frame(login_win)
    btn_frame.pack(pady=12)
    tk.Button(btn_frame, text="Entrar", width=12, command=do_login).pack(side="left", padx=6)
    tk.Button(btn_frame, text="Cadastrar novo usuário", width=20, command=lambda: cadastrar_usuario_gui(login_win)).pack(side="left", padx=6)

    ent_user.focus()
    login_win.bind("<Return>", do_login)
    root.wait_window(login_win)
    return usuario

# ----------------- Banco de dados SQLite -----------------
class Database:
    def __init__(self, path=DB_FILE):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        self._init_sample_items()

    def _create_tables(self):
        cur = self.conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id TEXT,
                sku TEXT UNIQUE,
                name TEXT,
                qty INTEGER DEFAULT 0,
                location TEXT,
                preco_compra REAL DEFAULT 0,
                preco_venda REAL DEFAULT 0,
                grupo TEXT,
                fabricante TEXT
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS damages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT,
                qty INTEGER,
                reason TEXT,
                date TEXT,
                preco_compra REAL DEFAULT 0,
                preco_venda REAL DEFAULT 0,
                FOREIGN KEY(item_id) REFERENCES items(id)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier TEXT,
                date TEXT,
                items_json TEXT
            )
        ''')
        self.conn.commit()

    def _init_sample_items(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM items")
        if cur.fetchone()[0] == 0:
            cur.execute(
                "INSERT INTO items (sku, name, qty, location, preco_compra, preco_venda) VALUES (?, ?, ?, ?, ?, ?)",
                ("7891234567890", "Friskies SACHE", 100, "Prateleira A1", 2.5, 4.99),
            )
            cur.execute(
                "INSERT INTO items (sku, name, qty, location, preco_compra, preco_venda) VALUES (?, ?, ?, ?, ?, ?)",
                ("7891234567001", "DogChow Papita", 50, "Prateleira B2", 5.0, 10.0),
            )
            self.conn.commit()

    def buscar_item_por_codigo(self, sku):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM items WHERE sku=?", (sku,))
        return cur.fetchone()

    def importar_produtos_excel(self, arquivo):
        # tenta ler o excel, se falhar, apenas retorna
        try:
            df = pd.read_excel(arquivo)
        except Exception as e:
            print("Erro ao ler Excel:", e)
            return
        cur = self.conn.cursor()
        for _, row in df.iterrows():
            codigo_interno = str(row.get("Código Inter", "") or "").strip()
            codigo_barras = str(row.get("Codigo Barras", "") or row.get("Código de Barras", "") or "").strip()
            nome = str(row.get("Descrição", "") or row.get("Nome", "") or "").strip()
            grupo = str(row.get("Grupo", "") or "").strip()
            fabricante = str(row.get("Fabricante", "") or "").strip()
            # padrão: qty 0, location vazio, preços zero
            if codigo_barras and nome:
                try:
                    cur.execute('''
                        INSERT OR IGNORE INTO items
                        (id, sku, name, qty, location, preco_compra, preco_venda, grupo, fabricante)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (codigo_interno, codigo_barras, nome, 0, "", 0.0, 0.0, grupo, fabricante))
                except Exception as e:
                    print("Erro ao inserir item do Excel:", e)
        self.conn.commit()

# ----------------- Aba de contagem (reutilizável) -----------------
class AbaContagemFrame(tk.Frame):
    def __init__(self, master, db: Database, modo="estoque", usuario=None):
        super().__init__(master)
        self.db = db
        self.modo = modo  # 'estoque', 'avaria', 'recebimento'
        self.usuario = usuario

        # configurações locais
        self.pedir_lote_validade = False
        self._autosave_job = None
        self.autosave_intervalo = None

        # Topo: campo código, nome e qtd
        top = tk.Frame(self, padx=8, pady=8)
        top.pack(fill=tk.X)

        tk.Label(top, text="CÓDIGO DE BARRAS:").grid(row=0, column=0, sticky="w")
        self.codigo_atual = tk.StringVar()
        self.entrada_cb = tk.Entry(top, textvariable=self.codigo_atual, width=40, font=("TkDefaultFont", 12))
        self.entrada_cb.grid(row=0, column=1, sticky="w")
        self.entrada_cb.focus()

        tk.Label(top, text="NOME:").grid(row=1, column=0, sticky="w")
        self.nome_produto = tk.StringVar()
        tk.Label(top, textvariable=self.nome_produto, fg="blue").grid(row=1, column=1, sticky="w")

        tk.Label(top, text="QTD:").grid(row=2, column=0, sticky="w")
        self.quantidade_atual = tk.IntVar(value=0)
        tk.Label(top, textvariable=self.quantidade_atual, font=("Arial", 24, "bold")).grid(row=2, column=1, sticky="w")

        # Campos extras para avaria
        if self.modo == "avaria":
            tk.Label(top, text="PREÇO DE COMPRA:").grid(row=3, column=0, sticky="w")
            self.preco_compra = tk.DoubleVar(value=0.0)
            tk.Entry(top, textvariable=self.preco_compra, width=14).grid(row=3, column=1, sticky="w")

            tk.Label(top, text="PREÇO DE VENDA:").grid(row=4, column=0, sticky="w")
            self.preco_venda = tk.DoubleVar(value=0.0)
            tk.Entry(top, textvariable=self.preco_venda, width=14).grid(row=4, column=1, sticky="w")
        else:
            # garantir que existam as variáveis para evitar AttributeError
            self.preco_compra = tk.DoubleVar(value=0.0)
            self.preco_venda = tk.DoubleVar(value=0.0)

        # Tabela central (colunas diferentes se avaria)
        columns = ["id", "codigo_barra", "nome", "qtd", "localizacao"]
        if self.modo == "avaria":
            columns += ["preco_compra", "preco_venda", "perda"]

        frame_central = tk.Frame(self)
        frame_central.pack(fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(frame_central, columns=columns, show="headings", selectmode="browse")
        headers = {
            "id": "ID",
            "codigo_barra": "Código de Barras",
            "nome": "Nome",
            "qtd": "Qtd",
            "localizacao": "Localização",
            "preco_compra": "Preço Compra",
            "preco_venda": "Preço Venda",
            "perda": "Perda R$"
        }
        for col in columns:
            self.tree.heading(col, text=headers.get(col, col))
            self.tree.column(col, anchor="w", width=110 if col != "nome" else 260)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(frame_central, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # status bar
        self.status_bar = tk.Label(self, text="", anchor="w", bd=1, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # botões inferiores
        bot = tk.Frame(self, pady=6)
        bot.pack(fill=tk.X)
        tk.Button(bot, text="Salvar Parcial (F1)", command=self.salvar_parcial).pack(side="left", padx=6)
        tk.Button(bot, text="Finalizar (Ctrl+F2)", command=self.finalizar).pack(side="left", padx=6)
        tk.Button(bot, text="Configurar Autosave", command=self.configurar_autosave).pack(side="left", padx=6)
        tk.Button(bot, text="Exportar PDF", command=self.exportar_pdf).pack(side="left", padx=6)
        tk.Button(bot, text="Imprimir Relatório", command=self.imprimir_relatorio).pack(side="left", padx=6)

        # botão de configurações (icone opcional)
        try:
            img = Image.open("engrenagem.png").resize((20,20))
            icon = ImageTk.PhotoImage(img)
            btn_config = tk.Button(bot, image=icon, command=self.abrir_configuracoes, bd=0)
            btn_config.image = icon
            btn_config.pack(side="right", padx=8)
        except Exception:
            btn_config = tk.Button(bot, text="⚙", font=("Arial", 12), command=self.abrir_configuracoes, bd=0)
            btn_config.pack(side="right", padx=8)

        # bindings
        self.entrada_cb.bind("<Return>", self.leitura_codigo_barra)
        self.entrada_cb.bind("<asterisk>", lambda e: self.abrir_pesquisa_produto())
        self.entrada_cb.bind("<KP_Multiply>", lambda e: self.abrir_pesquisa_produto())
        # Para o pedido do usuário: + e - abrem diálogos na ordem: código -> quantidade
        # Vínculo ao pressionar as teclas dentro da Entry
        self.entrada_cb.bind("<plus>", lambda e: self.fluxo_adicionar_dialogo())
        self.entrada_cb.bind("<KP_Add>", lambda e: self.fluxo_adicionar_dialogo())
        self.entrada_cb.bind("-", lambda e: self.fluxo_subtrair_dialogo())
        self.entrada_cb.bind("<KP_Subtract>", lambda e: self.fluxo_subtrair_dialogo())

        # variáveis auxiliares
        self.itens_tabela = []
        self.acao_em_espera = None
        self.qtd_para_adicionar = None
        self.qtd_para_subtrair = None

        self.atualiza_status()

    # ----- leitura via campo & ENTER -----
    def leitura_codigo_barra(self, event=None):
        cb = (self.codigo_atual.get() or "").strip()
        if not cb or len(cb) < 2:
            messagebox.showinfo("Info", "Digite um código de barras válido.")
            beep_erro()
            return
        row = self.db.buscar_item_por_codigo(cb)
        if row:
            self.nome_produto.set(row["name"])
            if self.modo == "avaria":
                try:
                    self.preco_compra.set(float(row["preco_compra"] or 0.0))
                    self.preco_venda.set(float(row["preco_venda"] or 0.0))
                except Exception:
                    self.preco_compra.set(0.0)
                    self.preco_venda.set(0.0)
            self.quantidade_atual.set(1)
            beep_ok()
            self.adiciona_item_tabela(row, localizado=True)
        else:
            self.nome_produto.set("NÃO MAPEADO")
            self.quantidade_atual.set(1)
            beep_erro()
            self.adiciona_item_tabela(None, cb=cb)
        self.codigo_atual.set("")
        self.atualiza_status()

    # ----- adicionar à tabela (ou acumular) -----
    def adiciona_item_tabela(self, row, cb=None, localizado=False):
        # prepara valores
        if row:
            id_ = row.get("id") or ""
            cb_ = row.get("sku") or ""
            nome_ = row.get("name") or ""
            qtd_ = int(self.quantidade_atual.get() or 0)
            loc_ = row.get("location") or ""
            preco_compra = float(row.get("preco_compra") or 0.0)
            preco_venda = float(row.get("preco_venda") or 0.0)
        else:
            id_ = ""
            cb_ = cb or ""
            nome_ = self.nome_produto.get() or ""
            qtd_ = int(self.quantidade_atual.get() or 0)
            loc_ = ""
            preco_compra = float(self.preco_compra.get() or 0.0)
            preco_venda = float(self.preco_venda.get() or 0.0)

        # se já existe a linha com o mesmo código de barras, soma a quantidade
        for iid in self.tree.get_children():
            vals = list(self.tree.item(iid, "values"))
            # col 1 = codigo_barra
            if len(vals) > 1 and str(vals[1]) == str(cb_):
                # atualiza quantidade
                try:
                    antiga = int(vals[3])
                except Exception:
                    antiga = 0
                nova_qtd = antiga + qtd_
                vals[3] = nova_qtd
                if self.modo == "avaria":
                    # calcula perda sobre preco_compra
                    perda = nova_qtd * (preco_compra or 0.0)
                    # perda índice: último da linha
                    if len(vals) >= 8:
                        vals[7] = f"{perda:.2f}"
                    else:
                        # ajustar caso estrutura incompleta
                        while len(vals) < 8:
                            vals.append("")
                        vals[7] = f"{perda:.2f}"
                self.tree.item(iid, values=vals)
                self.tree.see(iid)
                self.tree.yview_moveto(1)
                return

        # cria nova linha
        values = [id_, cb_, nome_, qtd_, loc_]
        if self.modo == "avaria":
            perda = qtd_ * (preco_compra or 0.0)
            values += [f"{preco_compra:.2f}", f"{preco_venda:.2f}", f"{perda:.2f}"]
        # Tags para destacar
        tags = ()
        if localizado:
            tags = ("localizado",)
        elif id_ == "":
            tags = ("nao_mapeado",)
        iid = self.tree.insert("", tk.END, values=values, tags=tags)
        self.tree.tag_configure("localizado", background="#C8F7C5")
        self.tree.tag_configure("nao_mapeado", background="#FFD2D2")
        self.tree.see(iid)
        self.tree.yview_moveto(1)

    def atualiza_status(self):
        total = 0
        mapeados = 0
        nao_mapeados = 0
        for iid in self.tree.get_children():
            vals = self.tree.item(iid, "values")
            try:
                qtd = int(vals[3])
            except Exception:
                qtd = 0
            total += qtd
            if (vals[0] or "") != "":
                mapeados += qtd
            else:
                nao_mapeados += qtd
        if self.modo == "avaria":
            perda_total = self.calcula_perda_total()
            self.status_bar.config(text=f"Total de Perda R$: {perda_total:,.2f}")
        else:
            self.status_bar.config(text=f"Total: {total} | Mapeados: {mapeados} | Não mapeados: {nao_mapeados}")

    def calcula_perda_total(self):
        total = 0.0
        for iid in self.tree.get_children():
            vals = self.tree.item(iid, "values")
            try:
                perda = float(vals[-1])
                total += perda
            except Exception:
                pass
        return total

    # ----- pesquisa via janela -----
    def abrir_pesquisa_produto(self, event=None):
        win = tk.Toplevel(self)
        win.title("Pesquisar Produto")
        win.geometry("700x420")
        win.transient(self)
        win.grab_set()

        tk.Label(win, text="Pesquisar por:").pack(pady=(6,0))
        campo_var = tk.StringVar(value="Nome")
        campos = ["Nome", "Código de Barras", "Código Interno", "Grupo", "Fabricante"]
        campo_menu = ttk.Combobox(win, textvariable=campo_var, values=campos, state="readonly")
        campo_menu.pack(pady=4)

        entry = tk.Entry(win, width=45)
        entry.pack(pady=4)

        tree = ttk.Treeview(win, columns=("sku", "name", "qty", "location"), show="headings", height=12)
        tree.heading("sku", text="Código de Barras")
        tree.heading("name", text="Nome")
        tree.heading("qty", text="Qtd")
        tree.heading("location", text="Localização")
        tree.column("sku", width=140)
        tree.column("name", width=340)
        tree.column("qty", width=70)
        tree.column("location", width=120)
        tree.pack(pady=8, fill=tk.BOTH, expand=True)

        def atualizar_lista(event=None):
            termo = (entry.get() or "").strip()
            campo = campo_var.get()
            for i in tree.get_children():
                tree.delete(i)
            cur = self.db.conn.cursor()
            if campo == "Nome":
                cur.execute("SELECT sku, name, qty, location FROM items WHERE name LIKE ?", (f"%{termo}%",))
            elif campo == "Código de Barras":
                cur.execute("SELECT sku, name, qty, location FROM items WHERE sku LIKE ?", (f"%{termo}%",))
            elif campo == "Código Interno":
                cur.execute("SELECT sku, name, qty, location FROM items WHERE id LIKE ?", (f"%{termo}%",))
            elif campo == "Grupo":
                cur.execute("SELECT sku, name, qty, location FROM items WHERE grupo LIKE ?", (f"%{termo}%",))
            elif campo == "Fabricante":
                cur.execute("SELECT sku, name, qty, location FROM items WHERE fabricante LIKE ?", (f"%{termo}%",))
            for row in cur.fetchall():
                tree.insert("", tk.END, values=(row["sku"], row["name"], row["qty"], row["location"]))

        def on_select(event):
            selected = tree.focus()
            if not selected:
                return
            vals = tree.item(selected, "values")
            cb = vals[0]
            nome = vals[1]
            qtd = simpledialog.askinteger("Adicionar à contagem", f"Quantidade para '{nome}':", minvalue=1, initialvalue=1, parent=win)
            if qtd:
                self.codigo_atual.set(cb)
                self.quantidade_atual.set(qtd)
                row = self.db.buscar_item_por_codigo(cb)
                self.nome_produto.set(nome)
                self.adiciona_item_tabela(row)
                self.atualiza_status()
                win.destroy()

        tree.bind("<Double-1>", on_select)
        entry.bind("<KeyRelease>", atualizar_lista)
        campo_menu.bind("<<ComboboxSelected>>", atualizar_lista)
        entry.focus()
        atualizar_lista()

        self.wait_window(win)

    # ---------------- fluxo dialogado solicitado: código -> quantidade ----------------
    def fluxo_adicionar_dialogo(self):
        # Primeiro pede o código de barras
        cb = simpledialog.askstring("Adicionar", "Digite o código de barras:", parent=self)
        if not cb:
            return
        # Depois pede a quantidade
        qtd = simpledialog.askinteger("Adicionar", "Digite a quantidade a adicionar:", minvalue=1, initialvalue=1, parent=self)
        if qtd is None:
            return
        # Registrar
        row = self.db.buscar_item_por_codigo(cb)
        if row:
            self.nome_produto.set(row["name"])
            self.quantidade_atual.set(qtd)
            self.adiciona_item_tabela(row)
            beep_ok()
        else:
            self.nome_produto.set("NÃO MAPEADO")
            self.quantidade_atual.set(qtd)
            self.adiciona_item_tabela(None, cb=cb)
            beep_erro()
        self.atualiza_status()

    def fluxo_subtrair_dialogo(self):
        cb = simpledialog.askstring("Subtrair", "Digite o código de barras:", parent=self)
        if not cb:
            return
        qtd = simpledialog.askinteger("Subtrair", "Digite a quantidade a subtrair:", minvalue=1, initialvalue=1, parent=self)
        if qtd is None:
            return
        qtd = -abs(int(qtd))
        row = self.db.buscar_item_por_codigo(cb)
        if row:
            self.nome_produto.set(row["name"])
            self.quantidade_atual.set(qtd)
            self.adiciona_item_tabela(row)
            beep_ok()
        else:
            self.nome_produto.set("NÃO MAPEADO")
            self.quantidade_atual.set(qtd)
            self.adiciona_item_tabela(None, cb=cb)
            beep_erro()
        self.atualiza_status()

    # ---------------- configurações & lote/validade ----------------
    def abrir_configuracoes(self):
        win = tk.Toplevel(self)
        win.title("Configurações")
        win.geometry("320x140")
        var_lote_validade = tk.BooleanVar(value=getattr(self, "pedir_lote_validade", False))
        chk = tk.Checkbutton(win, text="Pedir lote e validade ao contar/adicionar", variable=var_lote_validade)
        chk.pack(pady=10)
        def salvar():
            self.pedir_lote_validade = var_lote_validade.get()
            win.destroy()
        tk.Button(win, text="Salvar", command=salvar).pack(pady=8)

    # ---------------- exportar / salvar / imprimir ----------------
    def exportar_pdf(self):
        try:
            from fpdf import FPDF
        except Exception:
            messagebox.showerror("PDF", "Instale o pacote fpdf: pip install fpdf", parent=self)
            return
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)
        titulo = "Relatório de Inventário"
        pdf.cell(0, 10, txt=titulo, ln=True, align="C")
        pdf.ln(6)
        for iid in self.tree.get_children():
            vals = self.tree.item(iid, "values")
            linha = " | ".join(str(v) for v in vals)
            # limita tamanho da linha no PDF
            pdf.multi_cell(0, 6, txt=linha)
        out = "inventario.pdf"
        pdf.output(out)
        messagebox.showinfo("PDF", f"Relatório exportado como {out}", parent=self)

    def salvar_parcial(self):
        try:
            with open("contagem_backup.txt", "w", encoding="utf-8") as f:
                for iid in self.tree.get_children():
                    vals = self.tree.item(iid, "values")
                    linha = " | ".join(str(v) for v in vals)
                    f.write(linha + "\n")
            messagebox.showinfo("Backup", "Contagem parcial salva em contagem_backup.txt", parent=self)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar backup: {e}", parent=self)

    def finalizar(self):
        # Solicita senha do usuário logado (usa self.usuario fornecido pelo app)
        senha = simpledialog.askstring("Finalizar", "Digite sua senha para finalizar:", show="*", parent=self)
        usuario = self.usuario
        if not usuario or not senha or not autenticar(usuario, senha):
            messagebox.showerror("Erro", "Senha incorreta ou usuário não identificado.", parent=self)
            return
        try:
            with open("contagem_final.txt", "w", encoding="utf-8") as f:
                for iid in self.tree.get_children():
                    vals = self.tree.item(iid, "values")
                    linha = " | ".join(str(v) for v in vals)
                    f.write(linha + "\n")
            messagebox.showinfo("Finalizar", "Contagem final salva em contagem_final.txt", parent=self)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao finalizar: {e}", parent=self)

    def configurar_autosave(self):
        intervalo = simpledialog.askinteger("Autosave", "Intervalo em minutos:", minvalue=1, initialvalue=2, parent=self)
        if intervalo:
            self.autosave_intervalo = intervalo * 60 * 1000  # ms
            # cancela job anterior se existir
            if getattr(self, "_autosave_job", None):
                try:
                    self.after_cancel(self._autosave_job)
                except Exception:
                    pass
            # agenda repetidamente
            def _job():
                try:
                    self.salvar_parcial()
                finally:
                    # reprograma
                    self._autosave_job = self.after(self.autosave_intervalo, _job)
            self._autosave_job = self.after(self.autosave_intervalo, _job)
            messagebox.showinfo("Autosave", f"Autosave configurado para cada {intervalo} minutos.", parent=self)

    def imprimir_relatorio(self):
        # tenta imprimir arquivo de backup
        try:
            if os.path.exists("contagem_backup.txt"):
                # Windows: os.startfile(..., "print")
                if sys.platform.startswith("win"):
                    os.startfile("contagem_backup.txt", "print")
                else:
                    messagebox.showinfo("Imprimir", "Impressão automática disponível apenas no Windows.", parent=self)
            else:
                messagebox.showinfo("Imprimir", "Arquivo de backup não encontrado. Faça um salvamento parcial primeiro.", parent=self)
        except Exception as e:
            messagebox.showerror("Imprimir", f"Erro ao imprimir: {e}", parent=self)

# ----------------- Aplicativo principal -----------------
class InventarioApp:
    def __init__(self, root, usuario, db: Database):
        self.root = root
        self.usuario = usuario
        self.db = db

        self.root.title(f"IKARUS INVENTORY - Usuário: {usuario}")
        self.root.geometry("1200x700")

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True)

        # Cria as abas: estoque/contagem, avaria, recebimento
        self.aba_contagem = AbaContagemFrame(nb, db, modo="estoque", usuario=usuario)
        self.aba_avaria = AbaContagemFrame(nb, db, modo="avaria", usuario=usuario)
        self.aba_recebimento = AbaContagemFrame(nb, db, modo="recebimento", usuario=usuario)

        nb.add(self.aba_contagem, text="Inventário / Contagem")
        nb.add(self.aba_avaria, text="Controle de Avaria")
        nb.add(self.aba_recebimento, text="Recebimento")

        # atalhos globais se desejar
        self.root.bind_all("<F1>", lambda e: self.aba_contagem.salvar_parcial())
        self.root.bind_all("<Control-F2>", lambda e: self.aba_contagem.finalizar())

        self.root.protocol("WM_DELETE_WINDOW", self.confirmar_fechar)

    def confirmar_fechar(self):
        if messagebox.askokcancel("Sair", "Deseja realmente fechar o aplicativo?"):
            self.root.destroy()

# ----------------- Execução principal -----------------
def main():
    root = tk.Tk()
    root.withdraw()
    usuario = tela_login(root)
    if not usuario:
        # se não logou, encerra
        return
    root.deiconify()
    db = Database()
    # importa se existir planilha
    if os.path.exists("Produtos Box.xlsx"):
        db.importar_produtos_excel("Produtos Box.xlsx")
    app = InventarioApp(root, usuario, db)
    root.mainloop()

if __name__ == "__main__":
    main()
