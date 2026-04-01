import pandas as pd

# 1. carregar dados
df = pd.read_csv(
    "GFK.csv",
    encoding="latin1",
    sep=";",
    low_memory=False
)

# 2. limpar colunas
df.columns = df.columns.str.strip()

# 3. garantir Units numérico
df["Units"] = pd.to_numeric(df["Units"], errors="coerce")

# 4. ordenar meses corretamente
mes_ordem = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"

]

df["Month"] = pd.Categorical(df["Month"], categories=mes_ordem, ordered=True)

# =========================
# 📊 MARKET SHARE
# =========================

# total por mês/ano
total_mes = df.groupby(["Year", "Month"], observed=True)["Units"].sum().reset_index()
total_mes.rename(columns={"Units": "Total Units"}, inplace=True)

# vendas por marca
brand_mes = df.groupby(["Year", "Month", "Brand"], observed=True)["Units"].sum().reset_index()

# juntar
df_share = brand_mes.merge(total_mes, on=["Year", "Month"])

# calcular share
df_share["Market Share"] = df_share["Units"] / df_share["Total Units"]
df_share["Market Share %"] = df_share["Market Share"] * 100

# =========================
# 🔍 OUTPUT
# =========================

print("\nMARKET SHARE (TOP 10):")
print(
    df_share
    .sort_values(["Year", "Month", "Market Share"], ascending=[True, True, False])
    .groupby(["Year", "Month"])
    .head(5)
)
print("\nLÍDER POR MÊS:")

lider = (
    df_share
    .sort_values(["Year", "Month", "Market Share"], ascending=[True, True, False])
    .groupby(["Year", "Month"])
    .first()
)

print(lider[["Brand", "Market Share %"]])