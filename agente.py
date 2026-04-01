from openai import OpenAI
import pandas as pd
import re

# =========================
# 🤖 IDENTIDADE
# =========================

AGENTE_NOME = "Murilo Antonio da GFK"
client = OpenAI()

# =========================
# 📊 CARREGAR DADOS
# =========================

df = pd.read_csv("GFK.csv", encoding="latin1", sep=";", low_memory=False)

df.columns = df.columns.str.strip()
df["Units"] = pd.to_numeric(df["Units"], errors="coerce")
df["Average Price"] = pd.to_numeric(df["Average Price"], errors="coerce")

df = df[df["Units"] > 0]

# =========================
# 📅 ORDEM DOS MESES
# =========================

mes_ordem = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
]

df["Month"] = pd.Categorical(df["Month"], categories=mes_ordem, ordered=True)

# =========================
# 🔧 NORMALIZAÇÃO
# =========================

def limpar(texto):
    return re.sub(r"[^a-z0-9<> -]", "", texto.lower())

SINONIMOS = {
    "tamanho": "size",
    "tela": "screen",
    "marca": "brand",
    "modelo": "model",
    "mes": "month",
    "mês": "month",
    "ano": "year",
    "preco": "price",
    "preço": "price"
}

def normalizar_pergunta(pergunta):
    p = limpar(pergunta)
    for pt, en in SINONIMOS.items():
        p = p.replace(pt, en)
    return p

# =========================
# 🔍 DETECTAR DIMENSÕES
# =========================

def detectar_dimensoes(pergunta):

    pergunta_norm = normalizar_pergunta(pergunta)
    palavras = pergunta_norm.split()

    dimensoes = []

    for col in df.columns:

        col_norm = limpar(col)

        if len(col_norm) <= 2:
            continue

        col_palavras = col_norm.split()

        score = sum(1 for p in col_palavras if p in palavras)

        if score > 0:
            dimensoes.append((col, score))

    dimensoes = sorted(dimensoes, key=lambda x: x[1], reverse=True)

    return [d[0] for d in dimensoes[:3]]

# =========================
# 🔧 FILTROS
# =========================

def aplicar_filtros(df, pergunta):

    p = pergunta.lower()

    for y in range(2020, 2030):
        if str(y) in p:
            df = df[df["Year"] == y]

    for m in df["Brand"].dropna().unique():
        if m.lower() in p:
            df = df[df["Brand"] == m]

    return df

# =========================
# 💰 PRICE TIER DINÂMICO + ORDENADO
# =========================

def extrair_tiers(pergunta):
    return re.findall(r"(<\d+|\d+-\d+|>\d+)", pergunta.replace(" ", ""))

def criar_price_tier(df, tiers=None):

    if not tiers:
        bins = [0,1000,2000,3000,4000,5000,999999]
        labels = ["<1000","1000-2000","2000-3000","3000-4000","4000-5000",">5000"]

    else:
        limites = []

        for t in tiers:
            if "-" in t:
                a,b = t.split("-")
                limites.extend([float(a), float(b)])
            elif "<" in t:
                limites.extend([0, float(t[1:])])
            elif ">" in t:
                limites.extend([float(t[1:]), 999999])

        bins = sorted(set(limites))
        labels = tiers

    df["Price Tier"] = pd.cut(
        df["Average Price"],
        bins=bins,
        labels=labels,
        include_lowest=True
    )

    df["Price Tier"] = pd.Categorical(
        df["Price Tier"],
        categories=labels,
        ordered=True
    )

    return df

# =========================
# 📊 EXECUTOR
# =========================

def executar(pergunta):

    p = normalizar_pergunta(pergunta)

    df_filtrado = aplicar_filtros(df, pergunta)

    dimensoes = detectar_dimensoes(pergunta)

    # =========================
    # 💰 PRICE TIER (FIX PRINCIPAL)
    # =========================

    if "price tier" in p or "faixa" in p:

        tiers = extrair_tiers(pergunta)
        df_filtrado = criar_price_tier(df_filtrado, tiers)

        # 🔥 NÃO SOBRESCREVE MAIS
        dimensoes = ["Price Tier"] + [d for d in dimensoes if d != "Price Tier"]

    # =========================
    # 💰 PREÇO MÉDIO
    # =========================

    if "average price" in p or "preco medio" in p:

        if dimensoes:
            resultado = (
                df_filtrado
                .groupby(dimensoes, observed=True)["Average Price"]
                .mean()
                .reset_index()
            )
            return resultado.to_string(index=False)

    # =========================
    # 📊 VENDAS
    # =========================

    if "venda" in p or "sales" in p:

        if dimensoes:

            if "Month" in dimensoes and "Month #" in dimensoes:
                dimensoes.remove("Month #")

            resultado = (
                df_filtrado
                .groupby(dimensoes, observed=True)["Units"]
                .sum()
                .reset_index()
            )

            # 🔥 ORDENAÇÃO MULTI-DIMENSÃO
            if "Price Tier" in dimensoes and "Month" in dimensoes:
                resultado = resultado.sort_values(["Month","Price Tier"])

            elif "Price Tier" in dimensoes:
                resultado = resultado.sort_values("Price Tier")

            elif "Year" in dimensoes and "Month" in dimensoes:
                resultado = resultado.sort_values(["Year","Month"])

            elif "Month" in dimensoes:
                resultado = resultado.sort_values("Month")

            elif "Year" in dimensoes:
                resultado = resultado.sort_values("Year")

            else:
                resultado = resultado.sort_values("Units", ascending=False)

            return resultado.to_string(index=False)

        return (
            df_filtrado
            .groupby("Month", observed=True)["Units"]
            .sum()
            .reset_index()
            .sort_values("Month")
            .to_string(index=False)
        )

    return None

# =========================
# 🤖 FALLBACK IA
# =========================

def fallback(pergunta):

    try:
        r = client.responses.create(
            model="gpt-4.1-mini",
            input=pergunta
        )
        return r.output_text
    except:
        return "Não consegui interpretar."

# =========================
# 🤖 AGENTE
# =========================

def responder(pergunta):

    resultado = executar(pergunta)

    if resultado:
        return f"{AGENTE_NOME}:\n\n{resultado}"

    return f"{AGENTE_NOME}:\n\n{fallback(pergunta)}"

# =========================
# 🔁 LOOP
# =========================

print(f"🤖 {AGENTE_NOME} iniciado (multi-dimensão + price tier por mês).")
print("Digite 'sair' para encerrar.\n")

while True:
    pergunta = input("Pergunta: ")

    if pergunta.lower() == "sair":
        break

    print("\nResposta:")
    print(responder(pergunta))
    print("\n" + "-"*60 + "\n")