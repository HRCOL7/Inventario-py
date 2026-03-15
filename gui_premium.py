# ===============================
# IKARUS INVENTORY - Interface Gráfica Premium (CustomTkinter)
# ===============================

import os
from collections import Counter
from datetime import datetime
from typing import Optional, Tuple
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog

from config import (
    ARQUIVO_BACKUP, INTERVALO_AUTOSAVE_MS, SENHA_FINALIZAR,
    ARQUIVO_CSV_DETALHADO, ARQUIVO_CSV_NAO_MAPEADOS, 
    ARQUIVO_TXT_SAIDA, ARQUIVO_XLSX_SAIDA, PASTA_NUVEM, log
)
from planilha import construir_dataframes
from exportacao import exportar_txt_formatado, exportar_detalhado, exportar_pdf, PDF_OK
from cache_utils import CacheProducts, KeyboardShortcuts
from cloud_sync import criar_pasta_sessao, sincronizar_sessao_nuvem

# Configurar tema global
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


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


ICONS = {
    "save": "💾",
    "finish": "✅",
    "cancel": "❌",
    "export": "📤",
    "print": "🖨️",
    "search": "🔍",
    "add": "➕",
    "delete": "🗑️",
    "settings": "⚙️",
    "help": "❓",
    "box": "📦",
    "barcode": "🔖",
    "info": "ℹ️",
    "warning": "⚠️",
    "chart": "📊",
}


class AppPremium(ctk.CTk):
    """Janela principal do aplicativo (CustomTkinter)
    Nota: projeto originalmente desenvolvido com customtkinter. Mantemos a
    versão premium usando ctk quando disponível.
    """

    

    def __init__(self, mapeamento: dict):
        # Inicializa a janela CTk corretamente (não passar o mapeamento ao super)
        super().__init__()
        # Usar decoração nativa do sistema (barra padrão do Windows)
        self.mapeamento = mapeamento
        self.cache = CacheProducts(mapeamento)  # Inicializar cache
        self.contagem_por_cb = Counter()
        self.nao_mapeados_tmp = Counter()

        import tkinter as _tk
        self.codigo_atual = _tk.StringVar()
        self.quantidade_atual = _tk.IntVar(value=0)
        self.nome_produto = _tk.StringVar()
        self.status_text = _tk.StringVar(value="Pronto")
        self.ultimo_backup_hora = "—"
        self.pasta_nuvem = PASTA_NUVEM
        self.pasta_sessao = ""
        self.nome_sessao = ""
        self.arquivo_backup = ARQUIVO_BACKUP
        self.arquivo_txt_saida = ARQUIVO_TXT_SAIDA
        self.arquivo_xlsx_saida = ARQUIVO_XLSX_SAIDA
        self.arquivo_csv_detalhado = ARQUIVO_CSV_DETALHADO
        self.arquivo_csv_nao_mapeados = ARQUIVO_CSV_NAO_MAPEADOS

        self.title("IKARUS INVENTORY")
        self.geometry("1400x800")
        try:
            self.iconbitmap("pena.ico")
        except Exception:
            pass

        self._inicializar_pasta_sessao()

        self._criar_theme()
        self._criar_widgets()
        self._bind_shortcuts()  # Adicionar atalhos de teclado
        self._agendar_autosave()
        self.atualizar_lista()
        self._update_status()

    def _inicializar_pasta_sessao(self):
        """Solicita nome da pasta e configura caminhos de saida da sessao."""
        nome = simpledialog.askstring(
            "Nova Contagem",
            "Nome da pasta para esta contagem:",
            parent=self
        )
        if not nome:
            nome = "contagem"

        base = "sessoes_contagem"
        self.nome_sessao = nome
        self.pasta_sessao = criar_pasta_sessao(base, nome)
        self.arquivo_backup = os.path.join(self.pasta_sessao, os.path.basename(ARQUIVO_BACKUP))
        self.arquivo_txt_saida = os.path.join(self.pasta_sessao, os.path.basename(ARQUIVO_TXT_SAIDA))
        self.arquivo_xlsx_saida = os.path.join(self.pasta_sessao, os.path.basename(ARQUIVO_XLSX_SAIDA))
        self.arquivo_csv_detalhado = os.path.join(self.pasta_sessao, os.path.basename(ARQUIVO_CSV_DETALHADO))
        self.arquivo_csv_nao_mapeados = os.path.join(self.pasta_sessao, os.path.basename(ARQUIVO_CSV_NAO_MAPEADOS))

    def _sincronizar_nuvem(self):
        """Sincroniza sessao atual para a pasta de nuvem (se configurada)."""
        try:
            sincronizar_sessao_nuvem(self.pasta_sessao, self.pasta_nuvem)
        except Exception as e:
            log("SYNC_NUVEM_ERRO", str(e))

    def _criar_theme(self):
        """Define paleta de cores premium"""
        self.COLORS = {
            "primary": "#1f6feb",
            "primary_hover": "#388bfd",
            "success": "#238636",
            "success_hover": "#2ea043",
            "danger": "#da3633",
            "danger_hover": "#f85149",
            "warning": "#d29922",
            "bg_primary": "#0d1117",
            "bg_secondary": "#161b22",
            "bg_tertiary": "#21262d",
            "border": "#30363d",
            "text_primary": "#e6edf3",
            "text_secondary": "#8b949e",
            "text_tertiary": "#6e7681",
        }
        
        self.FONTS = {
            "title": ("Segoe UI", 28, "bold"),
            "heading": ("Segoe UI", 14, "bold"),
            "body": ("Segoe UI", 12),
            "small": ("Segoe UI", 10),
            "mono": ("Consolas", 11),
        }

    def _criar_widgets(self):
        """Cria interface moderna com CustomTkinter"""
        # Configurar cores do fundo
        self.configure(fg_color=self.COLORS["bg_primary"])
        
        # ========== HEADER ==========
        header = ctk.CTkFrame(
        self,
        fg_color=self.COLORS["primary"],
        corner_radius=0,
        height=90
        )
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        title_label = ctk.CTkLabel(
            header,
            text=f"{ICONS['box']} IKARUS INVENTORY",
            font=self.FONTS["title"],
            text_color="white"
        )
        title_label.pack(padx=20, pady=(12, 2))
        
        subtitle_label = ctk.CTkLabel(
            header,
            text="Sistema de Gerenciamento de Inventário",
            font=("Segoe UI", 11),
            text_color="#b0bcc4"
        )
        subtitle_label.pack(padx=20, pady=(0, 10))

        # ========== MAIN CONTAINER ==========
        main_container = ctk.CTkFrame(
        self,
        fg_color=self.COLORS["bg_primary"],
        corner_radius=0
        )
        main_container.pack(fill="both", expand=True, padx=0, pady=0)

        # ========== LEFT PANEL - ENTRADA ==========
        left_panel = ctk.CTkFrame(
        main_container,
        fg_color=self.COLORS["bg_secondary"],
        corner_radius=12
        )
        left_panel.pack(side="left", fill="both", padx=12, pady=12, expand=False)
        left_panel.configure(width=380)

        # Card de entrada de código
        entrada_card = ctk.CTkFrame(
        left_panel,
        fg_color=self.COLORS["bg_tertiary"],
        corner_radius=8,
        border_width=1,
        border_color=self.COLORS["border"]
        )
        entrada_card.pack(fill="x", padx=12, pady=12)

        label_cb = ctk.CTkLabel(
            entrada_card,
            text=f"{ICONS['barcode']} Código de Barras",
            font=self.FONTS["body"],
            text_color=self.COLORS["text_primary"]
        )
        label_cb.pack(anchor="w", padx=12, pady=(10, 5))

        self.entrada_cb = ctk.CTkEntry(
        entrada_card,
        textvariable=self.codigo_atual,
        placeholder_text="Digite 13 dígitos...",
        font=self.FONTS["mono"],
        corner_radius=6,
        border_width=2,
        border_color=self.COLORS["border"],
        fg_color=self.COLORS["bg_primary"],
        text_color=self.COLORS["text_primary"],
        placeholder_text_color=self.COLORS["text_tertiary"]
        )
        self.entrada_cb.pack(fill="x", padx=12, pady=(0, 12))
        self.entrada_cb.focus()
        self.entrada_cb.bind("<Return>", self.processar_cb)
        self.entrada_cb.bind("<KeyRelease>", self.autopreencher_nome)

        # Card de informações
        info_card = ctk.CTkFrame(
        left_panel,
        fg_color=self.COLORS["bg_tertiary"],
        corner_radius=8,
        border_width=1,
        border_color=self.COLORS["border"]
        )
        info_card.pack(fill="x", padx=12, pady=12)

        label_nome = ctk.CTkLabel(
            info_card,
            text="Nome do Produto",
            font=self.FONTS["small"],
            text_color=self.COLORS["text_secondary"]
        )
        label_nome.pack(anchor="w", padx=12, pady=(10, 2))

        nome_display = ctk.CTkLabel(
            info_card,
            textvariable=self.nome_produto,
            font=self.FONTS["body"],
            text_color=self.COLORS["primary"],
            wraplength=320,
            justify="left",
            anchor="nw"
        )
        nome_display.pack(anchor="w", padx=12, pady=(0, 12), fill="x")

        # Card de quantidade
        qtd_card = ctk.CTkFrame(
            left_panel,
            fg_color=self.COLORS["success"],
            corner_radius=8,
            border_width=0
        )
        qtd_card.pack(fill="x", padx=12, pady=12)

        label_qtd = ctk.CTkLabel(
            qtd_card,
            text="Quantidade Atual",
            font=self.FONTS["small"],
            text_color="white"
        )
        label_qtd.pack(anchor="w", padx=12, pady=(8, 2))

        qtd_display = ctk.CTkLabel(
            qtd_card,
            textvariable=self.quantidade_atual,
            font=("Segoe UI", 36, "bold"),
            text_color="white"
        )
        qtd_display.pack(anchor="w", padx=12, pady=(0, 12))

        # Botões de ação rápida
        botoes_card = ctk.CTkFrame(
            left_panel,
            fg_color=self.COLORS["bg_tertiary"],
            corner_radius=8,
            border_width=1,
            border_color=self.COLORS["border"]
        )
        botoes_card.pack(fill="x", padx=12, pady=12)

        btn_pesquisar = ctk.CTkButton(
            botoes_card,
            text=f"{ICONS['search']} Pesquisar",
            font=self.FONTS["body"],
            fg_color=self.COLORS["primary"],
            hover_color=self.COLORS["primary_hover"],
            corner_radius=6,
            height=36,
            command=self.pesquisar_item
        )
        btn_pesquisar.pack(fill="x", padx=8, pady=6)

        btn_adicionar = ctk.CTkButton(
            botoes_card,
            text=f"{ICONS['add']} Adicionar Manual",
            font=self.FONTS["body"],
            fg_color=self.COLORS["primary"],
            hover_color=self.COLORS["primary_hover"],
            corner_radius=6,
            height=36,
            command=self.adicionar_manual
        )
        btn_adicionar.pack(fill="x", padx=8, pady=6)

        btn_localizar = ctk.CTkButton(
            botoes_card,
            text=f"{ICONS['info']} Localizar Contado",
            font=self.FONTS["body"],
            fg_color=self.COLORS["primary"],
            hover_color=self.COLORS["primary_hover"],
            corner_radius=6,
            height=36,
            command=self.localizar_produto_contado_dialog
        )
        btn_localizar.pack(fill="x", padx=8, pady=6)

        # ========== RIGHT PANEL - LISTA ==========
        right_panel = ctk.CTkFrame(
            main_container,
            fg_color=self.COLORS["bg_secondary"],
            corner_radius=12
        )
        right_panel.pack(side="left", fill="both", expand=True, padx=12, pady=12)

        # Título da lista
        lista_title = ctk.CTkLabel(
            right_panel,
            text=f"{ICONS['box']} Produtos Contados",
            font=self.FONTS["heading"],
            text_color=self.COLORS["text_primary"]
        )
        lista_title.pack(anchor="w", padx=12, pady=(12, 8))

        # Criar lista de produtos usando ScrollableFrame
        self.lista_scrollable = ctk.CTkScrollableFrame(
            right_panel,
            fg_color=self.COLORS["bg_primary"],
            corner_radius=8,
            border_width=1,
            border_color=self.COLORS["border"]
        )
        self.lista_scrollable.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.lista_items = []  # Armazenar referências dos itens

        # ========== BOTTOM PANEL - AÇÕES ==========
        bottom_panel = ctk.CTkFrame(
            main_container,
            fg_color=self.COLORS["bg_primary"],
            corner_radius=0
        )
        bottom_panel.pack(fill="x", padx=12, pady=12)

        # Botões de ação
        btn_frame = ctk.CTkFrame(bottom_panel, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 8))

        btn_salvar = ctk.CTkButton(
            btn_frame,
            text=f"{ICONS['save']} Salvar Parcial (F1)",
            font=self.FONTS["body"],
            fg_color=self.COLORS["primary"],
            hover_color=self.COLORS["primary_hover"],
            corner_radius=6,
            height=40,
            command=self.salvar_parcial
        )
        btn_salvar.pack(side="left", padx=6)

        btn_finalizar = ctk.CTkButton(
            btn_frame,
            text=f"{ICONS['finish']} Finalizar (Ctrl+F2)",
            font=self.FONTS["body"],
            fg_color=self.COLORS["success"],
            hover_color=self.COLORS["success_hover"],
            corner_radius=6,
            height=40,
            command=self.finalizar
        )
        btn_finalizar.pack(side="left", padx=6)

        btn_exportar = ctk.CTkButton(
            btn_frame,
            text=f"{ICONS['export']} Exportar",
            font=self.FONTS["body"],
            fg_color=self.COLORS["primary"],
            hover_color=self.COLORS["primary_hover"],
            corner_radius=6,
            height=40,
            command=self.exportar_relatorio
        )
        btn_exportar.pack(side="left", padx=6)

        btn_config = ctk.CTkButton(
            btn_frame,
            text=f"{ICONS['settings']} Configurar",
            font=self.FONTS["body"],
            fg_color=self.COLORS["primary"],
            hover_color=self.COLORS["primary_hover"],
            corner_radius=6,
            height=40,
            command=self.configurar_autosave
        )
        btn_config.pack(side="left", padx=6)

        btn_ajuda = ctk.CTkButton(
            btn_frame,
            text=f"{ICONS['help']} Ajuda",
            font=self.FONTS["body"],
            fg_color=self.COLORS["primary"],
            hover_color=self.COLORS["primary_hover"],
            corner_radius=6,
            height=40,
            command=self.mostrar_ajuda_comandos
        )
        btn_ajuda.pack(side="left", padx=6)

        # Status bar
        status_frame = ctk.CTkFrame(
            bottom_panel,
            fg_color=self.COLORS["bg_secondary"],
            corner_radius=6,
            border_width=1,
            border_color=self.COLORS["border"]
        )
        status_frame.pack(fill="x", pady=8)

        status_label = ctk.CTkLabel(
            status_frame,
            textvariable=self.status_text,
            font=self.FONTS["small"],
            text_color=self.COLORS["text_secondary"],
            anchor="w"
        )
        status_label.pack(anchor="w", padx=12, pady=8)

        # Atalhos
        self.bind("<F1>", lambda e: self.salvar_parcial())
        self.bind("<Control-s>", lambda e: self.salvar_parcial())
        self.bind("<Control-F2>", lambda e: self.finalizar())
        self.bind("<Control-f>", lambda e: self.localizar_produto_contado_dialog())
        self.bind("<Control-h>", lambda e: self.mostrar_ajuda_comandos())
        self.entrada_cb.bind("<asterisk>", lambda e: self.pesquisar_item())
        self.entrada_cb.bind("<KP_Multiply>", lambda e: self.pesquisar_item())
        self.entrada_cb.bind("<plus>", lambda e: self.adicionar_manual())
        self.entrada_cb.bind("<minus>", lambda e: self.subtrair_item())

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # (usar redimensionamento nativo do gerenciador de janelas)

    def _bind_shortcuts(self):
        """Bind keyboard shortcuts to actions"""
        self.bind("<Control-s>", lambda e: self.salvar_parcial())
        self.bind("<Control-q>", lambda e: self.on_close())
        self.bind("<Control-f>", lambda e: self.pesquisar_item())
        self.bind("<F1>", lambda e: self.abrir_ajuda())
        self.bind("<F5>", lambda e: self.atualizar_lista())

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
        try:
            exportar_txt_formatado(self.contagem_por_cb, self.mapeamento, self.arquivo_backup)
            self.ultimo_backup_hora = datetime.now().strftime("%H:%M:%S")
            self._sincronizar_nuvem()
            self._update_status()
            messagebox.showinfo("Backup", f"Parcial salvo com sucesso em\n{self.arquivo_backup}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar: {e}")

    def finalizar(self):
        senha = simpledialog.askstring("Finalizar", "Digite a senha de 6 dígitos:", show="*")
        if senha != SENHA_FINALIZAR:
            messagebox.showerror("Erro", "Senha incorreta. Finalização cancelada.")
            beep_erro()
            return
        if not messagebox.askyesno("Finalizar", "Deseja finalizar e exportar os arquivos?"):
            return
        try:
            exportar_txt_formatado(self.contagem_por_cb, self.mapeamento, self.arquivo_txt_saida)
            exportar_detalhado(self.contagem_por_cb, self.mapeamento, output_dir=self.pasta_sessao)
            self._sincronizar_nuvem()
            beep_ok()
            messagebox.showinfo(
                "Finalizado",
                f"Exportado com sucesso:\n- {self.arquivo_txt_saida}\n- {self.arquivo_xlsx_saida}\n- {self.arquivo_csv_detalhado}\n- {self.arquivo_csv_nao_mapeados}"
            )
            self.quit()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na finalização: {e}")

    def configurar_autosave(self):
        try:
            minutos = simpledialog.askinteger("Configurar Autosave", "Intervalo em minutos:", minvalue=1, parent=self)
            if minutos:
                global INTERVALO_AUTOSAVE_MS
                INTERVALO_AUTOSAVE_MS = minutos * 60_000
                self._agendar_autosave()
                messagebox.showinfo("Configuração", f"Autosave ajustado para cada {minutos} minutos.", parent=self)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao configurar autosave: {e}", parent=self)

    def exportar_relatorio(self):
        formatos = ["TXT", "XLSX", "CSV"]
        if PDF_OK:
            formatos.append("PDF")
        formato = simpledialog.askstring("Exportar", f"Escolha o formato ({', '.join(formatos)}):", parent=self)
        if not formato:
            return
        formato = formato.strip().upper()
        try:
            if formato == "TXT":
                exportar_txt_formatado(self.contagem_por_cb, self.mapeamento, self.arquivo_txt_saida)
                self._sincronizar_nuvem()
                messagebox.showinfo("Exportação", f"Exportado para\n{self.arquivo_txt_saida}", parent=self)
            elif formato == "XLSX":
                exportar_detalhado(self.contagem_por_cb, self.mapeamento, output_dir=self.pasta_sessao)
                self._sincronizar_nuvem()
                messagebox.showinfo("Exportação", f"Exportado para\n{self.arquivo_xlsx_saida}", parent=self)
            elif formato == "CSV":
                df, df_nm = construir_dataframes(self.contagem_por_cb, self.mapeamento)
                df.to_csv(self.arquivo_csv_detalhado, index=False, encoding="utf-8")
                df_nm.to_csv(self.arquivo_csv_nao_mapeados, index=False, encoding="utf-8")
                self._sincronizar_nuvem()
                messagebox.showinfo("Exportação", f"Exportado para\n{self.arquivo_csv_detalhado}\n{self.arquivo_csv_nao_mapeados}", parent=self)
            elif formato == "PDF" and PDF_OK:
                arquivo_pdf = exportar_pdf(self.contagem_por_cb, self.mapeamento, output_dir=self.pasta_sessao)
                self._sincronizar_nuvem()
                messagebox.showinfo("Exportação", f"Relatório PDF gerado:\n{arquivo_pdf}", parent=self)
            else:
                messagebox.showerror("Erro", "Formato não suportado.", parent=self)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na exportação: {e}", parent=self)

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
            self.quantidade_atual.set(str(self.contagem_por_cb[cb]))
            beep_ok()
        else:
            self.contagem_por_cb[cb] += 1
            self.nome_produto.set("🔴 NÃO MAPEADO!")
            self.quantidade_atual.set(str(self.contagem_por_cb[cb]))
            beep_erro()
        
        self.codigo_atual.set("")
        self.atualizar_lista(focus_cb=cb)
        self._update_status()
        return "break"

    def adicionar_manual(self):
        """Abre um mini-cadastro (modal) para adicionar produto manualmente.

        Campos: Código de Barras (opcional, 13 dígitos), Código Interno (opcional),
        Nome do Produto (obrigatório), Quantidade (padrão 1).
        """
        import uuid

        win = ctk.CTkToplevel(self)
        win.title("Adicionar produto")
        win.geometry("500x600")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()
        
        # Usar ScrollableFrame para garantir que tudo fica visível
        frame = ctk.CTkScrollableFrame(win, fg_color=self.COLORS["bg_primary"])
        frame.pack(fill="both", expand=True, padx=0, pady=0)

        lbl_cb = ctk.CTkLabel(frame, text="Código de Barras (13 dígitos) — opcional", font=self.FONTS['small'])
        lbl_cb.pack(anchor='w', pady=(0,4), padx=12)
        entry_cb = ctk.CTkEntry(frame, placeholder_text="Opcional: 13 dígitos", corner_radius=6)
        entry_cb.pack(fill='x', pady=(0,4), padx=12)
        help_cb = ctk.CTkLabel(frame, text="Se não souber o código, deixe em branco.", font=self.FONTS['small'], text_color=self.COLORS['text_tertiary'])
        help_cb.pack(anchor='w', pady=(0,10), padx=12)

        lbl_ci = ctk.CTkLabel(frame, text="Código Interno (opcional)", font=self.FONTS['small'])
        lbl_ci.pack(anchor='w', pady=(0,4), padx=12)
        entry_ci = ctk.CTkEntry(frame, placeholder_text="Opcional: código interno", corner_radius=6)
        entry_ci.pack(fill='x', pady=(0,4), padx=12)
        help_ci = ctk.CTkLabel(frame, text="Código interno é útil para seu controle interno.", font=self.FONTS['small'], text_color=self.COLORS['text_tertiary'])
        help_ci.pack(anchor='w', pady=(0,10), padx=12)

        lbl_nome = ctk.CTkLabel(frame, text="Nome do Produto", font=self.FONTS['small'])
        lbl_nome.pack(anchor='w', pady=(0,4), padx=12)
        entry_nome = ctk.CTkEntry(frame, placeholder_text="Digite o nome do produto (obrigatório)", corner_radius=6)
        entry_nome.pack(fill='x', pady=(0,4), padx=12)
        help_nome = ctk.CTkLabel(frame, text="Nome requerido. Use palavras-chave para facilitar buscas.", font=self.FONTS['small'], text_color=self.COLORS['text_tertiary'])
        help_nome.pack(anchor='w', pady=(0,10), padx=12)

        lbl_qtd = ctk.CTkLabel(frame, text="Quantidade", font=self.FONTS['small'])
        lbl_qtd.pack(anchor='w', pady=(0,4), padx=12)
        entry_qtd = ctk.CTkEntry(frame, placeholder_text="1", corner_radius=6)
        entry_qtd.pack(fill='x', pady=(0,4), padx=12)
        help_qtd = ctk.CTkLabel(frame, text="Quantidade padrão é 1.", font=self.FONTS['small'], text_color=self.COLORS['text_tertiary'])
        help_qtd.pack(anchor='w', pady=(0,16), padx=12)

        btns = ctk.CTkFrame(frame, fg_color="transparent")
        btns.pack(fill='x', pady=(6,12), padx=12)

        def on_cancel():
            win.destroy()

        def on_ok(event=None):
            nome = entry_nome.get().strip()
            if not nome:
                messagebox.showerror("Erro", "Nome do produto é obrigatório.", parent=win)
                return

            cb = entry_cb.get().strip()
            ci = entry_ci.get().strip()
            qtd_str = entry_qtd.get().strip()
            try:
                qtd = int(qtd_str) if qtd_str else 1
                if qtd <= 0:
                    raise ValueError()
            except Exception:
                messagebox.showerror("Erro", "Quantidade inválida.", parent=win)
                return

            # validar código de barras se informado
            if cb:
                if not (len(cb) == 13 and cb.isdigit()):
                    messagebox.showerror("Erro", "Código de barras deve ter 13 dígitos ou ficar em branco.", parent=win)
                    return

            # gerar chave interna se não houver código de barras
            if not cb:
                cb_key = f"MAN-{uuid.uuid4().hex[:8]}"
            else:
                cb_key = cb

            # adicionar ao mapeamento em memória
            try:
                self.mapeamento[cb_key] = (ci, nome, "")
            except Exception:
                # fallback: não quebrar se mapeamento não for mutável
                pass

            # Persistir alteração no arquivo de mapeamento custom
            try:
                from planilha import salvar_mapeamento_custom
                # Construir um dicionário apenas com as entradas custom (leitura atual seguida de gravacão)
                # Para simplicidade, escrevemos todo o mapeamento atual — isso permitirá que custom
                # sobrescreva entradas do Excel.
                salvar_mapeamento_custom(self.mapeamento)
            except Exception:
                pass

            # incrementar contagem
            self.contagem_por_cb[cb_key] += qtd
            self.nome_produto.set(nome)
            self.quantidade_atual.set(str(self.contagem_por_cb[cb_key]))
            beep_ok()
            self.codigo_atual.set("")
            self.atualizar_lista(focus_cb=cb_key)
            self._update_status()

            try:
                exportar_detalhado(self.contagem_por_cb, self.mapeamento, output_dir=self.pasta_sessao)
                self._sincronizar_nuvem()
            except Exception:
                pass

            win.destroy()
        # --- Validação em tempo real ---
        def validar_campos(event=None):
            # validar código de barras
            cb_val = entry_cb.get().strip()
            if cb_val and not (len(cb_val) == 13 and cb_val.isdigit()):
                try:
                    entry_cb.configure(border_color=self.COLORS['danger'])
                except Exception:
                    pass
            else:
                try:
                    entry_cb.configure(border_color=self.COLORS['border'])
                except Exception:
                    pass

            # nome obrigatório
            nome_val = entry_nome.get().strip()
            if not nome_val:
                try:
                    entry_nome.configure(border_color=self.COLORS['danger'])
                except Exception:
                    pass
            else:
                try:
                    entry_nome.configure(border_color=self.COLORS['border'])
                except Exception:
                    pass

            # quantidade válida
            qtd_val = entry_qtd.get().strip()
            try:
                if qtd_val and int(qtd_val) > 0:
                    entry_qtd.configure(border_color=self.COLORS['border'])
                else:
                    entry_qtd.configure(border_color=self.COLORS['danger'])
            except Exception:
                try:
                    entry_qtd.configure(border_color=self.COLORS['danger'])
                except Exception:
                    pass

        entry_cb.bind('<KeyRelease>', validar_campos)
        entry_nome.bind('<KeyRelease>', validar_campos)
        entry_qtd.bind('<KeyRelease>', validar_campos)
        validar_campos()

        btn_cancel = ctk.CTkButton(btns, text="Cancelar", width=100, command=on_cancel)
        btn_cancel.pack(side='right', padx=(6,0))
        btn_ok = ctk.CTkButton(btns, text="Adicionar", width=100, fg_color=self.COLORS['primary'], command=on_ok)
        btn_ok.pack(side='right')

        # Bind Enter/Escape
        entry_nome.bind("<Return>", on_ok)
        entry_qtd.bind("<Return>", on_ok)
        win.bind("<Escape>", lambda e: on_cancel())

        entry_nome.focus()

    def pesquisar_item(self):
        """Abre janela para pesquisar produtos com fuzzy matching"""
        pesquisa_win = ctk.CTkToplevel(self)
        pesquisa_win.title("Pesquisar Produto")
        pesquisa_win.geometry("700x500")
        pesquisa_win.resizable(False, False)
        
        # Header
        header = ctk.CTkFrame(pesquisa_win, fg_color=self.COLORS["primary"])
        header.pack(fill="x", padx=0, pady=0)
        
        title = ctk.CTkLabel(
            header,
            text=f"{ICONS['search']} Pesquisar Produto",
            font=self.FONTS["heading"],
            text_color="white"
        )
        title.pack(padx=15, pady=12)
        
        # Content
        content = ctk.CTkFrame(pesquisa_win, fg_color=self.COLORS["bg_primary"])
        content.pack(fill="both", expand=True, padx=12, pady=12)
        
        label_campo = ctk.CTkLabel(content, text="Campo de pesquisa:", font=self.FONTS["body"])
        label_campo.pack(anchor="w", pady=(0, 6))
        
        campo_var = ctk.StringVar(value="Descrição")
        campo_options = ["Código Interno", "Código de Barras", "Descrição"]
        campo_menu = ctk.CTkComboBox(
            content,
            values=campo_options,
            variable=campo_var,
            state="readonly",
            corner_radius=6,
            font=self.FONTS["body"]
        )
        campo_menu.pack(fill="x", pady=(0, 12))
        
        label_busca = ctk.CTkLabel(content, text="Digite para pesquisar (suporta busca aproximada):", font=self.FONTS["body"])
        label_busca.pack(anchor="w", pady=(0, 6))
        
        entry = ctk.CTkEntry(
            content,
            placeholder_text="Comece a digitar...",
            font=self.FONTS["body"],
            corner_radius=6
        )
        entry.pack(fill="x", pady=(0, 12))
        
        # Lista de resultados
        listbox_frame = ctk.CTkFrame(content, fg_color=self.COLORS["bg_secondary"], corner_radius=6)
        listbox_frame.pack(fill="both", expand=True, pady=(0, 12))
        
        listbox_scroll = ctk.CTkScrollableFrame(
            listbox_frame,
            fg_color=self.COLORS["bg_secondary"],
            corner_radius=6
        )
        listbox_scroll.pack(fill="both", expand=True, padx=1, pady=1)
        
        listbox_items = []

        def atualizar_lista_sugestoes(event=None):
            termo = entry.get()
            campo_nome = campo_var.get()
            
            if campo_nome == "Código Interno":
                campo = "codigo_interno"
            elif campo_nome == "Código de Barras":
                campo = "codigo_barra"
            else:
                campo = "nome"
            
            # Usar cache com busca combinada (prefixo + fuzzy)
            resultados = self.cache.busca_combinada(termo, campo) if termo else []
            
            # Limpar items anteriores
            for widget in listbox_items:
                widget.destroy()
            listbox_items.clear()
            
            # Exibir mensagem se não há resultados
            if not resultados:
                no_results_label = ctk.CTkLabel(
                    listbox_scroll,
                    text="Nenhum resultado encontrado",
                    text_color=self.COLORS["text_secondary"],
                    font=self.FONTS["body"]
                )
                no_results_label.pack(pady=20)
                listbox_items.append(no_results_label)
                return
            
            # detect exact match key (if user searched by internal code or barcode)
            exact_key = None
            try:
                if campo in ('codigo_interno', 'codigo_barra'):
                    idx_key = 'codigo_interno' if campo == 'codigo_interno' else 'codigo_barra'
                    exact_item = self.cache._cache_indices.get(idx_key, {}).get(termo)
                    if exact_item:
                        exact_key = (exact_item[0], exact_item[1])
            except Exception:
                exact_key = None

            for idx, (cb, ci, nm, grupo) in enumerate(resultados):
                item_frame = ctk.CTkFrame(
                    listbox_scroll,
                    fg_color=self.COLORS["bg_tertiary"],
                    corner_radius=4
                )
                item_frame.pack(fill="x", padx=2, pady=2)
                
                item_text = f"{cb} | {ci} | {nm}"
                item_label = ctk.CTkLabel(
                    item_frame,
                    text=item_text,
                    font=self.FONTS["small"],
                    text_color=self.COLORS["text_primary"],
                    wraplength=600,
                    justify="left",
                    anchor="w"
                )
                item_label.pack(fill="x", padx=8, pady=6)
                
                item_label.bind("<Button-1>", lambda e, b=cb, n=nm: selecionar_nome(b, n))
                listbox_items.append(item_frame)
                # If this item is the exact match, highlight and scroll to it
                if exact_key and (cb, ci) == exact_key:
                        # highlight
                        try:
                            item_frame.configure(fg_color=self.COLORS["primary"])
                            item_label.configure(text_color=self.COLORS["text_primary"]) 
                        except Exception:
                            pass

                        # attempt to scroll the scrollable frame to this item (best-effort)
                        try:
                            # fraction of position
                            total = max(1, len(resultados))
                            frac = idx / total
                            # try common CTkScrollableFrame internals
                            if hasattr(listbox_scroll, '_canvas'):
                                listbox_scroll._canvas.yview_moveto(frac)
                            elif hasattr(listbox_scroll, 'yview_moveto'):
                                listbox_scroll.yview_moveto(frac)
                        except Exception:
                            pass

        def selecionar_nome(cb, nm):
            self.codigo_atual.set(cb)
            self.nome_produto.set(nm)
            qtd = simpledialog.askinteger("Adicionar", f"Quantidade para '{nm}':", minvalue=1, parent=pesquisa_win)
            if qtd:
                self.contagem_por_cb[cb] += qtd
                self.atualizar_lista(focus_cb=cb)
                self._update_status()
            pesquisa_win.destroy()

        # Usar debounce para evitar múltiplas chamadas
        self._search_timer = None
        
        def atualizar_com_debounce(event=None):
            if self._search_timer:
                pesquisa_win.after_cancel(self._search_timer)
            self._search_timer = pesquisa_win.after(100, atualizar_lista_sugestoes)
        
        campo_menu.configure(command=lambda x: atualizar_com_debounce())
        entry.bind("<KeyRelease>", atualizar_com_debounce)
        entry.focus()
        atualizar_lista_sugestoes()

        pesquisa_win.transient(self)
        pesquisa_win.grab_set()

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
            return resultados[:50]

        busca_win = ctk.CTkToplevel(self)
        busca_win.title("Localizar Produto Contado")
        busca_win.geometry("700x500")
        busca_win.resizable(False, False)
        
        # Header
        header = ctk.CTkFrame(busca_win, fg_color=self.COLORS["primary"])
        header.pack(fill="x", padx=0, pady=0)
        
        title = ctk.CTkLabel(
            header,
            text=f"{ICONS['info']} Localizar Produto Contado",
            font=self.FONTS["heading"],
            text_color="white"
        )
        title.pack(padx=15, pady=12)
        
        # Content
        content = ctk.CTkFrame(busca_win, fg_color=self.COLORS["bg_primary"])
        content.pack(fill="both", expand=True, padx=12, pady=12)
        
        label_campo = ctk.CTkLabel(content, text="Campo de pesquisa:", font=self.FONTS["body"])
        label_campo.pack(anchor="w", pady=(0, 6))
        
        campo_var = ctk.StringVar(value="Descrição")
        campo_options = ["Descrição", "Código Interno", "Código de Barras"]
        campo_menu = ctk.CTkComboBox(
            content,
            values=campo_options,
            variable=campo_var,
            state="readonly",
            corner_radius=6,
            font=self.FONTS["body"]
        )
        campo_menu.pack(fill="x", pady=(0, 12))
        
        label_busca = ctk.CTkLabel(content, text="Digite para pesquisar:", font=self.FONTS["body"])
        label_busca.pack(anchor="w", pady=(0, 6))
        
        entry = ctk.CTkEntry(
            content,
            placeholder_text="Comece a digitar...",
            font=self.FONTS["body"],
            corner_radius=6
        )
        entry.pack(fill="x", pady=(0, 12))
        
        # Lista de resultados
        listbox_frame = ctk.CTkFrame(content, fg_color=self.COLORS["bg_secondary"], corner_radius=6)
        listbox_frame.pack(fill="both", expand=True, pady=(0, 12))
        
        listbox_scroll = ctk.CTkScrollableFrame(
            listbox_frame,
            fg_color=self.COLORS["bg_secondary"],
            corner_radius=6
        )
        listbox_scroll.pack(fill="both", expand=True, padx=1, pady=1)
        
        listbox_items = []

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
            
            for widget in listbox_items:
                widget.destroy()
            listbox_items.clear()
            
            for cb, ci, nm, qtd in resultados:
                item_frame = ctk.CTkFrame(
                    listbox_scroll,
                    fg_color=self.COLORS["bg_tertiary"],
                    corner_radius=4
                )
                item_frame.pack(fill="x", padx=2, pady=2)
                
                cor_qtd = self.COLORS["success"] if qtd > 0 else self.COLORS["text_tertiary"]
                item_text = f"{cb} | {ci} | {nm} | {ICONS['box']} {qtd}"
                item_label = ctk.CTkLabel(
                    item_frame,
                    text=item_text,
                    font=self.FONTS["small"],
                    text_color=cor_qtd,
                    wraplength=600,
                    justify="left",
                    anchor="w"
                )
                item_label.pack(fill="x", padx=8, pady=6)
                
                item_label.bind("<Button-1>", lambda e, b=cb: selecionar_item(b))
                listbox_items.append(item_frame)

        def selecionar_item(cb):
            self.atualizar_lista(focus_cb=cb)
            busca_win.destroy()

        # Usar debounce para evitar múltiplas chamadas
        self._search_timer2 = None
        
        def atualizar_com_debounce(event=None):
            if self._search_timer2:
                busca_win.after_cancel(self._search_timer2)
            self._search_timer2 = busca_win.after(100, atualizar_lista)
        
        campo_menu.configure(command=lambda x: atualizar_com_debounce())
        entry.bind("<KeyRelease>", atualizar_com_debounce)
        entry.focus()
        atualizar_lista()

        busca_win.transient(self)
        busca_win.grab_set()

    def atualizar_lista(self, focus_cb: Optional[str] = None):
        """Atualiza a lista de produtos contados"""
        # Limpar items anteriores
        for widget in self.lista_items:
            widget.destroy()
        self.lista_items.clear()
        
        # Adicionar items
        for cb, qtd in sorted(self.contagem_por_cb.items(), key=lambda x: x[0]):
            if qtd <= 0:
                continue
            
            ci, nm, *_ = self.mapeamento.get(cb, ("", "(NÃO MAPEADO)", ""))
            eh_mapeado = ci != ""
            
            # Determinar cor
            if eh_mapeado:
                fg_color = self.COLORS["success"]
                icon = "✅"
            else:
                fg_color = self.COLORS["danger"]
                icon = "❌"
            
            item_frame = ctk.CTkFrame(
                self.lista_scrollable,
                fg_color=self.COLORS["bg_tertiary"],
                corner_radius=6,
                border_width=1,
                border_color=self.COLORS["border"]
            )
            item_frame.pack(fill="x", padx=6, pady=3)
            
            # Conteúdo do item
            content_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            content_frame.pack(fill="x", padx=10, pady=8)
            
            # Linha 1: Código e Status
            line1 = ctk.CTkFrame(content_frame, fg_color="transparent")
            line1.pack(fill="x", padx=0, pady=(0, 4))
            
            status_label = ctk.CTkLabel(
                line1,
                text=f"{icon} {cb}",
                font=self.FONTS["mono"],
                text_color=fg_color
            )
            status_label.pack(side="left", padx=(0, 8))
            
            qtd_label = ctk.CTkLabel(
                line1,
                text=f"{ICONS['box']} {qtd}x",
                font=("Segoe UI", 11, "bold"),
                text_color=self.COLORS["text_primary"]
            )
            qtd_label.pack(side="right", padx=0)
            
            # Linha 2: Nome
            name_label = ctk.CTkLabel(
                content_frame,
                text=f"📝 {nm}",
                font=self.FONTS["small"],
                text_color=self.COLORS["text_secondary"],
                wraplength=500,
                justify="left",
                anchor="w"
            )
            name_label.pack(anchor="w", padx=0)
            
            self.lista_items.append(item_frame)
            
            # Focar se for o item atual
            if focus_cb and cb == focus_cb:
                self.entrada_cb.focus()

    def _totais(self) -> Tuple[int, int, int]:
        total = sum(q for q in self.contagem_por_cb.values() if q > 0)
        map_total = sum(q for cb, q in self.contagem_por_cb.items() if q > 0 and cb in self.mapeamento and self.mapeamento[cb][0] != "")
        nm_total = total - map_total
        return total, map_total, nm_total

    def _update_status(self):
        total, map_total, nm_total = self._totais()
        taxa = int((map_total / total * 100) if total > 0 else 0)
        status = f"📦 Total: {total} | ✅ Mapeados: {map_total} ({taxa}%) | ❌ Não mapeados: {nm_total} | 🕒 Backup: {self.ultimo_backup_hora}"
        self.status_text.set(status)

    def _agendar_autosave(self):
        self.after(INTERVALO_AUTOSAVE_MS, self._autosave_tick)

    def _autosave_tick(self):
        try:
            exportar_txt_formatado(self.contagem_por_cb, self.mapeamento, self.arquivo_backup)
            self.ultimo_backup_hora = datetime.now().strftime("%H:%M:%S")
            self._sincronizar_nuvem()
            self._update_status()
        finally:
            self._agendar_autosave()

    def on_close(self):
        resp = messagebox.askyesnocancel("Sair", "Deseja salvar antes de sair?\n\n✅ SIM = salvar backup\n❌ NÃO = sair sem salvar\n⏸️ CANCELAR = voltar")
        if resp is None:
            return
        if resp:
            try:
                exportar_txt_formatado(self.contagem_por_cb, self.mapeamento, self.arquivo_backup)
                self.ultimo_backup_hora = datetime.now().strftime("%H:%M:%S")
                self._sincronizar_nuvem()
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao salvar: {e}")
        self.destroy()

    def toggle_max_restore(self):
        """Alterna entre maximizar e restaurar a janela (simula maximize para frameless)."""
        try:
            if getattr(self, "_is_maximized", False):
                # restaurar
                geom = getattr(self, "_restore_geom", None)
                if geom:
                    self.geometry(geom)
                self._is_maximized = False
            else:
                # salvar geometria atual e expandir para a tela
                self._restore_geom = self.geometry()
                sw = self.winfo_screenwidth()
                sh = self.winfo_screenheight()
                # posicionar em 0,0 com tamanho da tela
                self.geometry(f"{sw}x{sh}+0+0")
                self._is_maximized = True
        except Exception:
            pass

    def _start_resize(self, event):
        try:
            self._resizing = True
            self._resize_start_x = event.x_root
            self._resize_start_y = event.y_root
            geom = self.geometry().split('+')[0]
            w, h = geom.split('x')
            self._resize_width = int(w)
            self._resize_height = int(h)
        except Exception:
            self._resizing = False

    def _do_resize(self, event):
        if not getattr(self, '_resizing', False):
            return
        try:
            dx = event.x_root - self._resize_start_x
            dy = event.y_root - self._resize_start_y
            new_w = max(600, self._resize_width + dx)
            new_h = max(400, self._resize_height + dy)
            self.geometry(f"{new_w}x{new_h}")
        except Exception:
            pass

    def _minimize_with_override(self):
        """Minimiza a janela mesmo quando override-redirect está ativo.

        Estratéga: antes de iconify, desativa override-redirect, iconifica,
        e então quando a janela for re-mapeada (após restore) reaplica override.
        """
        try:
            # se já não tem override, apenas iconify
            if not self.overrideredirect():
                self.iconify()
                return
        except Exception:
            # some tkinter versions may not allow reading overrideredirect; try safe path
            pass

        try:
            # desativa override temporariamente
            try:
                self.overrideredirect(False)
            except Exception:
                pass
            # iconify (minimizar)
            try:
                self.iconify()
            except Exception:
                # fallback para withdraw
                try:
                    self.withdraw()
                except Exception:
                    pass

            # quando a janela for mapeada novamente, reaplicar overrideredirect
            def _on_map(event):
                try:
                    # reaplicar depois de um pequeno atraso
                    self.after(50, lambda: self.overrideredirect(True))
                except Exception:
                    pass
                try:
                    self.unbind("<Map>", _on_map_id)
                except Exception:
                    pass

            try:
                _on_map_id = self.bind("<Map>", _on_map)
            except Exception:
                pass
        except Exception:
            pass

    def subtrair_item(self, event=None):
        if not self.lista_items:
            messagebox.showinfo("Info", "Nenhum item para subtrair.")
            return
        
        # Pegar último item adicionado
        cb_input = simpledialog.askstring("Subtrair", "Digite o código de barras:", parent=self)
        if not cb_input:
            return
        
        if cb_input not in self.contagem_por_cb:
            messagebox.showinfo("Não encontrado", f"Código {cb_input} não foi contado.")
            return
        
        qtd = simpledialog.askinteger("Subtrair", f"Quantidade a subtrair de {cb_input}:", minvalue=1, parent=self)
        if qtd is None:
            return
        
        anterior = self.contagem_por_cb.get(cb_input, 0)
        self.contagem_por_cb[cb_input] = max(0, anterior - qtd)
        self.atualizar_lista(focus_cb=cb_input)
        self._update_status()

    def mostrar_ajuda_comandos(self):
        """Exibe janela com comandos disponíveis"""
        ajuda_win = ctk.CTkToplevel(self)
        ajuda_win.title("Ajuda - Comandos")
        ajuda_win.geometry("600x500")
        ajuda_win.resizable(False, False)
        
        # Header
        header = ctk.CTkFrame(ajuda_win, fg_color=self.COLORS["primary"])
        header.pack(fill="x", padx=0, pady=0)
        
        title = ctk.CTkLabel(
            header,
            text=f"{ICONS['help']} Comandos Disponíveis",
            font=self.FONTS["heading"],
            text_color="white"
        )
        title.pack(padx=15, pady=12)
        
        # Content
        content = ctk.CTkScrollableFrame(ajuda_win, fg_color=self.COLORS["bg_primary"])
        content.pack(fill="both", expand=True, padx=12, pady=12)
        
        # Título de atalhos
        title_shortcuts = ctk.CTkLabel(
            content,
            text="⌨️ Atalhos de Teclado",
            font=("Segoe UI", 13, "bold"),
            text_color=self.COLORS["primary"]
        )
        title_shortcuts.pack(anchor="w", padx=0, pady=(0, 8))
        
        # Todos os atalhos do sistema
        all_shortcuts = KeyboardShortcuts.get_all_shortcuts()
        
        for descricao, display in all_shortcuts.items():
            card = ctk.CTkFrame(content, fg_color=self.COLORS["bg_secondary"], corner_radius=6)
            card.pack(fill="x", padx=0, pady=4)
            
            atalho_label = ctk.CTkLabel(
                card,
                text=display,
                font=("Segoe UI", 11, "bold"),
                text_color=self.COLORS["primary"],
                width=140,
                anchor="w"
            )
            atalho_label.pack(side="left", padx=10, pady=8)
            
            desc_label = ctk.CTkLabel(
                card,
                text=descricao,
                font=self.FONTS["small"],
                text_color=self.COLORS["text_secondary"],
                anchor="w"
            )
            desc_label.pack(side="left", padx=0, pady=8, fill="x", expand=True)
        
        # Botão OK
        btn_ok = ctk.CTkButton(
            ajuda_win,
            text="OK",
            font=self.FONTS["body"],
            fg_color=self.COLORS["primary"],
            hover_color=self.COLORS["primary_hover"],
            corner_radius=6,
            height=36,
            command=ajuda_win.destroy
        )
        btn_ok.pack(padx=12, pady=12, fill="x")
        
        ajuda_win.transient(self)
        ajuda_win.grab_set()


# Função para criar a aplicação
def criar_app(mapeamento: dict):
    """Factory function para criar e retornar a aplicação"""
    app = AppPremium(mapeamento)
    return app
