# ===============================
# IKARUS INVENTORY - Funções de Login e Gerenciamento de Usuários (GUI)
# ===============================

from typing import Optional
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk, Toplevel, Listbox, Button, END

from usuarios import (
    cadastrar_usuario, autenticar, alterar_senha, excluir_usuario,
    obter_usuarios, obter_senhas, carregar_usuarios
)

def cadastrar_usuario_gui(root):
    """Janela para cadastrar novo usuário"""
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
    else:
        messagebox.showerror("Erro", "Usuário já existe!", parent=root)

def alterar_senha_gui(root, usuario):
    """Janela para alterar senha do usuário"""
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
    
    if alterar_senha(usuario, senha_atual, nova):
        messagebox.showinfo("Alterar Senha", "Senha alterada com sucesso!", parent=root)
    else:
        messagebox.showerror("Erro", "Falha ao alterar senha.", parent=root)

def mostrar_senhas_gui(root):
    """Exibe senhas de todos os usuários (apenas admin)"""
    senhas = obter_senhas()
    texto = "\n".join([f'{usuario}: {senha}' for usuario, senha in senhas.items()])
    messagebox.showinfo("Senhas dos usuários", texto or "Nenhum usuário cadastrado.", parent=root)

def consultar_usuarios_gui(root):
    """Exibe lista de usuários cadastrados"""
    usuarios = obter_usuarios()
    texto = "\n".join(usuarios) if usuarios else "Nenhum usuário cadastrado."
    messagebox.showinfo("Usuários cadastrados", texto, parent=root)

def excluir_usuario_gui(root):
    """Janela para excluir usuário"""
    usuarios = obter_usuarios()
    nomes = [u for u in usuarios if u != "admin"]
    
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
            if excluir_usuario(usuario):
                messagebox.showinfo("Excluir Usuário", f"Usuário '{usuario}' excluído.", parent=win)
                win.destroy()
            else:
                messagebox.showerror("Erro", "Falha ao excluir usuário.", parent=win)

    btn = Button(win, text="Excluir", command=excluir)
    btn.pack(pady=8)

def tela_login(root) -> Optional[str]:
    """
    Janela de login do aplicativo.
    Retorna o nome do usuário autenticado ou None se cancelado.
    """
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

    usuarios_cadastrados = obter_usuarios()

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

    root.wait_window(log_frame)
    return usuario
