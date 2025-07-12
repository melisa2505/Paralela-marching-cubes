import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv("matrix_analysis.csv")

# Gráfico 1: Tiempo vs Threads por resolución
plt.figure(figsize=(10,6))
for res in sorted(df['Resolution'].unique(), key=lambda x: float(x)):
    subset = df[df['Resolution'] == res].groupby('Threads')['Time_seconds'].mean()
    plt.plot(subset.index, subset.values, marker='o', label=f"res={res}")
plt.xlabel("Threads")
plt.ylabel("Tiempo promedio (s)")
plt.title("Tiempo de ejecución vs Threads por resolución")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# Gráfico 2: Speedup vs Threads por resolución
plt.figure(figsize=(10,6))
for res in sorted(df['Resolution'].unique(), key=lambda x: float(x)):
    subset = df[df['Resolution'] == res].groupby('Threads')['Speedup_vs_1thread'].mean()
    plt.plot(subset.index, subset.values, marker='o', label=f"res={res}")
plt.xlabel("Threads")
plt.ylabel("Speedup")
plt.title("Speedup vs Threads por resolución")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# Gráfico 3: Eficiencia vs Threads por resolución
plt.figure(figsize=(10,6))
for res in sorted(df['Resolution'].unique(), key=lambda x: float(x)):
    subset = df[df['Resolution'] == res].groupby('Threads')['Efficiency'].mean()
    plt.plot(subset.index, subset.values, marker='o', label=f"res={res}")
plt.xlabel("Threads")
plt.ylabel("Eficiencia")
plt.title("Eficiencia vs Threads por resolución")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
