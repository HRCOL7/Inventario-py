# ===============================
# IKARUS INVENTORY - Login Premium (Tkinter - Python 3.13 Compatible)
# Reimplementation with theme toggle and autocomplete
# ===============================

from typing import Optional
import tkinter as tk
from tkinter import messagebox, simpledialog, Toplevel, Frame, Label, Button, Entry
import tkinter.font as tkFont

from usuarios import (
    cadastrar_usuario, autenticar, alterar_senha, excluir_usuario,
    obter_usuarios, obter_senhas, carregar_usuarios
)
import json
import os

ARQUIVO_CONFIG_TEMA = "config_tema.json"

# Ícones em emoji
ICONS = {
    "user": "👤",
    "lock": "🔐",
    "eye": "👁️",
    "add": "➕",
    "delete": "🗑️",
    "admin": "🔑",
    "edit": "✏️",
}


class LoginPremium(Toplevel):
    """Janela de login com design premium (Tkinter puro)"""

    def _carregar_tema_salvo(self):
        """Carrega tema salvo do arquivo de configuração"""
        if os.path.exists(ARQUIVO_CONFIG_TEMA):
            try:
                with open(ARQUIVO_CONFIG_TEMA, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('tema_login', 'dark')
            except Exception:
                return 'dark'
        return 'dark'
    
    def _salvar_tema(self):
        """Salva tema selecionado no arquivo de configuração"""
        try:
            config = {}
            if os.path.exists(ARQUIVO_CONFIG_TEMA):
                with open(ARQUIVO_CONFIG_TEMA, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            config['tema_login'] = self.theme
            with open(ARQUIVO_CONFIG_TEMA, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def __init__(self, parent):
        super().__init__(parent)

        self.title("🔐 Login - IKARUS INVENTORY")
        self.geometry("500x700")
        self.resizable(False, False)
        self.grab_set()

        # Carregar tema salvo
        self.theme = self._carregar_tema_salvo()

        # Paletas de cores
        self.PALETTES = {
            "dark": {
                "primary": "#1f6feb",
                "primary_hover": "#388bfd",
                "success": "#238636",
                "danger": "#da3633",
                "bg_primary": "#0d1117",
                "bg_secondary": "#161b22",
                "bg_tertiary": "#21262d",
                "border": "#30363d",
                "text_primary": "#e6edf3",
                "text_secondary": "#8b949e",
            },
            "light": {
                "primary": "#1976d2",
                "primary_hover": "#1565c0",
                "success": "#2e7d32",
                "danger": "#c62828",
                "bg_primary": "#f5f7fb",
                "bg_secondary": "#ffffff",
                "bg_tertiary": "#f0f3f7",
                "border": "#d0d7de",
                "text_primary": "#0b1220",
                "text_secondary": "#334155",
            }
        }

        self.COLORS = self.PALETTES[self.theme]

        # Configuração da janela
        self.configure(bg=self.COLORS["bg_primary"])

        # Fontes
        self.font_title = tkFont.Font(family="Arial", size=20, weight="bold")
        self.font_subtitle = tkFont.Font(family="Arial", size=10)
        self.font_label = tkFont.Font(family="Arial", size=11)
        self.font_button = tkFont.Font(family="Arial", size=10, weight="bold")

        # Variáveis
        self.usuario_logado = None
        self.admin_mode = False

        # Widgets references
        self._suggest_win = None

        # Criar widgets
        self._criar_widgets()

        # Centrar janela
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _criar_widgets(self):
        """Cria os widgets da interface e guarda referências para trocar tema."""
        # Container principal
        self.main_frame = Frame(self, bg=self.COLORS["bg_primary"])
        self.main_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # ===== HEADER =====
        self.header_frame = Frame(self.main_frame, bg=self.COLORS["primary"], height=100)
        self.header_frame.pack(fill="x", side="top")
        self.header_frame.pack_propagate(False)

        self.title_label = Label(
            self.header_frame,
            text="🔐 IKARUS INVENTORY",
            font=self.font_title,
            bg=self.COLORS["primary"],
            fg=self.COLORS["text_primary"]
        )
        self.title_label.pack(pady=15)

        self.subtitle_label = Label(
            self.header_frame,
            text="Sistema de Gerenciamento de Inventário",
            font=self.font_subtitle,
            bg=self.COLORS["primary"],
            fg=self.COLORS["text_secondary"]
        )
        self.subtitle_label.pack(pady=(0, 10))

        # Theme toggle button
        self.btn_theme = Button(
            self.header_frame,
            text="☀️" if self.theme == "dark" else "🌙",
            font=self.font_button,
            bg=self.COLORS["primary"],
            fg=self.COLORS["text_primary"],
            activebackground=self.COLORS["primary_hover"],
            command=self.toggle_theme
        )
        self.btn_theme.place(relx=0.95, rely=0.2, anchor="ne")

        # ===== CONTENT =====
        self.content_frame = Frame(self.main_frame, bg=self.COLORS["bg_primary"])
        self.content_frame.pack(fill="both", expand=True, padx=40, pady=40)

        # --- Card Login ---
        self.login_frame = Frame(self.content_frame, bg=self.COLORS["bg_secondary"])
        self.login_frame.pack(fill="x", pady=10)

        # Padding interno
        self.padding = Frame(self.login_frame, bg=self.COLORS["bg_secondary"])
        self.padding.pack(fill="both", expand=True, padx=20, pady=20)

        # Label "Faça login"
        login_title = Label(
            self.padding,
            text="📝 Faça Login",
            font=tkFont.Font(family="Arial", size=14, weight="bold"),
            bg=self.COLORS["bg_secondary"],
            fg=self.COLORS["text_primary"]
        )
        login_title.pack(pady=(0, 20))

        # Campo Usuário
        Label(
            self.padding,
            text=f"{ICONS['user']} Usuário",
            font=self.font_label,
            bg=self.COLORS["bg_secondary"],
            fg=self.COLORS["text_primary"]
        ).pack(anchor="w", pady=(10, 2))

        self.entry_usuario = Entry(
            self.padding,
            font=self.font_label,
            bg=self.COLORS["bg_tertiary"],
            fg=self.COLORS["text_primary"],
            insertbackground=self.COLORS["text_primary"]
        )
        self.entry_usuario.pack(fill="x", pady=(0, 15))
        self.entry_usuario.bind("<Return>", lambda e: self.entry_senha.focus())
        self.entry_usuario.bind("<KeyRelease>", self._on_usuario_key)
        self.entry_usuario.bind("<FocusOut>", lambda e: self.after(150, self._hide_suggest))
        self.entry_usuario.bind("<Down>", self._focus_suggest)

        # Campo Senha
        Label(
            self.padding,
            text=f"{ICONS['lock']} Senha",
            font=self.font_label,
            bg=self.COLORS["bg_secondary"],
            fg=self.COLORS["text_primary"]
        ).pack(anchor="w", pady=(10, 2))

        self.entry_senha = Entry(
            self.padding,
            font=self.font_label,
            bg=self.COLORS["bg_tertiary"],
            fg=self.COLORS["text_primary"],
            insertbackground=self.COLORS["text_primary"],
            show="•"
        )
        self.entry_senha.pack(fill="x", pady=(0, 15))
        self.entry_senha.bind("<Return>", lambda e: self._fazer_login())

        # Botão Login
        self.btn_login = Button(
            self.padding,
            text="🔓 Entrar",
            font=self.font_button,
            bg=self.COLORS["primary"],
            fg=self.COLORS["text_primary"],
            activebackground=self.COLORS["primary_hover"],
            activeforeground=self.COLORS["text_primary"],
            command=self._fazer_login
        )
        self.btn_login.pack(fill="x", pady=10)

        # --- Card Registrar ---
        self.register_frame = Frame(self.content_frame, bg=self.COLORS["bg_secondary"])
        self.register_frame.pack(fill="x", pady=10)

        self.padding_reg = Frame(self.register_frame, bg=self.COLORS["bg_secondary"])
        self.padding_reg.pack(fill="both", expand=True, padx=20, pady=20)

        Label(
            self.padding_reg,
            text="👤 Novo Usuário?",
            font=tkFont.Font(family="Arial", size=12, weight="bold"),
            bg=self.COLORS["bg_secondary"],
            fg=self.COLORS["text_primary"]
        ).pack(pady=(0, 10))

        btn_cadastro = Button(
            self.padding_reg,
            text="➕ Cadastrar",
            font=self.font_button,
            bg=self.COLORS["success"],
            fg=self.COLORS["text_primary"],
            activebackground="#2ea043",
            activeforeground=self.COLORS["text_primary"],
            command=self._cadastro_dialog
        )
        btn_cadastro.pack(fill="x", pady=5)

        btn_alterar_senha = Button(
            self.padding_reg,
            text="🔑 Alterar Senha",
            font=self.font_button,
            bg=self.COLORS["danger"],
            fg=self.COLORS["text_primary"],
            activebackground="#e81b23",
            activeforeground=self.COLORS["text_primary"],
            command=self._alterar_senha_dialog
        )
        btn_alterar_senha.pack(fill="x", pady=5)

        # --- Botões Admin (ocultos inicialmente) ---
        self.admin_frame = Frame(self.content_frame, bg=self.COLORS["bg_secondary"])
        self.admin_frame.pack(fill="x", pady=10)

        padding_admin = Frame(self.admin_frame, bg=self.COLORS["bg_secondary"])
        padding_admin.pack(fill="both", expand=True, padx=20, pady=20)

        Label(
            padding_admin,
            text="🔐 Área Administrativa",
            font=tkFont.Font(family="Arial", size=12, weight="bold"),
            bg=self.COLORS["bg_secondary"],
            fg=self.COLORS["text_primary"]
        ).pack(pady=(0, 10))

        self.btn_ver_senhas = Button(
            padding_admin,
            text="🔍 Ver Senhas",
            font=self.font_button,
            bg=self.COLORS["primary"],
            fg=self.COLORS["text_primary"],
            activebackground=self.COLORS["primary_hover"],
            activeforeground=self.COLORS["text_primary"],
            command=self._ver_senhas_dialog,
            state="disabled"
        )
        self.btn_ver_senhas.pack(fill="x", pady=5)

        self.btn_consultar = Button(
            padding_admin,
            text="📋 Consultar Usuários",
            font=self.font_button,
            bg=self.COLORS["primary"],
            fg=self.COLORS["text_primary"],
            activebackground=self.COLORS["primary_hover"],
            activeforeground=self.COLORS["text_primary"],
            command=self._consultar_usuarios_dialog,
            state="disabled"
        )
        self.btn_consultar.pack(fill="x", pady=5)

        self.btn_excluir = Button(
            padding_admin,
            text="🗑️ Excluir Usuário",
            font=self.font_button,
            bg=self.COLORS["danger"],
            fg=self.COLORS["text_primary"],
            activebackground="#e81b23",
            activeforeground=self.COLORS["text_primary"],
            command=self._excluir_usuario_dialog,
            state="disabled"
        )
        self.btn_excluir.pack(fill="x", pady=5)

    # ----------------- Login / User actions -----------------
    def _fazer_login(self):
        usuario = self.entry_usuario.get().strip()
        senha = self.entry_senha.get()

        if not usuario or not senha:
            messagebox.showwarning("Aviso", "Por favor, preencha todos os campos!")
            return

        # Autenticar
        if autenticar(usuario, senha):
            self.usuario_logado = usuario
            self.admin_mode = (usuario.lower() == "admin")
            self._atualizar_botoes_admin()
            messagebox.showinfo("Sucesso", f"Bem-vindo, {usuario}! 👋")
            self.after(100, self.destroy)  # Ensure window closes after login
        else:
            messagebox.showerror("Erro", "Usuário ou senha incorretos! ❌")
            self.entry_senha.delete(0, "end")
            self.entry_usuario.focus()

    def _cadastro_dialog(self):
        # Janela de cadastro
        janela = Toplevel(self)
        janela.title("Cadastrar Novo Usuário")
        janela.geometry("300x250")
        janela.grab_set()

        # Usuário
        Label(janela, text="Usuário:", font=self.font_label).pack(pady=(10, 0), anchor="w", padx=10)
        entry_user = Entry(janela, font=self.font_label)
        entry_user.pack(fill="x", padx=10, pady=(0, 10))
        entry_user.focus()

        # Senha
        Label(janela, text="Senha:", font=self.font_label).pack(anchor="w", padx=10)
        entry_pass = Entry(janela, font=self.font_label, show="•")
        entry_pass.pack(fill="x", padx=10, pady=(0, 10))

        # Confirmar Senha
        Label(janela, text="Confirmar Senha:", font=self.font_label).pack(anchor="w", padx=10)
        entry_pass_confirm = Entry(janela, font=self.font_label, show="•")
        entry_pass_confirm.pack(fill="x", padx=10, pady=(0, 20))

        def registrar():
            user = entry_user.get().strip()
            pwd = entry_pass.get()
            pwd_confirm = entry_pass_confirm.get()

            if not user or not pwd:
                messagebox.showwarning("Aviso", "Preencha todos os campos!")
                return

            if pwd != pwd_confirm:
                messagebox.showerror("Erro", "Senhas não conferem!")
                return

            if cadastrar_usuario(user, pwd):
                messagebox.showinfo("Sucesso", f"Usuário '{user}' cadastrado! ✅")
                janela.destroy()
            else:
                messagebox.showerror("Erro", f"Usuário '{user}' já existe!")

        # Botão Registrar
        Button(
            janela,
            text="✅ Registrar",
            font=self.font_button,
            bg=self.COLORS["success"],
            fg=self.COLORS["text_primary"],
            command=registrar
        ).pack(fill="x", padx=10, pady=5)

        Button(
            janela,
            text="❌ Cancelar",
            font=self.font_button,
            bg=self.COLORS["danger"],
            fg=self.COLORS["text_primary"],
            command=janela.destroy
        ).pack(fill="x", padx=10, pady=5)

    def _alterar_senha_dialog(self):
        usuario = simpledialog.askstring("Alterar Senha", f"{ICONS['user']} Qual seu usuário?", parent=self)
        if not usuario:
            return

        senha_atual = simpledialog.askstring("Alterar Senha", f"{ICONS['lock']} Senha atual?", show="•", parent=self)
        if not senha_atual:
            return

        # Verificar senha
        if not autenticar(usuario, senha_atual):
            messagebox.showerror("Erro", "Senha atual incorreta!")
            return

        nova_senha = simpledialog.askstring("Alterar Senha", "Nova senha?", show="•", parent=self)
        if not nova_senha:
            return

        confirma_senha = simpledialog.askstring("Alterar Senha", "Confirme a nova senha?", show="•", parent=self)
        if nova_senha != confirma_senha:
            messagebox.showerror("Erro", "Senhas não conferem!")
            return

        if alterar_senha(usuario, senha_atual, nova_senha):
            messagebox.showinfo("Sucesso", "Senha alterada com sucesso! ✅")
        else:
            messagebox.showerror("Erro", "Erro ao alterar senha!")

    def _ver_senhas_dialog(self):
        if not self.admin_mode:
            messagebox.showerror("Erro", "Acesso negado!")
            return

        senhas = obter_senhas()

        janela = Toplevel(self)
        janela.title("🔐 Senhas Cadastradas (ADMIN)")
        janela.geometry("400x300")
        janela.grab_set()

        from tkinter import Scrollbar, Listbox

        listbox = Listbox(janela, font=("Courier", 10))
        scrollbar = Scrollbar(janela, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)

        listbox.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        if senhas:
            for usuario, senha in senhas.items():
                listbox.insert("end", f"{usuario}: {senha}")
        else:
            listbox.insert("end", "Nenhum usuário cadastrado")

    def _consultar_usuarios_dialog(self):
        if not self.admin_mode:
            messagebox.showerror("Erro", "Acesso negado!")
            return

        usuarios = obter_usuarios()

        janela = Toplevel(self)
        janela.title("📋 Usuários Cadastrados (ADMIN)")
        janela.geometry("300x300")
        janela.grab_set()

        from tkinter import Scrollbar, Listbox

        listbox = Listbox(janela, font=("Courier", 10))
        scrollbar = Scrollbar(janela, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)

        listbox.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        if usuarios:
            for i, usuario in enumerate(usuarios, 1):
                listbox.insert("end", f"{i}. {usuario}")
        else:
            listbox.insert("end", "Nenhum usuário cadastrado")

    def _excluir_usuario_dialog(self):
        if not self.admin_mode:
            messagebox.showerror("Erro", "Acesso negado!")
            return

        usuario = simpledialog.askstring("Excluir Usuário", f"{ICONS['user']} Qual usuário deseja excluir?", parent=self)
        if not usuario:
            return

        if usuario.lower() == "admin":
            messagebox.showerror("Erro", "Não é possível excluir o usuário admin!")
            return

        confirma = messagebox.askyesno("Confirmar", f"Deseja realmente excluir '{usuario}'? ⚠️")

        if confirma and excluir_usuario(usuario):
            messagebox.showinfo("Sucesso", f"Usuário '{usuario}' excluído! ✅")
        else:
            messagebox.showerror("Erro", f"Erro ao excluir usuário '{usuario}'!")

    def _atualizar_botoes_admin(self):
        if self.admin_mode:
            self.btn_ver_senhas.config(state="normal")
            self.btn_consultar.config(state="normal")
            self.btn_excluir.config(state="normal")
        else:
            self.btn_ver_senhas.config(state="disabled")
            self.btn_consultar.config(state="disabled")
            self.btn_excluir.config(state="disabled")

    # ----------------- Autocomplete and theme -----------------
    def _on_usuario_key(self, event=None):
        texto = self.entry_usuario.get().strip()
        usuarios = obter_usuarios()
        if not texto or not usuarios:
            self._hide_suggest()
            return

        termo = texto.lower()
        sugestoes = [u for u in usuarios if u.lower().startswith(termo)]
        if not sugestoes:
            sugestoes = [u for u in usuarios if termo in u.lower()]

        if sugestoes:
            self._show_suggest(sugestoes)
        else:
            self._hide_suggest()

    def _show_suggest(self, sugestoes):
        try:
            # Create popup only once
            if self._suggest_win and self._suggest_win.winfo_exists():
                win = self._suggest_win
                # Update geometry and contents only
                x = self.entry_usuario.winfo_rootx()
                y = self.entry_usuario.winfo_rooty() + self.entry_usuario.winfo_height()
                win.geometry(f"{250}x{min(150, 24 * len(sugestoes))}+{x}+{y}")
                # Find or create Listbox
                lb = None
                for child in win.winfo_children():
                    if child.winfo_class() == 'Listbox':
                        lb = child
                        break
                if lb:
                    lb.delete(0, "end")
                    for s in sugestoes[:10]:
                        lb.insert("end", s)
                else:
                    from tkinter import Listbox
                    lb = Listbox(win, font=self.font_label, activestyle="none")
                    lb.pack(side="left", fill="both", expand=True)
                    for s in sugestoes[:10]:
                        lb.insert("end", s)
                    self._bind_suggest_listbox(lb)
            else:
                win = Toplevel(self)
                win.overrideredirect(True)
                win.attributes("-topmost", True)
                self._suggest_win = win
                x = self.entry_usuario.winfo_rootx()
                y = self.entry_usuario.winfo_rooty() + self.entry_usuario.winfo_height()
                win.geometry(f"{250}x{min(150, 24 * len(sugestoes))}+{x}+{y}")
                from tkinter import Listbox
                lb = Listbox(win, font=self.font_label, activestyle="none")
                lb.pack(side="left", fill="both", expand=True)
                for s in sugestoes[:10]:
                    lb.insert("end", s)
                self._bind_suggest_listbox(lb)
        except Exception:
            pass

    def _bind_suggest_listbox(self, lb):
        def on_select_click(event):
            idx = lb.nearest(event.y)
            if idx is None:
                return
            val = lb.get(idx)
            self.entry_usuario.delete(0, "end")
            self.entry_usuario.insert(0, val)
            self._hide_suggest()
            self.entry_senha.focus()

        def on_select_key(event):
            sel = lb.curselection()
            if not sel:
                return
            val = lb.get(sel[0])
            self.entry_usuario.delete(0, "end")
            self.entry_usuario.insert(0, val)
            self._hide_suggest()
            self.entry_senha.focus()

        lb.bind("<ButtonRelease-1>", on_select_click)
        lb.bind("<Double-Button-1>", on_select_click)
        lb.bind("<Return>", on_select_key)

        def on_lb_key(event):
            if event.keysym == "Up" and lb.curselection():
                idx = lb.curselection()[0]
                if idx == 0:
                    self.entry_usuario.focus()
            elif event.keysym == "Escape":
                self._hide_suggest()

        lb.bind("<Key>", on_lb_key)

    def _focus_suggest(self, event=None):
        # Only move focus to Listbox if popup exists
        try:
            if self._suggest_win and self._suggest_win.winfo_exists():
                lb = None
                for c in self._suggest_win.winfo_children():
                    if c.winfo_class() == 'Listbox':
                        lb = c
                        break
                if lb:
                    lb.focus_set()
                    lb.selection_set(0)
        except Exception:
            pass

    def _hide_suggest(self):
        try:
            if self._suggest_win and self._suggest_win.winfo_exists():
                self._suggest_win.destroy()
            self._suggest_win = None
        except Exception:
            self._suggest_win = None

    def _focus_suggest(self, event=None):
        # try to focus the listbox in suggest window
        try:
            if self._suggest_win and self._suggest_win.winfo_exists():
                lb = None
                for c in self._suggest_win.winfo_children():
                    if c.winfo_class() == 'Listbox':
                        lb = c
                        break
                if lb:
                    lb.focus_set()
                    lb.selection_set(0)
        except Exception:
            pass

    def toggle_theme(self):
        # switch theme and reapply colors
        self.theme = 'light' if self.theme == 'dark' else 'dark'
        self.COLORS = self.PALETTES[self.theme]
        self._salvar_tema()
        self.btn_theme.config(text="☀️" if self.theme == "dark" else "🌙")
        self._apply_theme()

    def _apply_theme(self):
        # update primary containers and key widgets
        try:
            self.configure(bg=self.COLORS["bg_primary"])
            self.main_frame.configure(bg=self.COLORS["bg_primary"])
            self.header_frame.configure(bg=self.COLORS["primary"])
            self.title_label.configure(bg=self.COLORS["primary"], fg=self.COLORS["text_primary"])
            self.subtitle_label.configure(bg=self.COLORS["primary"], fg=self.COLORS["text_secondary"])
            self.btn_theme.configure(bg=self.COLORS["primary"], fg=self.COLORS["text_primary"])

            self.content_frame.configure(bg=self.COLORS["bg_primary"])
            self.login_frame.configure(bg=self.COLORS["bg_secondary"])
            self.padding.configure(bg=self.COLORS["bg_secondary"])

            for w in [self.entry_usuario, self.entry_senha, self.btn_login]:
                try:
                    if isinstance(w, Entry):
                        w.configure(bg=self.COLORS["bg_tertiary"], fg=self.COLORS["text_primary"], insertbackground=self.COLORS["text_primary"])
                    else:
                        w.configure(bg=self.COLORS["primary"], fg=self.COLORS["text_primary"], activebackground=self.COLORS["primary_hover"]) 
                except Exception:
                    pass

            # register and admin
            self.register_frame.configure(bg=self.COLORS["bg_secondary"])
            self.padding_reg.configure(bg=self.COLORS["bg_secondary"])
            self.admin_frame.configure(bg=self.COLORS["bg_secondary"])
        except Exception:
            pass


def tela_login_premium(root):
    login = LoginPremium(root)
    root.wait_window(login)
    return login.usuario_logado
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    usuario = tela_login_premium(root)
    print(f"Usuário logado: {usuario}")
