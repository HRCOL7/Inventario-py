import argparse
import json
import os
from collections import Counter
from threading import Lock

from flask import Flask, jsonify, request, send_from_directory

from cloud_sync import criar_pasta_sessao
from config import PASTA_NUVEM, log
from planilha import carregar_mapeamento, salvar_mapeamento_custom


def _load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return default


def _save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def create_mobile_app(caminho_excel, aba=None, session_dir=None):
    app = Flask(__name__, static_folder="mobile", static_url_path="")

    mapeamento = carregar_mapeamento(caminho_excel, aba)

    if session_dir:
        pasta_sessao = session_dir
        os.makedirs(pasta_sessao, exist_ok=True)
    else:
        pasta_sessao = criar_pasta_sessao("sessoes_contagem", "mobile")

    arquivo_contagem = os.path.join(pasta_sessao, "inventario_mobile.json")
    arquivo_precos = os.path.join(pasta_sessao, "produtos_precos.json")

    lock = Lock()
    contagem = Counter(_load_json(arquivo_contagem, {}))
    precos = _load_json(arquivo_precos, {})

    def persistir():
        _save_json(arquivo_contagem, dict(contagem))
        _save_json(arquivo_precos, precos)
        if PASTA_NUVEM:
            try:
                from cloud_sync import sincronizar_sessao_nuvem
                sincronizar_sessao_nuvem(pasta_sessao, PASTA_NUVEM)
            except Exception as exc:
                log("MOBILE_SYNC_NUVEM_ERRO", str(exc))

    @app.route("/")
    def index():
        return send_from_directory("mobile", "index.html")

    @app.get("/api/ping")
    def ping():
        return jsonify({"ok": True, "sessao": pasta_sessao})

    @app.get("/api/produto/<codigo_barras>")
    def consultar_produto(codigo_barras):
        codigo_barras = str(codigo_barras).strip()
        dados = mapeamento.get(codigo_barras)
        if not dados:
            return jsonify({
                "encontrado": False,
                "codigo_barras": codigo_barras,
                "quantidade": int(contagem.get(codigo_barras, 0)),
                "preco": precos.get(codigo_barras),
            })

        codigo_interno, nome, grupo = dados[0], dados[1], dados[2] if len(dados) > 2 else ""
        return jsonify({
            "encontrado": True,
            "codigo_barras": codigo_barras,
            "codigo_interno": codigo_interno,
            "nome": nome,
            "grupo": grupo,
            "quantidade": int(contagem.get(codigo_barras, 0)),
            "preco": precos.get(codigo_barras),
        })

    @app.post("/api/cadastrar")
    def cadastrar_produto():
        payload = request.get_json(silent=True) or {}
        cb = str(payload.get("codigo_barras", "")).strip()
        ci = str(payload.get("codigo_interno", "")).strip()
        nome = str(payload.get("nome", "")).strip()
        grupo = str(payload.get("grupo", "")).strip()
        preco = payload.get("preco")

        if not cb or not nome:
            return jsonify({"ok": False, "erro": "codigo_barras e nome sao obrigatorios"}), 400

        with lock:
            mapeamento[cb] = (ci, nome, grupo)
            if preco is not None and str(preco).strip() != "":
                try:
                    precos[cb] = float(preco)
                except Exception:
                    return jsonify({"ok": False, "erro": "preco invalido"}), 400

            salvar_mapeamento_custom(mapeamento)
            persistir()

        return jsonify({"ok": True, "codigo_barras": cb})

    @app.post("/api/contar")
    def contar_item():
        payload = request.get_json(silent=True) or {}
        cb = str(payload.get("codigo_barras", "")).strip()
        qtd = int(payload.get("quantidade", 1))

        if not cb:
            return jsonify({"ok": False, "erro": "codigo_barras obrigatorio"}), 400

        with lock:
            contagem[cb] += qtd
            if contagem[cb] < 0:
                contagem[cb] = 0
            persistir()

        return jsonify({"ok": True, "codigo_barras": cb, "quantidade": int(contagem[cb])})

    @app.post("/api/ajuste")
    def ajuste_item():
        payload = request.get_json(silent=True) or {}
        cb = str(payload.get("codigo_barras", "")).strip()
        delta = int(payload.get("delta", 0))

        if not cb:
            return jsonify({"ok": False, "erro": "codigo_barras obrigatorio"}), 400

        with lock:
            contagem[cb] += delta
            if contagem[cb] < 0:
                contagem[cb] = 0
            persistir()

        return jsonify({"ok": True, "codigo_barras": cb, "quantidade": int(contagem[cb])})

    @app.get("/api/inventario")
    def listar_inventario():
        rows = []
        for cb, qtd in sorted(contagem.items()):
            if qtd <= 0:
                continue
            dados = mapeamento.get(cb, ("", "NAO MAPEADO", ""))
            rows.append({
                "codigo_barras": cb,
                "codigo_interno": dados[0],
                "nome": dados[1],
                "grupo": dados[2] if len(dados) > 2 else "",
                "quantidade": int(qtd),
                "preco": precos.get(cb),
            })
        return jsonify({"ok": True, "itens": rows, "sessao": pasta_sessao})

    return app


def main():
    parser = argparse.ArgumentParser(description="Servidor mobile IKARUS")
    parser.add_argument("--excel", default="Produtos Box.xlsx", help="Arquivo Excel de produtos")
    parser.add_argument("--aba", default=None, help="Nome da aba do Excel")
    parser.add_argument("--host", default="0.0.0.0", help="Host de bind")
    parser.add_argument("--port", type=int, default=8000, help="Porta")
    parser.add_argument("--session-dir", default=None, help="Pasta da sessao")
    parser.add_argument("--https", action="store_true", help="Inicia com HTTPS (certificado de desenvolvimento)")
    args = parser.parse_args()

    app = create_mobile_app(args.excel, args.aba, args.session_dir)
    ssl_context = "adhoc" if args.https else None
    app.run(host=args.host, port=args.port, debug=False, ssl_context=ssl_context)


if __name__ == "__main__":
    main()
