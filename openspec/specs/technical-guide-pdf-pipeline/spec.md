# technical-guide-pdf-pipeline Specification

## Purpose
Define los requisitos de maquetación, formato editorial y automatización de la compilación desatendida del documento técnico a formato PDF profesional.

## Requirements

### Requirement: Documento Técnico Integral en Formato Markdown
El sistema DEBE (MUST) generar el archivo `docs/k8s-mongodb-statefulset.md` estructurado en 9 capítulos temáticos completos, incluyendo fundamentos, manifiestos explicados, verificación, experimentos de caos y resolución de problemas.

#### Scenario: Cobertura curricular completa
- **WHEN** el estudiante consulta la guía en formato Markdown
- **THEN** encuentra explicaciones teóricas, diagramas de arquitectura en texto ASCII puro y bloques de comandos con salidas reales esperadas.

### Requirement: Generación de Plantilla HTML Editorial Imprimible
El sistema DEBE (MUST) generar una representación HTML estilizada con soporte de paginación A4 vertical, reglas `@page`, tipografías Inter y JetBrains Mono, bloques de código syntax-ready y recuadros de advertencia.

#### Scenario: Visualización y maquetación web editorial
- **WHEN** se genera el archivo `docs/k8s-mongodb-statefulset.html` y se abre en un navegador
- **THEN** la maquetación respeta los saltos de página lógicos, números de página en pie de documento y márgenes estandarizados de 18mm x 14mm.

### Requirement: Compilación Desatendida a PDF con Jerarquía de Marcadores
El sistema DEBE (MUST) incluir un script en Python (`scripts/generate_html_pdf.py`) que invoque Google Chrome o Chromium en modo headless para compilar `k8s-mongodb-statefulset.pdf` e inyectar marcadores navegables vía `pypdf`.

#### Scenario: Compilación exitosa del PDF entregable
- **WHEN** se ejecuta el comando `python3 scripts/generate_html_pdf.py`
- **THEN** el proceso genera un archivo PDF válido en la raíz del proyecto, con panel de marcadores lateral estructurado coincidiendo con los 9 capítulos.
