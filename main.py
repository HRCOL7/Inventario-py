# ===============================
# IKARUS INVENTORY - Função Principal e Ponto de Entrada
# ===============================

import sys
import tkinter as tk

from config import ARQUIVO_EXCEL_PADRAO, ABA_EXCEL_PADRAO, log
from planilha import carregar_mapeamento
from gui_premium import criar_app
from login_gui_premium import tela_login_premium

def main():
    """Função principal: inicializa a aplicação, faz login e carrega a GUI Premium"""
    
    caminho_excel, aba = ARQUIVO_EXCEL_PADRAO, ABA_EXCEL_PADRAO
    args = sys.argv[1:]
    
    if len(args) >= 1:
        caminho_excel = args[0]
    if len(args) >= 2:
        aba = args[1]

    # Criar janela temporária para o login (usar tkinter padrão)
    root_temp = tk.Tk()
    root_temp.withdraw()
    
    usuario = tela_login_premium(root_temp)
    if not usuario:
        root_temp.destroy()
        sys.exit(0)  # Saiu sem logar
    
    log("LOGIN_OK", f"usuario={usuario}")
    root_temp.destroy()

    try:
        mapeamento = carregar_mapeamento(caminho_excel, aba)
    except Exception as e:
        from tkinter import messagebox
        messagebox.showerror("Erro", f"Falha ao carregar mapeamento: {e}")
        sys.exit(1)

    # Criar app premium (captura traceback para depuração se falhar)
    try:
        app = criar_app(mapeamento)
        app.mainloop()
    except Exception:
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
