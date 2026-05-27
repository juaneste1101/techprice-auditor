import sqlite3
import random
import os

def inicializar_db():
    if os.path.exists("database.db"):
        os.remove("database.db")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        categoria TEXT NOT NULL,
        tienda TEXT NOT NULL,
        precio_actual REAL NOT NULL,
        precio_anterior REAL NOT NULL,
        url TEXT NOT NULL
    )""")
    
    productos_unicos = set()
    catalogo = []
    
    print("Sintetizando 1000 componentes únicos comerciales...")
    
    marcas_gpu = ["ASUS", "MSI", "Gigabyte", "Zotac", "PNY", "Sapphire", "XFX"]
    chips_gpu = ["RTX 3060", "RTX 4060", "RTX 4060 Ti", "RTX 4070", "RTX 4070 Ti", "RTX 4080", "RTX 4090", "RX 7600", "RX 7700 XT", "RX 7800 XT", "RX 7900 XTX"]
    sufijos_gpu = ["OC Edition", "Gaming X", "Dual", "TUF Gaming", "ROG Strix", "Windforce", "Eagle", "Phantom"]
    
    marcas_ram = ["Corsair", "Kingston", "G.Skill", "Adata XPG", "TeamGroup"]
    lineas_ram = ["FURY Beast", "Vengeance LPX", "Vengeance RGB", "Trident Z5", "Spectrix D50"]
    caps_ram = ["16GB (2x8GB)", "32GB (2x16GB)", "64GB (2x32GB)"]
    vels_ram = ["3200MHz", "3600MHz", "5600MHz", "6000MHz"]
    
    marcas_ssd = ["Samsung", "WD Black", "Crucial", "Adata", "Kingston"]
    lineas_ssd = ["980 PRO", "SN850X", "P3 Plus", "Legend 700", "KC3000", "NV2"]
    caps_ssd = ["512GB", "1TB", "2TB", "4TB"]
    
    # BUCLE CORREGIDO: Límite matemático seguro
    while len(productos_unicos) < 1000:
        categoria = random.choice(["Tarjeta Gráfica", "Memoria RAM", "Disco SSD"])
        
        if categoria == "Tarjeta Gráfica":
            nombre = f"{random.choice(marcas_gpu)} {random.choice(sufijos_gpu)} {random.choice(chips_gpu)}"
        elif categoria == "Memoria RAM":
            nombre = f"{random.choice(marcas_ram)} {random.choice(lineas_ram)} {random.choice(caps_ram)} {random.choice(vels_ram)}"
        else:
            nombre = f"{random.choice(marcas_ssd)} {random.choice(lineas_ssd)} {random.choice(caps_ssd)} NVMe M.2"
            
        if nombre not in productos_unicos:
            productos_unicos.add(nombre)
            
            if categoria == "Tarjeta Gráfica":
                if "RTX 4090" in nombre: base = 11500000
                elif "RTX 4080" in nombre: base = 6100000
                elif "RTX 4070 Ti" in nombre: base = 4300000
                elif "RTX 4070" in nombre: base = 3200000
                elif "RTX 4060 Ti" in nombre: base = 2350000
                elif "RTX 4060" in nombre: base = 1850000
                elif "RTX 3060" in nombre: base = 1450000
                else: base = random.randint(1500000, 3000000)
                
            elif categoria == "Memoria RAM":
                if "16GB" in nombre: base = 420000
                elif "32GB" in nombre: base = 900000
                else: base = 1800000
                if "5600MHz" in nombre or "6000MHz" in nombre: base = int(base * 1.2)
                
            elif categoria == "Disco SSD":
                if "512GB" in nombre: base = 280000
                elif "1TB" in nombre: base = 480000
                elif "2TB" in nombre: base = 850000
                else: base = 1600000

            precio_final = int(base * random.uniform(0.95, 1.05))
            catalogo.append({"nombre": nombre, "cat": categoria, "precio": precio_final})

    procesadores_ref = [
        ("Intel Core i5-13400F", 1000000), ("Intel Core i5-13600K", 1500000),
        ("Intel Core i7-13700K", 2150000), ("Intel Core i9-13900K", 2950000),
        ("AMD Ryzen 5 5600X", 800000), ("AMD Ryzen 7 5800X3D", 1600000),
        ("AMD Ryzen 7 7800X3D", 2200000), ("AMD Ryzen 9 7950X3D", 3350000)
    ]
    for p_nom, p_prec in procesadores_ref:
        catalogo.append({"nombre": p_nom, "cat": "Procesador", "precio": p_prec})

    tiendas = ["Amazon", "Mercado Libre", "Tauret Computadores", "SpeedLogic", "Clones y Periféricos"]
    
    print(f"Cruzando ofertas para {len(catalogo)} productos...")
    
    for prod in catalogo:
        tiendas_producto = random.sample(tiendas, 3)
        for tienda in tiendas_producto:
            precio_mercado = prod["precio"] * random.uniform(0.94, 1.06)
            
            escenario = random.choices(["FALSO_DESCUENTO", "OFERTA_REAL", "ESTABLE"], weights=[0.70, 0.15, 0.15])[0]
            
            if escenario == "FALSO_DESCUENTO":
                precio_actual = precio_mercado 
                precio_anterior = precio_mercado * random.uniform(0.60, 0.85) 
            elif escenario == "OFERTA_REAL":
                precio_actual = precio_mercado * random.uniform(0.70, 0.90) 
                precio_anterior = precio_mercado
            else:
                precio_actual = precio_mercado
                precio_anterior = precio_mercado 
            
            url_busqueda = f"https://www.google.com/search?q=comprar+{prod['nombre'].replace(' ', '+')}+colombia"
            
            cursor.execute("""
                INSERT INTO productos (nombre, categoria, tienda, precio_actual, precio_anterior, url)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (prod["nombre"], prod["cat"], tienda, int(precio_actual), int(precio_anterior), url_busqueda))
            
    conn.commit()
    print("✅ ¡Data Warehouse finalizado al instante!")
    conn.close()

if __name__ == "__main__":
    inicializar_db()