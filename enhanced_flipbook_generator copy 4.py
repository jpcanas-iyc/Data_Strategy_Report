import pandas as pd
from sqlalchemy import create_engine, text
import logging
import random
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------
# 1. Conectar a la BD
# -------------------------
def conectar_db():
    connection_string = (
        r'mssql+pyodbc:///?odbc_connect='
        r'Driver={SQL Server};'
        r'Server=PSR-S670-N\BIGDATA;'
        r'Database=DWH_INCOLMOTOS;'
        r'Trusted_Connection=yes'
    )
    engine = create_engine(connection_string)
    return engine

# -------------------------
# 2. Obtener los datos
# -------------------------
def obtener_tareas(engine):
    query = """

    SELECT 
        T.Tarea_Project_Key,
        T.Project_Project_Key,
        T.Jefatura_Project_Key,
        T.Codigo_Esquema_Tarea,
        T.Codigo_Tarea,
        T.Nombre_Tarea_Project,
        T.Descripcion_Tarea_Project,
        T.Estado_Tarea_Project_key,
        T.Objs_Estrat_Area_Project_Key,
        T.Objs_Div_TI_Project_Key,
        T.Gcia_Project_Key,
        T.Categoria_YMC_key,
        T.Codigo_MTP_key,
        T.Porcentaje_Ejecucion,
        T.Deposito_Project_Key,
        T.Fecha_Inicio,
        T.Fecha_Fin,
        T.Fecha_Estimada_Entrega,
        T.Notas_IA_Project,
        D.Nombre_Deposito_Project,
        G.Nom_Gcia_Project,
        E.Nom_Estado_Tarea_Project
    FROM [DWH_INCOLMOTOS].[ti].[Dim_Tareas_Project] T
    LEFT JOIN [DWH_INCOLMOTOS].[ti].[Dim_Depositos_Project] D
        ON T.Deposito_Project_Key = D.Deposito_Project_Key
    LEFT JOIN [DWH_INCOLMOTOS].[ti].[Dim_Gcias_Involucradas_Project] G
        ON T.Gcia_Project_Key = G.Gcia_Project_Key
    LEFT JOIN [DWH_INCOLMOTOS].[ti].[Dim_Estado_Tareas_Project] E
        ON T.Estado_Tarea_Project_key = E.Estado_Tarea_Project_key
    WHERE T.Jefatura_Project_Key = 2
    AND T.Tarea_Project_Key NOT IN (41, 33)
    AND T.Estado_Tarea_Project_key IN (2,4)

    """
    df = pd.read_sql(query, engine)
    return df


def Promedio_Encuestas(engine):
    query = """
        SELECT 
            COUNT(*) AS Total_Encuestas,
            ROUND(AVG(Calidad_Entrega),2)        AS Promedio_Calidad,
            ROUND(AVG(Tiempo_Entrega),2)         AS Promedio_Tiempo,
            ROUND(AVG(Acompañamiento_Entrega),2) AS Promedio_Acompanamiento,
            ROUND(AVG(Experiencia_Entrega),2)    AS Promedio_Experiencia
        FROM [DWH_INCOLMOTOS].[admn].[Fact_Encuesta_Proyectos];
    """
    promedio = pd.read_sql(query, engine)
    return promedio

def Total_Planeados_yAnterior(engine):
    query = """
        SELECT COUNT(Tarea_Project_Key) AS total
        FROM [DWH_INCOLMOTOS].[ti].[Dim_Tareas_Project]
        WHERE Tarea_Project_Key NOT IN (41, 33)
        AND Estado_Tarea_Project_key IN (2,4)
    """
    df = pd.read_sql(query, engine)
    return int(df["total"][0] or 0)




def obtener_cumplimiento_proyectos(engine):

    query = """
        SELECT 
            CAST(
                COUNT(CASE WHEN Estado_Tarea_Project_key = 2 
                           AND Deposito_Project_Key = 2 THEN 1 END) * 100.0
                /
                NULLIF(COUNT(CASE WHEN Estado_Tarea_Project_key = 2 THEN 1 END), 0)
            AS DECIMAL(5,2)) AS planeados,

            CAST(
                COUNT(CASE WHEN Estado_Tarea_Project_key = 3 
                           AND Deposito_Project_Key = 2 THEN 1 END) * 100.0
                /
                NULLIF(COUNT(CASE WHEN Estado_Tarea_Project_key = 3 THEN 1 END), 0)
            AS DECIMAL(5,2)) AS nuevos,

            CAST(
                COUNT(CASE WHEN Estado_Tarea_Project_key = 4 
                           AND Deposito_Project_Key = 2 THEN 1 END) * 100.0
                /
                NULLIF(COUNT(CASE WHEN Estado_Tarea_Project_key = 4 THEN 1 END), 0)
            AS DECIMAL(5,2)) AS plan_anterior

        FROM [DWH_INCOLMOTOS].[ti].[Dim_Tareas_Project]
        WHERE Tarea_Project_Key NOT IN (41, 33)
    """

    df = pd.read_sql(query, engine)

    return {
        "planeados": float(df["planeados"][0] or 0),
        "nuevos": float(df["nuevos"][0] or 0),
        "plan_anterior": float(df["plan_anterior"][0] or 0),
    }





def obtener_resumen_ejecutivo(engine):
    query = """
        SELECT 
            -- Totales individuales
            COUNT(CASE WHEN Estado_Tarea_Project_key = 2 THEN 1 END) AS total_planeados,
            COUNT(CASE WHEN Estado_Tarea_Project_key = 4 THEN 1 END) AS total_plan_anterior,

            -- Totales combinados
            COUNT(CASE WHEN Estado_Tarea_Project_key IN (2,4) THEN 1 END) AS total_plan,

            COUNT(CASE WHEN Estado_Tarea_Project_key IN (2,4)
                       AND Deposito_Project_Key = 2 THEN 1 END) AS ejecutados_plan,

            COUNT(CASE WHEN Estado_Tarea_Project_key = 3 THEN 1 END) AS total_nuevos,

            COUNT(CASE WHEN Estado_Tarea_Project_key = 3
                       AND Deposito_Project_Key = 2 THEN 1 END) AS ejecutados_nuevos

        FROM [DWH_INCOLMOTOS].[ti].[Dim_Tareas_Project]
        WHERE Tarea_Project_Key NOT IN (41, 33)
    """

    df = pd.read_sql(query, engine)

    total_planeados = int(df["total_planeados"][0] or 0)
    total_plan_anterior = int(df["total_plan_anterior"][0] or 0)

    total_plan = int(df["total_plan"][0] or 0)
    ejecutados_plan = int(df["ejecutados_plan"][0] or 0)

    total_nuevos = int(df["total_nuevos"][0] or 0)
    ejecutados_nuevos = int(df["ejecutados_nuevos"][0] or 0)

    total_general = total_plan + total_nuevos

    porcentaje_avance = round(
        (ejecutados_plan / total_plan * 100) if total_plan > 0 else 0, 1
    )

    incremento = round(
        ((total_general - total_plan) / total_plan * 100) if total_plan > 0 else 0,
        1
    )

    return {
        "total_planeados": total_planeados,
        "total_plan_anterior": total_plan_anterior,
        "total_plan": total_plan,
        "ejecutados_plan": ejecutados_plan,
        "porcentaje_avance": porcentaje_avance,
        "total_nuevos": total_nuevos,
        "ejecutados_nuevos": ejecutados_nuevos,
        "total_general": total_general,
        "incremento": incremento
    }


# -------------------------
# 3. Obtener imágenes aleatorias
# -------------------------
def obtener_imagenes_aleatorias(carpeta_img="img", cantidad=None):
    """
    Obtiene lista de imágenes y videos de la carpeta especificada
    """
    extensiones = [
        '.jpg', '.jpeg', '.png', '.gif', '.webp',
        '.mp4', '.webm', '.ogg'
    ]

    imagenes = []

    if os.path.exists(carpeta_img):
        for archivo in os.listdir(carpeta_img):
            if any(archivo.lower().endswith(ext) for ext in extensiones):
                imagenes.append(f"../{carpeta_img}/{archivo}")

    if not imagenes:
        logger.warning(f"No se encontraron archivos multimedia en {carpeta_img}")
        return []

    if cantidad and len(imagenes) > cantidad:
        return random.sample(imagenes, cantidad)

    return imagenes


# -------------------------
# 4. Calcular estadísticas
# -------------------------
def generar_estadisticas(df):
    total_tareas = len(df)
    
    # Agrupaciones
    por_deposito = df.groupby("Nombre_Deposito_Project").size().to_dict()
    por_gerencia = df.groupby("Nom_Gcia_Project").size().to_dict()
    por_estado = df.groupby("Nom_Estado_Tarea_Project").size().to_dict()
    
    estadisticas = {
        "total_tareas": total_tareas,
        "por_deposito": por_deposito,
        "por_gerencia": por_gerencia,
        "por_estado": por_estado,
    }
    return estadisticas

# -------------------------
# 5. Generadores de layouts
# -------------------------

def layout_left_text(row, img_url):
    """Layout con texto a la izquierda e imagen a la derecha"""
    return f"""
    <div class="double layout-left-text">
        <div class="text-column">
            <div class="text-content">
                <div class="accent-line"></div>
                <div class="task-code">{row['Codigo_Tarea']}</div>
                <h2>{row['Nombre_Tarea_Project']}</h2>
                <div class="task-info">
                    <div class="task-label">Depósito</div>
                    <div class="task-value">{row['Nombre_Deposito_Project']}</div>
                </div>
                <div class="task-info">
                    <div class="task-label">Gerencia</div>
                    <div class="task-value">{row['Nom_Gcia_Project']}</div>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {row['Porcentaje_Ejecucion']*100}%"></div>
                </div>
                <div class="percentage-badge">{row['Porcentaje_Ejecucion']*100:.0f}%</div>
                <div class="task-info">
                    <div class="date-display">Inicio: {row['Fecha_Inicio']}</div>
                    <div class="date-display">Fin: {row['Fecha_Fin']}</div>
                </div>
            </div>
        </div>
        <div class="image-column">
            <img src="{img_url}" alt="Background">
        </div>
    </div>
    """

def layout_right_text(row, img_url):
    """Layout con texto a la derecha e imagen a la izquierda"""
    return f"""
    <div class="double layout-right-text">
        <div class="text-column">
            <div class="text-content">
                <h2>{row['Nombre_Tarea_Project']}</h2>
                <div class="divider"></div>
                <div class="task-label">Código: {row['Codigo_Tarea']}</div>
                <div class="task-info">
                    <strong>Estado:</strong> {row['Nom_Estado_Tarea_Project']}
                </div>
                <div class="task-info">
                    <strong>Notas:</strong><br>{str(row['Notas_IA_Project'] or '')[:100]}
                </div>
                <div class="task-info">
                    <strong>Progreso:</strong> {row['Porcentaje_Ejecucion']*100:.0f}%
                </div>
                <div class="task-info">
                    <div class="date-display">Entrega: {row['Fecha_Estimada_Entrega']}</div>
                </div>
            </div>
        </div>
        <div class="image-column">
            <img src="{img_url}" alt="Background">
        </div>
    </div>
    """

def layout_diagonal(row, img_url):
    """Layout con división diagonal"""
    return f"""
    <div class="double layout-diagonal">
        <div class="diagonal-bg"></div>
        <div class="content-wrapper">
            <div class="text-section">
                <div class="task-code" style="color: var(--accent-red);">{row['Codigo_Tarea']}</div>
                <h2>{row['Nombre_Tarea_Project']}</h2>
                <div class="task-info">
                    <strong>Depósito:</strong> {row['Nombre_Deposito_Project']}
                </div>
                <div class="task-info">
                    <strong>Gerencia:</strong> {row['Nom_Gcia_Project']}
                </div>
                <div class="percentage-badge">{row['Porcentaje_Ejecucion']*100:.0f}% Completado</div>
            </div>
            <div class="image-section">
                <img src="{img_url}" alt="Background">
            </div>
        </div>
    </div>
    """

def layout_center_margins(row, img_url):
    """Layout con márgenes laterales y contenido central"""
    return f"""
    <div class="double layout-center-margins">
        <div class="left-margin">
            <div class="margin-text">{row['Codigo_Tarea']}</div>
        </div>
        <div class="center-content">
            <div class="image-container">
                <img src="{img_url}" alt="Background">
                <div class="text-overlay">
                    <h2>{row['Nombre_Tarea_Project']}</h2>
                    <div class="task-info">
                        <strong>{row['Nom_Estado_Tarea_Project']}</strong> - {row['Porcentaje_Ejecucion']*100:.0f}%
                    </div>
                    <div class="task-info">
                        {str(row['Notas_IA_Project'] or '')[:100]}...
                    </div>
                </div>
            </div>
        </div>
        <div class="right-margin">
            <div class="margin-text">PROYECTO</div>
        </div>
    </div>
    """

def layout_full_overlay(row, img_url):
    """Layout con imagen de fondo completa y overlay de texto"""
    return f"""
    <div class="double layout-full-overlay">
        <div class="background-image">
            <img src="{img_url}" alt="Background">
        </div>
        <div class="gradient-overlay"></div>
        <div class="content-box">
            <h2>
                {row['Nombre_Tarea_Project'].split()[0]}
                <span class="red-accent">{' '.join(row['Nombre_Tarea_Project'].split()[1:])}</span>
            </h2>
            <div class="task-info" style="font-size: 16px; margin-bottom: 15px;">
                <strong>Código:</strong> {row['Codigo_Tarea']}
            </div>
            <div class="task-info">
                <strong>Depósito:</strong> {row['Nombre_Deposito_Project']}
            </div>
            <div class="task-info">
                <strong>Estado:</strong> {row['Nom_Estado_Tarea_Project']}
            </div>
            <div class="percentage-badge" style="margin-top: 20px; font-size: 18px;">
                {row['Porcentaje_Ejecucion']*100:.0f}%
            </div>
        </div>
    </div>
    """

def layout_grid(row, img_url):
    """Layout con grid asimétrico"""
    return f"""
    <div class="double layout-grid">
        <div class="text-area">
            <h2>{row['Nombre_Tarea_Project']}</h2>
            <div class="task-info">
                <div class="task-label">Código</div>
                <div class="task-value">{row['Codigo_Tarea']}</div>
            </div>
            <div class="task-info">
                <div class="task-label">Notas</div>
                <div class="task-value">{str(row['Notas_IA_Project'] or '')[:100]}..</div>
            </div>
            <div class="highlight-box">
                <strong>Progreso:</strong> {row['Porcentaje_Ejecucion']*100:.0f}%<br>
                <strong>Estado:</strong> {row['Nom_Estado_Tarea_Project']}
            </div>
        </div>
        <div class="image-area-1">
            <img src="{img_url}" alt="Background">
        </div>
        <div class="image-area-2">
            <div>
                <div class="task-label">Depósito</div>
                <div style="font-size: 18px; font-weight: 700; margin-bottom: 10px;">
                    {row['Nombre_Deposito_Project']}
                </div>
                <div class="task-label">Gerencia</div>
                <div style="font-size: 16px;">
                    {row['Nom_Gcia_Project']}
                </div>
            </div>
        </div>
    </div>
    """



def layout_descripcion_proyecto(row):
    descripcion = row["Descripcion_Tarea_Project"] or ""

    if not descripcion.strip():
        descripcion = "Sin descripción disponible."

    secciones = [
        "Situación actual",
        "Problema clave",
        "Objetivo del proyecto",
        "Alcance de la solución",
        "Impacto esperado / ROI"
    ]

    # Insertar separadores
    for s in secciones:
        descripcion = descripcion.replace(s, f"|||{s}")

    bloques = [b.strip() for b in descripcion.split("|||") if b.strip()]

    # Ignorar Área si existiera
    bloques_filtrados = []
    for bloque in bloques:
        if bloque.lower().startswith("área"):
            continue
        bloques_filtrados.append(bloque)

    # Agrupar de 2 en 2
    grupos = [bloques_filtrados[i:i+2] for i in range(0, len(bloques_filtrados), 2)]

    bloques_html = ""

    for grupo in grupos:
        bloques_html += '<div class="desc-group">'
        
        for bloque in grupo:
            partes = bloque.split(":", 1)
            if len(partes) == 2:
                titulo = partes[0].strip()
                contenido = partes[1].strip()
            else:
                titulo = ""
                contenido = bloque.strip()

            bloques_html += f"""
                <div class="desc-section">
                    <div class="desc-title">{titulo}</div>
                    <div class="desc-text">{contenido}</div>
                </div>
            """

        bloques_html += "</div>"

    return f"""
    <div class="double layout-descripcion">
        <div class="descripcion-container">

            <div class="descripcion-header">
                <h2>{row['Nombre_Tarea_Project']}</h2>
                <div class="descripcion-sub">
                    {row['Nom_Estado_Tarea_Project']} · {row['Nombre_Deposito_Project']}
                </div>
            </div>

            <div class="descripcion-body">
                {bloques_html}
            </div>

        </div>
    </div>
    """




# -------------------------
# 6. Generar flipbook HTML
# -------------------------

def generar_flipbook(df, output="output/flipbook.html"):
    estadisticas = generar_estadisticas(df)
    resumen = obtener_resumen_ejecutivo(engine)

    paginas = []
    
    # Obtener todas las imágenes disponibles
    imagenes = obtener_imagenes_aleatorias()
    if not imagenes:
        logger.warning("No hay imágenes disponibles. Se usará un placeholder.")
        imagenes = ["../img/placeholder.jpg"] * len(df)
    
    # Definir layouts disponibles organizados por color de fondo
    layouts_azules = [
        layout_left_text,      # Azul
        layout_full_overlay,   # Azul
    ]
    
    layouts_oscuros = [
        layout_right_text,     # Gris oscuro
        layout_center_margins, # Negro
        layout_grid,           # Negro
    ]
    
    layouts_claros = [
        layout_diagonal,       # Blanco/claro
    ]
    
    # --- Portada CORREGIDA ---
    img_portada = "../img/70aniversarioYamaha1.jpg"
    portada = f"""
    <div class="double portada-custom">
        <div class="bg-image">
            <img src="{img_portada}" alt="Portada">
        </div>
        <div class="overlay-content">
            <div class="title-container">
               <p>
                <span style="font-size:35px;">Data Strategy Report</span><br>
                <span style="font-style:italic; font-size:12px; color:#4a4a4a;">
                    Digital Magazine Vol.1 – 2026
                </span>

                </p>

                <div class="accent-bar"></div>
            </div>
            <div class="bottom-container">
                <div class="subtitle">Infraestructura De Datos</div>
                
            </div>
        </div>
    </div>
    """
    paginas.append(portada)
    
    # --- Página con foto IMG_0283.jpeg DESPUÉS DE LA PORTADA ---



    df = obtener_tareas(engine)

    # Limpiar datos
    df = df.dropna(subset=["Nombre_Tarea_Project"]).drop_duplicates(subset=["Nombre_Tarea_Project"])

    # Construir los <li>
    lista_items = ""

    for _, row in df.iterrows():
        nombre = str(row["Nombre_Tarea_Project"]).strip()

        try:
            estado = int(row["Estado_Tarea_Project_key"])
        except:
            estado = None

        try:
            deposito = int(row["Deposito_Project_Key"])
        except:
            deposito = None    

        anchor = nombre.lower().replace(" ", "_").replace("/", "_")

        if estado == 3:
            nombre_mostrar = f"""
                {nombre}
                <span style="
                    color:#0A2D82;
                    font-style: italic;
                    text-shadow: 1px 1px 4px rgba(30,144,255,0.7);
                    margin-left:6px;
                ">
                    Nuevo
                </span>
            """
        elif estado == 4:
            nombre_mostrar = f"""
                {nombre}
                <span style="
                    color:#616365;
                    font-style: italic;
                    text-shadow: 1px 1px 4px rgba(30,144,255,0.7);
                    margin-left:6px;
                ">
                    Plan Anterior
                </span>
                
            """    
        else:
            nombre_mostrar = nombre




        if deposito == 2:
            nombre_mostrar = f"""
                {nombre_mostrar}
                <span style="
                    color:#0A2D82;
                    font-style: italic;
                    text-shadow: 1px 1px 4px rgba(30,144,255,0.7);
                    margin-left:6px;
                ">
                    ✓
                </span>
            """
        else:
            nombre_mostrar = nombre_mostrar




        lista_items += f"""
            <li>
                <a href="#{anchor}" style="color:#808080; text-decoration:none;">
                    {nombre_mostrar}
                </a>
            </li>
        """



    pagina_imagen = f"""
    <div class="double full-image-page">
        <img src="https://jpcanas-iyc.github.io/Data_Strategy_Report/img/IMG_0283.JPEG" alt="IMG_0283">
    </div>
    """


    paginas.append(pagina_imagen)
    

        
            
  
    df = obtener_tareas(engine)

    # =========================
    # LIMPIAR DATOS
    # =========================
    df = df.dropna(subset=["Nombre_Tarea_Project"]) \
        .drop_duplicates(subset=["Nombre_Tarea_Project"])

    lista_nuevo = ""
    lista_finalizado = ""
    lista_en_curso = ""
    lista_otros = ""

    for _, row in df.iterrows():
        nombre = str(row["Nombre_Tarea_Project"]).strip()

        try:
            estado = int(row["Estado_Tarea_Project_key"])
        except:
            estado = None

        try:
            deposito = int(row["Deposito_Project_Key"])
        except:
            deposito = None    

        anchor = nombre.lower().replace(" ", "_").replace("/", "_")

        # -----------------------------
        # ETIQUETA VISUAL DE TEXTO
        # -----------------------------
        if estado == 3:
            nombre_mostrar = f"""
                {nombre}

            """
        elif estado == 4:
            nombre_mostrar = f"""
                {nombre}

            """
        else:
            nombre_mostrar = nombre

        item_html = f"""
            <li>
                <a href="#{anchor}" style="color:#808080; text-decoration:none;">
                    {nombre_mostrar}
                </a>
            </li>
        """

        # =====================================================
        # PRIORIDAD DE AGRUPACIÓN (NO REPETIR)
        # =====================================================

        # 1️ NUEVO (Estado = 2)
        if estado == 3:
            lista_nuevo += item_html

        # 2️ FINALIZADO
        elif deposito == 2:
            lista_finalizado += item_html

        # 3️ EN CURSO
        elif deposito == 3:
            lista_en_curso += item_html




    # =========================
    # HTML COMPLETO
    # =========================
    estadistica_html = f"""
    <div class="double stats-premiumDerecha" style="position:relative; overflow:hidden;">    

        <div class="stats-container" style="position:relative; z-index:2;">
            
            <div class="stats-hero-section">
                <div class="stats-kicker">Plan De Trabajo 2026<br></div>
                <span style="font-size:28px;">Tabla De Contenido</span>
                <div class="hero-display"></div>
            </div>
            
            <div class="stats-content-grid">
                <!-- FINALIZADO -->     
                <div class="stats-card" style="margin-bottom:20px;">
                     <span style="
                        display:block;
                        width:100%;
                        padding:6px 14px;
                        border-radius:5px;
                        background-color:rgba(46,125,50,0.06);
                        color:#666666;
                        font-size:14px;
                        font-weight:600;
                        letter-spacing:0.5px;
                        text-align:left;
                    ">
                        Finalizado
                    </span>
                    <ol style="font-size:10px; line-height:2.4;">
                        {lista_finalizado}
                    </ol>
                </div>

                <!-- EN CURSO -->
                <div class="stats-card" style="margin-bottom:20px;">
                        <span style="
                            display:block;
                            width:100%;
                            padding:6px 14px;
                            border-radius:5px;
                            background-color:rgba(212,160,23,0.05);
                            color:#666666;
                            font-size:14px;
                            font-weight:600;
                            letter-spacing:0.5px;
                            text-align:left;
                        ">
                            En Curso
                        </span>
                    <ol style="font-size:10px; line-height:2.4;">
                        {lista_en_curso}
                    </ol>
                </div>

                <!-- NUEVO -->
                <div class="stats-card" style="margin-bottom:20px;">
                        <span style="
                            display:block;
                            width:100%;
                            padding:6px 5px;
                            border-radius:20px;
                            background-color:rgba(10,45,130,0.05);
                            color:#666666;
                            font-size:14px;
                            font-weight:600;
                            letter-spacing:0.5px;
                            text-align:left;
                        ">
                            Nuevo
                        </span>

                    <ol style="font-size:10px; line-height:2.4;">
                        {lista_nuevo}
                    </ol>
                </div>


            </div>

        </div>
    </div>
    """

    paginas.append(estadistica_html)




    df_prom = Promedio_Encuestas(engine)

    total_encuestas = int(df_prom["Total_Encuestas"][0])
    prom_calidad = float(df_prom["Promedio_Calidad"][0])
    prom_tiempo = float(df_prom["Promedio_Tiempo"][0])
    prom_acomp = float(df_prom["Promedio_Acompanamiento"][0])
    prom_exp = float(df_prom["Promedio_Experiencia"][0])

    indice_global = round(
        (prom_calidad + prom_tiempo + prom_acomp + prom_exp) / 4, 2
    )

    estrellas_llenas = int(round(indice_global))
    estrellas_html = ""

    for i in range(5):
        if i < estrellas_llenas:
            estrellas_html += '<span class="star filled">★</span>'
        else:
            estrellas_html += '<span class="star empty">☆</span>'



    cumplimientos = obtener_cumplimiento_proyectos(engine)

    planeados = round(cumplimientos["planeados"], 2)
    nuevos = round(cumplimientos["nuevos"], 2)
    plan_anterior = round(cumplimientos["plan_anterior"], 2)
    total_proyectos = Total_Planeados_yAnterior(engine)



                        
    pagina_kpi = f"""
    <div class="double kpi-page">
        <div class="kpi-container">

            <div class="stats-hero-section">
                <div class="stats-kicker">Plan De Trabajo 2026<br></div>
                <span style="font-size:28px;">Indicadores</span>
                <div class="hero-display"></div>
            </div>

            <div class="kpi-top-graphs">

            <div>
                <span style="
                    display:inline-block;
                    padding:4px 12px;
                    border-radius:5px;
                    background-color:rgba(198,40,40,0.08);
                    color:#C62828;
                    font-size:12px;
                    font-weight:600;
                    letter-spacing:0.5px;
                    text-align:left;
                    margin-bottom:10px;">
                    Cumplimiento Proyectos
                </span>

                <div class="kpi-bar-chart">

                    <div class="kpi-bar-item">
                        <div class="kpi-bar-label">Planeados</div>
                        <div class="kpi-bar">
                            <div class="kpi-bar-fill" data-value="{planeados}"></div>
                        </div>
                        <div class="kpi-bar-value">{planeados}%</div>
                    </div>

                    <div class="kpi-bar-item">
                        <div class="kpi-bar-label">Nuevos</div>
                        <div class="kpi-bar">
                            <div class="kpi-bar-fill" data-value="{nuevos}"></div>
                        </div>
                        <div class="kpi-bar-value">{nuevos}%</div>
                    </div>

                    <div class="kpi-bar-item">
                        <div class="kpi-bar-label">Plan Anterior</div>
                        <div class="kpi-bar">
                            <div class="kpi-bar-fill" data-value="{plan_anterior}"></div>
                        </div>
                        <div class="kpi-bar-value">{plan_anterior}%</div>
                    </div>

                </div>
            </div>

            <!-- Descripción dinámica -->
            <div style="font-size:10px; line-height:2.4; margin-top:15px;">

                <span style="color:#C62828; font-weight:700;">
                    {resumen["total_plan"]} proyectos
                </span> 
                forman parte del plan anual estratégico definido para el 2026 
                (
                <span style="color:#C62828; font-weight:700;">
                    {resumen["total_planeados"]} Planeados
                </span> 
                y 
                <span style="color:#C62828; font-weight:700;">
                    {resumen["total_plan_anterior"]} Plan Anterior
                </span>).

                De estos, se han ejecutado 
                <span style="color:#C62828; font-weight:700;">
                    {resumen["ejecutados_plan"]} proyectos
                </span>, 
                lo que representa un avance del 
                <span style="color:#C62828; font-weight:700;">
                    {resumen["porcentaje_avance"]}%
                </span> 
                frente a lo planificado.


                Durante el transcurso del año han ingresado 
                <span style="color:#C62828; font-weight:700; size:20">
                    {resumen["total_nuevos"]} nuevos proyectos
                </span>, 
                de los cuales se han ejecutado 
                <span style="color:#C62828; font-weight:700;">
                    {resumen["ejecutados_nuevos"]} proyectos
                </span>.


                En total, la gestión del año contempla 
                <span style="color:#C62828; font-weight:700;">
                    {resumen["total_general"]} proyectos
                </span>, 
                lo que representa un incremento del 
                <span style="color:#C62828; font-weight:700;">
                    {resumen["incremento"]}%
                </span> 
                frente a lo inicialmente planificado.

            </div>

        </div>

        <style>
        .kpi-bar {{
            width: 100%;
            height: 10px;
            background: #eee;
            border-radius: 6px;
            overflow: hidden;
        }}

        .kpi-bar-fill {{
            height: 100%;
            width: 0;
            background: linear-gradient(90deg, #C62828, #ef5350);
            border-radius: 6px;
            transition: width 1.8s cubic-bezier(.4,0,.2,1);
            box-shadow: 0 0 8px rgba(198,40,40,0.4);
        }}

        .kpi-bar-item {{
            margin-bottom: 15px;
        }}

        .kpi-bar-label {{
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 4px;
        }}

        .kpi-bar-value {{
            font-size: 12px;
            margin-top: 4px;
            font-weight: 600;
        }}
        </style>

        <script>
        document.addEventListener("DOMContentLoaded", function() {{
            document.querySelectorAll('.kpi-bar-fill').forEach(function(bar) {{
                let target = bar.getAttribute("data-value");
                setTimeout(() => {{
                    bar.style.width = target + "%";
                }}, 400);
            }});
        }});
        </script>

            <div class="kpi-roi-header">
                <div class="kpi-roi-title">
                    Desempeño del ROI
                </div>
            </div>

            




           <div class="kpi-quick-stats">

                <div class="kpi-quick-item">
                    <div class="kpi-metric-value">128</div>
                    <div class="kpi-quick-label">Cantidad Nuevos Procesos</div>
                </div>

                <div class="kpi-quick-item">
                    <div class="kpi-metric-value">321</div>
                    <div class="kpi-quick-label">Ahorros Tiempo Horas</div>
                </div>

                <div class="kpi-quick-item">
                    <div class="kpi-metric-value">1,050</div>
                    <div class="kpi-quick-label">Ahorro Dinero</div>
                </div>

                <div class="kpi-quick-item">
                    <div class="kpi-metric-value">4</div>
                    <div class="kpi-quick-label">Cantidad Personas Beneficiadas</div>
                </div>

                <!-- 👇 Nota explicativa -->
                <div class="kpi-footer-notedesc">
                    Se realizaron <strong>17 encuestas</strong> para evaluar la satisfacción del cliente
                    a partir de 4 hitos importantes que engloban la experiencia general durante
                    y después de la entrega del proyecto (1 = Muy insatisfecho / 5 = Muy satisfecho).
                </div>

            </div>









            <div class="kpi-bottom-section"> 

                <div class="kpi-general-rating">
                    {estrellas_html}
                </div>

                <div class="kpi-satisfaction-grid">

                    <div class="kpi-metric-item">
                        <div class="kpi-metric-value">{prom_calidad}</div>
                        <div class="kpi-metric-label">Calidad de la<br>Solución</div>
                    </div>

                    <div class="kpi-metric-item">
                        <div class="kpi-metric-value">{prom_tiempo}</div>
                        <div class="kpi-metric-label">Tiempos de<br>entrega</div>
                    </div>

                    <div class="kpi-metric-item">
                        <div class="kpi-metric-value">{prom_acomp}</div>
                        <div class="kpi-metric-label">Acompañamiento</div>
                    </div>

                    <div class="kpi-metric-item">
                        <div class="kpi-metric-value">{prom_exp}</div>
                        <div class="kpi-metric-label">Experiencia de<br>Cliente</div>
                    </div>

                </div>

                <div class="kpi-footer-note">
                    Se realizaron <strong style="color:#C62828;"><b>{total_encuestas} encuestas</b></strong>


                    para evaluar la satisfacción del cliente a partir de 4 hitos
                    importantes que engloba la experiencia general que tuvo el
                    cliente durante y después de la entrega de un proyecto
                    (1 = Muy insatisfecho / 5 = Muy satisfecho).
                </div>

            </div>

        </div>
    </div>
    """




    paginas.append(pagina_kpi)


    # =========================
    # PÁGINA DERECHA - VIDEO
    # =========================
  

    pagina_video = f"""
    <div class="double full-video-page">
        <video id="kpiVideo" muted playsinline>
            <source src="../img/fondoderechakpi(2).mp4" type="video/mp4">
        </video>
    </div>
    """



    
    paginas.append(pagina_video)










    
    # --- Páginas de las tareas con layouts alternando colores ---
    # --- Páginas de las tareas (2 páginas por proyecto) ---
    color_anterior = None  

    for idx, (_, row) in enumerate(df.iterrows()):

        img_url = random.choice(imagenes)

        # Alternar colores SOLO para la página izquierda
        if color_anterior == 'azul':
            grupo = random.choice([layouts_oscuros, layouts_claros])
            color_anterior = 'oscuro' if grupo == layouts_oscuros else 'claro'
        elif color_anterior == 'oscuro':
            grupo = random.choice([layouts_azules, layouts_claros])
            color_anterior = 'azul' if grupo == layouts_azules else 'claro'
        else:
            grupo = random.choice([layouts_azules, layouts_oscuros, layouts_claros])
            if grupo == layouts_azules:
                color_anterior = 'azul'
            elif grupo == layouts_oscuros:
                color_anterior = 'oscuro'
            else:
                color_anterior = 'claro'

        layout_func = random.choice(grupo)

        # 🔹 Página izquierda (foto + datos)
        pagina_izquierda = layout_func(row, img_url)
        paginas.append(pagina_izquierda)

        # 🔹 Página derecha (descripción)
        pagina_derecha = layout_descripcion_proyecto(row)
        paginas.append(pagina_derecha)





    
    # --- HTML final CON FLECHAS Y EFECTO DE HOJAS EN LOS LATERALES DEL LIBRO ---
    html = f"""
    <!doctype html>
    <html lang="es">
    <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=1050, user-scalable=no" />
        <link rel="stylesheet" href="../css/enhanced-flipbook.css">
        <script type="text/javascript" src="../extras/jquery.min.1.7.js"></script>
        <script type="text/javascript" src="../extras/modernizr.2.5.3.min.js"></script>
        
        <style>
            /* Efecto de canto de libro en los laterales del flipbook */
            .container {{
                position: relative;
            }}
            
            .container::before,
            .container::after {{
                content: '';
                position: absolute;
                top: 0;
                height: 100%;
                width: 25px;
                z-index: 10000;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.5s ease;
            }}
            
            /* Mostrar bordes cuando ya no estamos en la portada */
            .container.show-edges::before,
            .container.show-edges::after {{
                opacity: 1;
            }}
            
            /* Borde izquierdo - hojas del libro */
            .container::before {{
                left: 0;
                background: 
                    repeating-linear-gradient(
                        to right,
                        rgba(255, 255, 255, 0.98) 0px,
                        rgba(248, 248, 248, 0.9) 0.8px,
                        rgba(242, 242, 242, 0.8) 1.5px,
                        rgba(255, 255, 255, 0.95) 2.3px,
                        rgba(250, 250, 250, 1) 3px,
                        rgba(245, 245, 245, 0.85) 3.8px,
                        rgba(238, 238, 238, 0.75) 4.5px,
                        rgba(255, 255, 255, 0.95) 5.3px,
                        rgba(248, 248, 248, 0.9) 6px,
                        rgba(242, 242, 242, 0.8) 6.8px,
                        rgba(255, 255, 255, 0.98) 7.5px,
                        rgba(250, 250, 250, 0.95) 8.3px,
                        rgba(245, 245, 245, 0.85) 9px,
                        rgba(238, 238, 238, 0.75) 9.8px,
                        rgba(255, 255, 255, 0.95) 10.5px,
                        rgba(248, 248, 248, 0.9) 11.3px,
                        rgba(242, 242, 242, 0.8) 12px,
                        rgba(255, 255, 255, 0.98) 12.8px,
                        rgba(250, 250, 250, 1) 13.5px,
                        rgba(245, 245, 245, 0.85) 14.3px,
                        rgba(238, 238, 238, 0.75) 15px,
                        transparent 25px
                    );
            }}
            
            /* Borde derecho - hojas del libro */
            .container::after {{
                right: 0;
                background: 
                    repeating-linear-gradient(
                        to left,
                        rgba(255, 255, 255, 0.98) 0px,
                        rgba(248, 248, 248, 0.9) 0.8px,
                        rgba(242, 242, 242, 0.8) 1.5px,
                        rgba(255, 255, 255, 0.95) 2.3px,
                        rgba(250, 250, 250, 1) 3px,
                        rgba(245, 245, 245, 0.85) 3.8px,
                        rgba(238, 238, 238, 0.75) 4.5px,
                        rgba(255, 255, 255, 0.95) 5.3px,
                        rgba(248, 248, 248, 0.9) 6px,
                        rgba(242, 242, 242, 0.8) 6.8px,
                        rgba(255, 255, 255, 0.98) 7.5px,
                        rgba(250, 250, 250, 0.95) 8.3px,
                        rgba(245, 245, 245, 0.85) 9px,
                        rgba(238, 238, 238, 0.75) 9.8px,
                        rgba(255, 255, 255, 0.95) 10.5px,
                        rgba(248, 248, 248, 0.9) 11.3px,
                        rgba(242, 242, 242, 0.8) 12px,
                        rgba(255, 255, 255, 0.98) 12.8px,
                        rgba(250, 250, 250, 1) 13.5px,
                        rgba(245, 245, 245, 0.85) 14.3px,
                        rgba(238, 238, 238, 0.75) 15px,
                        transparent 25px
                    );
            }}
        </style>
    </head>
    <body>

    <div class="flipbook-viewport">
        <div class="container">
            <div class="flipbook">
                {''.join(paginas)}
            </div>
        </div>
    </div>

    <!-- CONTENEDOR DE NAVEGACIÓN FIJO EN BORDES -->
    <div class="navigation-container">
        <!-- Área clickeable izquierda -->
        <div class="nav-area nav-area-left" id="prevArea"></div>
        <!-- Área clickeable derecha -->
        <div class="nav-area nav-area-right" id="nextArea"></div>
        
        <!-- Flechas visibles -->
        <div class="nav-icon nav-icon-left" id="prevPage">‹</div>
        <div class="nav-icon nav-icon-right" id="nextPage">›</div>
    </div>

    <script type="text/javascript" src="../lib/turn.min.js"></script>

    <!-- Inicialización del flipbook -->
    <script type="text/javascript">
        var $flipbook = $('.flipbook');

        $flipbook.turn({{
            elevation: 50,
            gradients: true,
            autoCenter: true,
            duration: 1000,
            acceleration: true,
            display: 'double',
            when: {{
                turning: function(event, page, view) {{
                    console.log('Página actual:', page);
                }}
            }}
        }});
    </script>

    <!-- LÓGICA DE FLECHAS Y BORDES MEJORADA -->
    <script type="text/javascript">
        $(document).ready(function() {{
            var $container = $('.container');
            
            // Navegación con flechas y áreas
            $('#nextPage, #nextArea').click(function() {{
                $flipbook.turn('next');
            }});

            $('#prevPage, #prevArea').click(function() {{
                $flipbook.turn('previous');
            }});

            // Navegación con teclado
            $(document).keydown(function(e) {{
                if (e.key === 'ArrowRight') {{
                    $flipbook.turn('next');
                }}
                if (e.key === 'ArrowLeft') {{
                    $flipbook.turn('previous');
                }}
            }});

            // Manejar visibilidad de flechas Y bordes de hojas
            $flipbook.bind('turned', function(event, page) {{
                var total = $flipbook.turn('pages');
                                var total = $flipbook.turn('pages');
                var video = document.getElementById("kpiVideo");

               
                var paginaVideo = 2; 

                if (video) {{
                    if (page === paginaVideo) {{
                         
                        video.play();            // reproduce
                    }}else {{
                         video.currentTime = 0;          // pausa si sales
                    }}
                }}
                            
                // Mostrar/ocultar bordes de hojas según la página
                if (page > 1) {{
                    $container.addClass('show-edges');
                }} else {{
                    $container.removeClass('show-edges');
                }}
                
                // Manejar flechas
                if (page <= 1) {{
                    $('#prevPage').fadeOut(200);
                    $('#prevArea').css('pointer-events', 'none');
                }} else {{
                    $('#prevPage').fadeIn(200);
                    $('#prevArea').css('pointer-events', 'all');
                }}
                
                if (page >= total) {{
                    $('#nextPage').fadeOut(200);
                    $('#nextArea').css('pointer-events', 'none');
                }} else {{
                    $('#nextPage').fadeIn(200);
                    $('#nextArea').css('pointer-events', 'all');
                }}
            }});

            // Inicializar visibilidad de flechas (sin bordes en portada)
            $flipbook.trigger('turned', [1]);
        }});
    </script>

    </body>
    </html>
    """
    


    # Crear directorio de salida si no existe
    os.makedirs(os.path.dirname(output), exist_ok=True)
    
    with open(output, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info(f"✅ Flipbook generado en {output}")
    logger.info(f"📊 Total de páginas: {len(paginas)}")
    logger.info(f"⬆️  Portada: título arriba, subtítulo abajo")
    logger.info(f"➡️  Flechas en los bordes de la pantalla")
    logger.info(f"📖 Efecto de hojas aparece después de la portada")



# -------------------------
# 7. Ejecutar
# -------------------------
if __name__ == "__main__":
    try:
        engine = conectar_db()
        df = obtener_tareas(engine)
        generar_flipbook(df)
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise