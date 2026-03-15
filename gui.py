# ===============================
# IKARUS INVENTORY - Interface Gráfica (GUI)
# ===============================

import os
from collections import Counter
from datetime import datetime
from typing import Optional, Tuple
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from config import (
    ARQUIVO_BACKUP, INTERVALO_AUTOSAVE_MS, SENHA_FINALIZAR,
    ARQUIVO_CSV_DETALHADO, ARQUIVO_CSV_NAO_MAPEADOS, 
    ARQUIVO_TXT_SAIDA, ARQUIVO_XLSX_SAIDA, log
)
from planilha import construir_dataframes
from exportacao import exportar_txt_formatado, exportar_detalhado, exportar_pdf, PDF_OK

# Utilitários de som
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

class InventarioGUI:
    """Classe principal da interface gráfica"""
    
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

        self._criar_widgets()
        self._agendar_autosave()
        self.atualizar_lista()
        self._update_status()

    def _criar_widgets(self):
        """Cria todos os widgets da interface"""
        # Painel superior
        top = tk.Frame(self.root, padx=8, pady=8)
        top.pack(fill=tk.X)

        tk.Label(top, text="CÓDIGO DE BARRAS:").grid(row=0, column=0, sticky="w")
        vcmd = (self.root.register(self._validate_cb), "%P")
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

        # Painel central com treeview
        mid = tk.Frame(self.root, padx=8, pady=6)
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

        # Painel inferior com botões
        bot = tk.Frame(self.root, pady=6)
        bot.pack(fill=tk.X)
        tk.Button(bot, text="Salvar Parcial (F1)", command=self.salvar_parcial).pack(side="left", padx=6)
        tk.Button(bot, text="Finalizar (Ctrl+F2)", command=self.finalizar).pack(side="left", padx=6)
        tk.Button(bot, text="Configurar Autosave", command=self.configurar_autosave).pack(side="left", padx=6)
        tk.Button(bot, text="Exportar Relatório", command=self.exportar_relatorio).pack(side="left", padx=6)
        tk.Button(bot, text="Imprimir Relatório", command=self.imprimir_relatorio).pack(side="left", padx=6)

        # Barra de status
        status_bar = tk.Label(self.root, textvariable=self.status_text, anchor="w", bd=1, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Atalhos
        self.root.bind("<Return>", self.processar_cb)
        self.root.bind("<F1>", lambda e: self.salvar_parcial())
        self.root.bind("<Control-s>", lambda e: self.salvar_parcial())
        self.root.bind("<Control-F2>", lambda e: self.finalizar())
        self.root.bind("<Control-f>", lambda e: self.localizar_produto_contado_dialog())
        self.entrada_cb.bind("<asterisk>", lambda e: self.pesquisar_item())
        self.entrada_cb.bind("<KP_Multiply>", lambda e: self.pesquisar_item())
        self.entrada_cb.bind("<plus>", lambda e: self.adicionar_manual())
        self.entrada_cb.bind("-", lambda e: self.subtrair_item())

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Menu de contexto
        self.menu_popup = tk.Menu(self.root, tearoff=0)
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
        messagebox.showinfo("Backup", f"Parcial salvo em {ARQUIVO_BACKUP}")

    def finalizar(self):
        senha = simpledialog.askstring("Finalizar", "Digite a senha de 6 dígitos:", show="*")
        if senha != SENHA_FINALIZAR:
            messagebox.showerror("Erro", "Senha incorreta. Finalização cancelada.")
            return
        if not messagebox.askyesno("Finalizar", "Deseja finalizar e exportar os arquivos?"):
            return
        exportar_txt_formatado(self.contagem_por_cb, self.mapeamento, ARQUIVO_TXT_SAIDA)
        exportar_detalhado(self.contagem_por_cb, self.mapeamento)
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
                exportar_pdf(self.contagem_por_cb, self.mapeamento)
                messagebox.showinfo("Exportação", "Relatório PDF gerado: relatorio_inventario.pdf", parent=self.root)
            else:
                messagebox.showerror("Erro", "Formato não suportado ou biblioteca PDF não instalada.", parent=self.root)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na exportação: {e}", parent=self.root)

    def imprimir_relatorio(self):
        try:
            relatorio = "relatorio_inventario.pdf"
            if not os.path.exists(relatorio):
                exportar_pdf(self.contagem_por_cb, self.mapeamento)
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
            beep_ok()
        else:
            self.contagem_por_cb[cb] += 1
            self.nome_produto.set("NÃO MAPEADO!")
            self.quantidade_atual.set(self.contagem_por_cb[cb])
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
            beep_ok()
        else:
            self.nome_produto.set("NÃO MAPEADO!")
            beep_erro()
        
        self.quantidade_atual.set(self.contagem_por_cb[cb])
        self.codigo_atual.set("")
        self.atualizar_lista(focus_cb=cb)
        self._update_status()
        
        try:
            exportar_detalhado(self.contagem_por_cb, self.mapeamento)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar no Excel: {e}", parent=self.root)

    def pesquisar_item(self):
        """Abre janela para pesquisar produtos"""
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
        """Abre janela para localizar item já contado (Ctrl+F)"""
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
            tag = "nao_mapeado" if ci == "" else "mapeado"
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
        
        codigo_interno = simpledialog.askstring("Cadastro Manual", "Código Interno:", parent=self.root)
        if not codigo_interno:
            return
        
        descricao = simpledialog.askstring("Cadastro Manual", "Descrição:", parent=self.root)
        if not descricao:
            return
        
        grupo = simpledialog.askstring("Cadastro Manual", "Grupo (opcional):", parent=self.root)
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
        finally:
            self._agendar_autosave()

    def on_close(self):
        resp = messagebox.askyesnocancel("Sair", "Deseja salvar antes de sair?\n(YES = salvar backup, NO = sair sem salvar, CANCEL = voltar)")
        if resp is None:
            return
        if resp:
            try:
                exportar_txt_formatado(self.contagem_por_cb, self.mapeamento, ARQUIVO_BACKUP)
                self.ultimo_backup_hora = datetime.now().strftime("%H:%M:%S")
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
        self.atualizar_lista(focus_cb=cb)
        self._update_status()

    def mostrar_ajuda_comandos(self):
        comandos = [
            ("Ctrl+F", "Localizar produto contado"),
            ("F1 ou Ctrl+S", "Salvar parcial (backup)"),
            ("Ctrl+F2", "Finalizar e exportar relatórios"),
            ("Ctrl+H", "Mostrar esta janela de ajuda"),
            ("*", "Pesquisar produto (no campo código de barras)"),
            ("+", "Adicionar produto manualmente (no campo código de barras)"),
            ("-", "Subtrair quantidade do item selecionado"),
            ("Botão direito na lista", "Menu de ações rápidas"),
        ]
        texto = "\n".join([f"{atalho:15} - {desc}" for atalho, desc in comandos])
        messagebox.showinfo("Comandos Disponíveis", texto, parent=self.root)
