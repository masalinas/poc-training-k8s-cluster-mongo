#!/usr/bin/env python3
# =============================================================================
# scripts/generate_html_pdf.py
# Genera el documento HTML editorial y compila k8s-mongodb-statefulset.pdf
# =============================================================================
import os
import re
import sys
import shutil
import subprocess
import markdown

WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS_DIR = os.path.join(WORKSPACE_DIR, "docs")
MD_PATH = os.path.join(DOCS_DIR, "k8s-mongodb-statefulset.md")
HTML_PATH = os.path.join(DOCS_DIR, "k8s-mongodb-statefulset.html")
PDF_PATH = os.path.join(WORKSPACE_DIR, "k8s-mongodb-statefulset.pdf")

# Estructura jerárquica de marcadores para el panel lateral del PDF
OUTLINE_STRUCTURE = [
    {
        "title": "Portada",
        "page": 0
    },
    {
        "title": "Tabla de Contenidos",
        "id": "toc"
    },
    {
        "title": "1. Fundamentos y Arquitectura de Estado en Kubernetes",
        "id": "sec1",
        "children": [
            {"title": "1.1 El Contrato de Estado: Deployment vs StatefulSet", "id": "sec1-1"},
            {"title": "1.2 Diagrama de Topología y Flujo de Replicación del Replica Set", "id": "sec1-2"},
            {"title": "1.3 Matriz de Componentes del Clúster", "id": "sec1-3"}
        ]
    },
    {
        "title": "2. Preparación del Almacenamiento Dinámico (StorageClass)",
        "id": "sec2",
        "children": [
            {"title": "2.1 El Problema del Almacenamiento en Clústeres Kubeadm", "id": "sec2-1"},
            {"title": "2.2 Despliegue de Rancher local-path-provisioner", "id": "sec2-2"},
            {"title": "2.3 Verificación de la StorageClass por Defecto", "id": "sec2-3"},
            {"title": "2.4 Ajuste de Tolerancias del Nodo Master (Control Plane)", "id": "sec2-4"}
        ]
    },
    {
        "title": "3. Configuración Base y Gestión de Credenciales",
        "id": "sec3",
        "children": [
            {"title": "3.1 Secret de Autenticación para Superusuario y Clúster KeyFile", "id": "sec3-1"},
            {"title": "3.2 ConfigMap con mongod.conf (WiredTiger, Replicación y Seguridad)", "id": "sec3-2"}
        ]
    },
    {
        "title": "4. La Capa de Red: Headless Service y el Paradigma de Conexión de MongoDB",
        "id": "sec4",
        "children": [
            {"title": "4.1 Por qué un Servicio Estándar no Sirve: Headless Service (clusterIP: None)", "id": "sec4-1"},
            {"title": "4.2 Resolución DNS Individual por Pod en CoreDNS", "id": "sec4-2"},
            {"title": "4.3 El Antipatrón del Servicio Primario Estático y el Rol de los Drivers", "id": "sec4-3"}
        ]
    },
    {
        "title": "5. Despliegue del StatefulSet y Mecánica del InitContainer",
        "id": "sec5",
        "children": [
            {"title": "5.1 Anatomía del StatefulSet: replicas, serviceName y OrderedReady", "id": "sec5-1"},
            {"title": "5.2 Aislamiento de Volúmenes con volumeClaimTemplates", "id": "sec5-2"},
            {"title": "5.3 Desmontando la Fricción de Seguridad: El InitContainer para el keyFile", "id": "sec5-3"},
            {"title": "5.4 Despliegue Secuencial y Seguimiento del Arranque", "id": "sec5-4"}
        ]
    },
    {
        "title": "6. Inicialización Guiada y Verificación del Replica Set",
        "id": "sec6",
        "children": [
            {"title": "6.1 Acceso Interactivo con mongosh al Pod Inicial (mongodb-0)", "id": "sec6-1"},
            {"title": "6.2 Inicialización del Replica Set (rs.initiate()) paso a paso con FQDNs", "id": "sec6-2"},
            {"title": "6.3 Creación de Base de Datos, Colección y Documentos de Prueba", "id": "sec6-3"},
            {"title": "6.4 Validación de Replicación Oplog en Secundarios y Protección contra Escrituras", "id": "sec6-4"}
        ]
    },
    {
        "title": "7. El Experimento del Caos: Resiliencia y Límites de Kubernetes Puro",
        "id": "sec7",
        "children": [
            {"title": "7.1 Fase 1: Caída del Nodo Primario y Elección Automática por Quórum", "id": "sec7-1"},
            {"title": "7.2 Fase 2: Simulación de Pérdida de Quórum y Auto-Degradación", "id": "sec7-2"},
            {"title": "7.3 Fase 3: El Dilema del Escalado en StatefulSets (5 réplicas vs rs.conf())", "id": "sec7-3"},
            {"title": "7.4 Por qué las Primitivas Nativas no Pueden Resolver la Gestión del Ciclo de Vida", "id": "sec7-4"}
        ]
    },
    {
        "title": "8. La Brecha hacia la Producción: Por Qué Usamos Operadores",
        "id": "sec8",
        "children": [
            {"title": "8.1 Matriz Comparativa: StatefulSet Manual vs. Operadores de Producción", "id": "sec8-1"},
            {"title": "8.2 Capacidades Esenciales de un Operador (MongoDB Community y Percona PSMDB)", "id": "sec8-2"}
        ]
    },
    {
        "title": "9. Resolución de Problemas Frecuentes (Troubleshooting)",
        "id": "sec9",
        "children": [
            {"title": "9.1 Error 1: Permisos Abiertos en Keyfile (permissions on keyfile are too open)", "id": "sec9-1"},
            {"title": "9.2 Error 2: Operación Rechazada en Secundario (NotWritablePrimary)", "id": "sec9-2"},
            {"title": "9.3 Error 3: Pods en Pending por Ausencia de StorageClass o Taints", "id": "sec9-3"},
            {"title": "9.4 Error 4: Fallo de Resolución DNS durante rs.initiate()", "id": "sec9-4"}
        ]
    }
]

CSS_STYLES = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

    @page {
      size: A4 portrait;
      margin: 18mm 14mm 18mm 14mm;
      @bottom-right {
        content: "Página " counter(page);
        font-family: 'Inter', sans-serif;
        font-size: 8pt;
        color: #64748b;
      }
      @bottom-left {
        content: "Curso Kubernetes - Cap. 3: MongoDB con StatefulSets y Consenso Distribuido";
        font-family: 'Inter', sans-serif;
        font-size: 8pt;
        color: #64748b;
      }
    }

    * {
      box-sizing: border-box;
    }

    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      font-size: 10pt;
      line-height: 1.55;
      color: #1e293b;
      background-color: #ffffff;
      margin: 0;
      padding: 0;
    }

    /* Portada Editorial */
    .cover {
      page-break-after: always;
      display: flex;
      flex-direction: column;
      justify-content: center;
      min-height: 90vh;
      padding: 40px 20px;
    }

    .badge-k8s {
      display: inline-block;
      align-self: flex-start;
      background-color: #dbeafe;
      color: #1e40af;
      font-weight: 700;
      font-size: 9pt;
      padding: 6px 14px;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 24px;
    }

    .cover h1 {
      font-size: 26pt;
      font-weight: 800;
      line-height: 1.2;
      color: #0f172a;
      margin: 0 0 16px 0;
      letter-spacing: -0.02em;
    }

    .cover h2 {
      font-size: 14pt;
      font-weight: 500;
      line-height: 1.45;
      color: #475569;
      margin: 0 0 40px 0;
    }

    .cover-meta {
      border-top: 2px solid #e2e8f0;
      padding-top: 24px;
      margin-top: 20px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      font-size: 9pt;
      color: #64748b;
    }

    .cover-meta strong {
      color: #0f172a;
      display: block;
      margin-bottom: 2px;
    }

    .cover-footer {
      margin-top: 40px;
      padding: 14px 18px;
      background-color: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      font-size: 8.5pt;
      color: #475569;
      line-height: 1.5;
    }

    /* Encabezados y Secciones */
    .section-banner {
      background: linear-gradient(135deg, #1e3a8a 0%, #0369a1 100%);
      color: #ffffff;
      padding: 14px 18px;
      border-radius: 8px;
      margin-top: 36px;
      margin-bottom: 20px;
      page-break-after: avoid;
      page-break-inside: avoid;
    }

    .section-banner h2 {
      color: #ffffff;
      font-weight: 700;
      border-bottom: none;
      padding: 0;
      margin: 0;
      font-size: 15pt;
    }

    .section-banner p {
      color: #bae6fd;
      margin: 4px 0 0 0;
      font-size: 8.5pt;
    }

    h3 {
      font-size: 12pt;
      font-weight: 600;
      color: #1e3a8a;
      margin-top: 22px;
      margin-bottom: 8px;
      page-break-after: avoid;
    }

    h4 {
      font-size: 10.5pt;
      font-weight: 600;
      color: #334155;
      margin-top: 14px;
      margin-bottom: 6px;
      page-break-after: avoid;
    }

    p {
      margin-top: 0;
      margin-bottom: 10px;
    }

    ul, ol {
      margin-top: 0;
      margin-bottom: 12px;
      padding-left: 22px;
    }

    li {
      margin-bottom: 4px;
    }

    /* Bloques de Código */
    pre {
      background-color: #0f172a;
      color: #f8fafc;
      font-family: 'JetBrains Mono', monospace;
      font-size: 8pt;
      line-height: 1.45;
      padding: 12px 14px;
      border-radius: 6px;
      border-left: 4px solid #38bdf8;
      margin: 10px 0 14px 0;
      page-break-inside: avoid;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
      white-space: pre-wrap !important;
      word-wrap: break-word !important;
      word-break: break-all !important;
      overflow-wrap: anywhere !important;
      overflow: visible !important;
    }

    code {
      font-family: 'JetBrains Mono', monospace;
      font-size: 8.5pt;
      background-color: #f1f5f9;
      color: #0f172a;
      padding: 2px 5px;
      border-radius: 4px;
      border: 1px solid #e2e8f0;
      word-break: break-all;
      overflow-wrap: anywhere;
    }

    pre code {
      background-color: transparent;
      color: inherit;
      padding: 0;
      border: none;
      font-size: inherit;
      white-space: pre-wrap !important;
      word-break: break-all !important;
      overflow-wrap: anywhere !important;
    }

    /* Alertas y Callouts */
    .alert {
      padding: 12px 14px;
      border-radius: 6px;
      margin: 14px 0;
      font-size: 9pt;
      page-break-inside: avoid;
      border-left: 4px solid;
    }

    .alert-warning {
      background-color: #fffbeb;
      border-color: #f59e0b;
      color: #92400e;
    }

    .alert-important {
      background-color: #fef2f2;
      border-color: #ef4444;
      color: #991b1b;
    }

    .alert-note {
      background-color: #f0f9ff;
      border-color: #0284c7;
      color: #075985;
    }

    .alert-tip {
      background-color: #f0fdf4;
      border-color: #22c55e;
      color: #166534;
    }

    .alert-caution {
      background-color: #fef2f2;
      border-color: #dc2626;
      color: #7f1d1d;
    }

    .alert-title {
      font-weight: 700;
      margin-bottom: 4px;
      text-transform: uppercase;
      font-size: 8pt;
      letter-spacing: 0.05em;
    }

    /* Tablas */
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 14px 0;
      font-size: 8.8pt;
      page-break-inside: avoid;
    }

    th, td {
      border: 1px solid #cbd5e1;
      padding: 8px 10px;
      text-align: left;
    }

    th {
      background-color: #f8fafc;
      font-weight: 600;
      color: #0f172a;
    }

    tr:nth-child(even) td {
      background-color: #f1f5f9;
    }

    /* Tabla de Contenidos */
    .toc {
      background-color: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 30px;
      page-break-after: always;
    }

    .toc h2 {
      margin-top: 0;
      border-bottom: 2px solid #cbd5e1;
      padding-bottom: 8px;
      font-size: 14pt;
      color: #0f172a;
    }

    .toc ul {
      list-style-type: none;
      padding-left: 0;
      margin-bottom: 0;
    }

    .toc > ul > li {
      font-weight: 600;
      margin-top: 10px;
    }

    .toc ul ul {
      padding-left: 20px;
      margin-top: 4px;
    }

    .toc ul ul li {
      font-weight: 400;
      font-size: 9pt;
      margin-bottom: 3px;
    }

    .toc a {
      color: #1e3a8a;
      text-decoration: none;
    }

    .toc a:hover {
      text-decoration: underline;
    }
"""

def build_editorial_html(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Pre-procesamiento de alertas de estilo GitHub
    def replace_alerts(match):
        kind = match.group(1).lower()
        content = match.group(2).strip()
        titles = {
            "note": "Nota Técnica",
            "tip": "Consejo Práctico",
            "warning": "Advertencia",
            "caution": "Precaución Crítica",
            "important": "Importante"
        }
        title = titles.get(kind, kind.capitalize())
        # Convertir párrafos internos
        lines = [line.lstrip("> ").strip() for line in content.split("\n")]
        body = "<br>".join(lines)
        return f'<div class="alert alert-{kind}"><div class="alert-title">{title}</div>{body}</div>'

    alert_pattern = re.compile(r'> \[!(NOTE|TIP|WARNING|CAUTION|IMPORTANT)\](.*?)(?=\n\n|\n[^\>]|$)', re.DOTALL | re.IGNORECASE)
    processed_md = alert_pattern.sub(replace_alerts, md_text)

    # Conversión Markdown a HTML con extensiones
    raw_html = markdown.markdown(processed_md, extensions=['fenced_code', 'tables'])

    # Post-procesamiento para insertar IDs estructurados en h2 y h3
    chapter_subs = {
        1: "El contrato de estado, comparativa de identidad y topología de Replica Set",
        2: "Aprovisionamiento dinámico local, Rancher local-path y tolerancias de nodo",
        3: "Secret con clave criptográfica keyFile y ConfigMap con mongod.conf",
        4: "Headless Services (clusterIP: None), CoreDNS y conexión dinámica por seedlist",
        5: "StatefulSets OrderedReady, PVCs dedicados e initContainer para permisos 0400",
        6: "Conexión interactiva con mongosh, rs.initiate() con FQDNs y verificación de Oplog",
        7: "Inyección de fallos, quórum de elecciones, auto-degradación y desfase de escalado",
        8: "Análisis comparativo: StatefulSet manual frente a MongoDB Community y Percona PSMDB",
        9: "Diagnóstico y remediación de errores frecuentes de red, almacenamiento y permisos"
    }

    def replace_h2(match):
        full_title = match.group(1).strip()
        m = re.match(r'^(\d+)\.\s*(.*)', full_title)
        if m:
            num = int(m.group(1))
            sec_id = f"sec{num}"
            subtitle = chapter_subs.get(num, "")
            return f'<div class="section-banner" id="{sec_id}"><h2>{full_title}</h2><p>{subtitle}</p></div>'
        return f'<h2>{full_title}</h2>'

    raw_html = re.sub(r'<h2>(.*?)</h2>', replace_h2, raw_html)

    def replace_h3(match):
        full_title = match.group(1).strip()
        m = re.match(r'^(\d+)\.(\d+)\s*(.*)', full_title)
        if m:
            sec_id = f"sec{m.group(1)}-{m.group(2)}"
            return f'<h3 id="{sec_id}">{full_title}</h3>'
        return f'<h3>{full_title}</h3>'

    raw_html = re.sub(r'<h3>(.*?)</h3>', replace_h3, raw_html)

    # Separar la Portada, TOC y el Contenido Principal
    # Construcción de la Portada Editorial
    cover_html = """
    <div class="cover">
      <div class="badge-k8s">Capítulo 3 · Bases de Datos NoSQL y Consenso Distribuido</div>
      <h1>Guía Práctica de MongoDB en Kubernetes con StatefulSets</h1>
      <h2>Despliegue Manual de Alta Disponibilidad con Replica Set, Anatomía de Red y el Dilema de Orquestación sin Operadores</h2>
      
      <div class="cover-meta">
        <div>
          <strong>Autor:</strong>
          Equipo Docente de Kubernetes y Arquitectura de Datos
        </div>
        <div>
          <strong>Documento Oficial del Curso:</strong>
          Capítulo 3 - Gestión de Cargas con Estado NoSQL
        </div>
        <div>
          <strong>Entregable del Laboratorio:</strong>
          <code>k8s-mongodb-statefulset.pdf</code>
        </div>
        <div>
          <strong>Pila Tecnológica Evaluada:</strong>
          Kubernetes v1.31, MongoDB 7.0, local-path-provisioner, CoreDNS
        </div>
      </div>

      <div class="cover-footer">
        <strong>Objetivo del Laboratorio:</strong> Comprender a nivel de paquete y almacenamiento el funcionamiento de un Replica Set distribuido de MongoDB en Kubernetes estándar. Demostrar empíricamente las capacidades de auto-elección de líder por quórum y los límites estructurales de las primitivas nativas ante particiones de red y operaciones de escalado, fundamentando la necesidad técnica de los Operadores en entornos productivos.
      </div>
    </div>
    """

    # Quitar los encabezados iniciales que se sustituyen por la portada y TOC
    main_body = re.sub(r'<h1>.*?</h1>', '', raw_html, count=1)
    main_body = re.sub(r'<h2>Tabla de Contenidos</h2>.*?<hr />', '', main_body, count=1, flags=re.DOTALL)
    main_body = re.sub(r'<p><strong>Autor:</strong>.*?</p>', '', main_body, count=1, flags=re.DOTALL)

    # Tabla de Contenidos estilizada
    toc_html = """
    <div class="toc" id="toc">
      <h2>Tabla de Contenidos</h2>
      <ul>
        <li><a href="#sec1">1. Fundamentos y Arquitectura de Estado en Kubernetes</a>
          <ul>
            <li><a href="#sec1-1">1.1 El Contrato de Estado: Deployment vs StatefulSet</a></li>
            <li><a href="#sec1-2">1.2 Diagrama de Topología y Flujo de Replicación del Replica Set</a></li>
            <li><a href="#sec1-3">1.3 Matriz de Componentes del Clúster</a></li>
          </ul>
        </li>
        <li><a href="#sec2">2. Preparación del Almacenamiento Dinámico (StorageClass)</a>
          <ul>
            <li><a href="#sec2-1">2.1 El Problema del Almacenamiento en Clústeres Kubeadm / Bare-Metal</a></li>
            <li><a href="#sec2-2">2.2 Despliegue de Rancher local-path-provisioner</a></li>
            <li><a href="#sec2-3">2.3 Verificación de la StorageClass por Defecto</a></li>
            <li><a href="#sec2-4">2.4 Ajuste de Tolerancias del Nodo Master (Control Plane)</a></li>
          </ul>
        </li>
        <li><a href="#sec3">3. Configuración Base y Gestión de Credenciales</a>
          <ul>
            <li><a href="#sec3-1">3.1 Secret de Autenticación para Superusuario y Clúster KeyFile</a></li>
            <li><a href="#sec3-2">3.2 ConfigMap con mongod.conf (WiredTiger, Replicación y Seguridad)</a></li>
          </ul>
        </li>
        <li><a href="#sec4">4. La Capa de Red: Headless Service y el Paradigma de Conexión de MongoDB</a>
          <ul>
            <li><a href="#sec4-1">4.1 Por qué un Servicio Estándar no Sirve: Headless Service (clusterIP: None)</a></li>
            <li><a href="#sec4-2">4.2 Resolución DNS Individual por Pod en CoreDNS</a></li>
            <li><a href="#sec4-3">4.3 El Antipatrón del Servicio Primario Estático y el Rol de los Drivers</a></li>
          </ul>
        </li>
        <li><a href="#sec5">5. Despliegue del StatefulSet y Mecánica del InitContainer</a>
          <ul>
            <li><a href="#sec5-1">5.1 Anatomía del StatefulSet: replicas, serviceName y OrderedReady</a></li>
            <li><a href="#sec5-2">5.2 Aislamiento de Volúmenes con volumeClaimTemplates</a></li>
            <li><a href="#sec5-3">5.3 Desmontando la Fricción de Seguridad: El InitContainer para el keyFile</a></li>
            <li><a href="#sec5-4">5.4 Despliegue Secuencial y Seguimiento del Arranque</a></li>
          </ul>
        </li>
        <li><a href="#sec6">6. Inicialización Guiada y Verificación del Replica Set</a>
          <ul>
            <li><a href="#sec6-1">6.1 Acceso Interactivo con mongosh al Pod Inicial (mongodb-0)</a></li>
            <li><a href="#sec6-2">6.2 Inicialización del Replica Set (rs.initiate()) paso a paso con FQDNs</a></li>
            <li><a href="#sec6-3">6.3 Creación de Base de Datos, Colección y Documentos de Prueba</a></li>
            <li><a href="#sec6-4">6.4 Validación de Replicación Oplog en Secundarios y Protección contra Escrituras</a></li>
          </ul>
        </li>
        <li><a href="#sec7">7. El Experimento del Caos: Resiliencia y Límites de Kubernetes Puro</a>
          <ul>
            <li><a href="#sec7-1">7.1 Fase 1: Caída del Nodo Primario y Elección Automática por Quórum</a></li>
            <li><a href="#sec7-2">7.2 Fase 2: Simulación de Pérdida de Quórum y Auto-Degradación</a></li>
            <li><a href="#sec7-3">7.3 Fase 3: El Dilema del Escalado en StatefulSets (5 réplicas vs rs.conf())</a></li>
            <li><a href="#sec7-4">7.4 Por qué las Primitivas Nativas no Pueden Resolver la Gestión del Ciclo de Vida</a></li>
          </ul>
        </li>
        <li><a href="#sec8">8. La Brecha hacia la Producción: Por Qué Usamos Operadores</a>
          <ul>
            <li><a href="#sec8-1">8.1 Matriz Comparativa: StatefulSet Manual vs. Operadores de Producción</a></li>
            <li><a href="#sec8-2">8.2 Capacidades Esenciales de un Operador (MongoDB Community y Percona PSMDB)</a></li>
          </ul>
        </li>
        <li><a href="#sec9">9. Resolución de Problemas Frecuentes (Troubleshooting)</a>
          <ul>
            <li><a href="#sec9-1">9.1 Error 1: Permisos Abiertos en Keyfile (permissions on keyfile are too open)</a></li>
            <li><a href="#sec9-2">9.2 Error 2: Operación Rechazada en Secundario (NotWritablePrimary)</a></li>
            <li><a href="#sec9-3">9.3 Error 3: Pods en Pending por Ausencia de StorageClass o Taints</a></li>
            <li><a href="#sec9-4">9.4 Error 4: Fallo de Resolución DNS durante rs.initiate()</a></li>
          </ul>
        </li>
      </ul>
    </div>
    """

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Guía Práctica de MongoDB en Kubernetes con StatefulSets</title>
  <style>
{CSS_STYLES}
  </style>
</head>
<body>
{cover_html}
{toc_html}
{main_body}
</body>
</html>
"""
    return full_html

def add_pdf_bookmarks(pdf_path):
    """Inyecta el árbol de marcadores (Document Outlines) en el PDF usando pypdf."""
    try:
        import pypdf
    except ImportError:
        print("Aviso: 'pypdf' no está disponible. Omitiendo inyección de marcadores del panel lateral.")
        return

    print("Inyectando marcadores jerárquicos (Document Outlines) en el panel lateral del PDF...")
    reader = pypdf.PdfReader(pdf_path)
    writer = pypdf.PdfWriter()
    writer.append(reader)

    def get_page(target_id):
        for key in (target_id, "/" + target_id):
            if key in reader.named_destinations:
                return reader.get_destination_page_number(reader.named_destinations[key])
        return None

    def add_items(items, parent=None):
        for item in items:
            p_num = item.get("page")
            if p_num is None and "id" in item:
                p_num = get_page(item["id"])
            if p_num is not None:
                node = writer.add_outline_item(item["title"], p_num, parent=parent)
                if "children" in item:
                    add_items(item["children"], parent=node)

    add_items(OUTLINE_STRUCTURE)

    temp_path = pdf_path + ".tmp"
    with open(temp_path, "wb") as f:
        writer.write(f)
    os.replace(temp_path, pdf_path)

def main():
    os.makedirs(DOCS_DIR, exist_ok=True)
    html_content = build_editorial_html(MD_PATH)
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML editorial generado exitosamente en: {HTML_PATH}")

    chrome_candidates = [
        "/opt/google/chrome/google-chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    ]
    chrome_bin = None
    for cand in chrome_candidates:
        if os.path.exists(cand):
            chrome_bin = cand
            break
        found = shutil.which(cand)
        if found:
            chrome_bin = found
            break

    if not chrome_bin:
        chrome_bin = "google-chrome"

    cmd = [
        chrome_bin,
        "--headless",
        "--no-sandbox",
        "--disable-gpu",
        "--allow-file-access-from-files",
        "--enable-local-file-accesses",
        "--user-data-dir=/tmp/chrome-user-data-mongo",
        "--no-pdf-header-footer",
        f"--print-to-pdf={PDF_PATH}",
        f"file://{HTML_PATH}"
    ]
    print(f"Compilando PDF con Chrome headless a: {PDF_PATH}...")
    if os.path.exists(PDF_PATH):
        os.remove(PDF_PATH)

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode == 0 and os.path.exists(PDF_PATH):
        add_pdf_bookmarks(PDF_PATH)
        size_kb = os.path.getsize(PDF_PATH) / 1024
        print(f"¡Éxito! Archivo PDF compilado con marcadores del panel lateral: {PDF_PATH} ({size_kb:.1f} KB)")
    else:
        print("Error generando PDF:")
        print(res.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
