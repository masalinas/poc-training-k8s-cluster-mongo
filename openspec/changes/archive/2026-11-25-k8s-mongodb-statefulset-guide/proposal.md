# Proposal: Guía Práctica de MongoDB en Kubernetes con StatefulSet y Contraste con Operadores

## Why

El despliegue de bases de datos NoSQL distribuidas en Kubernetes mediante Operadores oculta la complejidad fundamental de la orquestación con estado. Los estudiantes y administradores frecuentemente desconocen cómo interactúan los StatefulSets, los Headless Services, el aprovisionamiento dinámico de almacenamiento y los initContainers para la gestión de seguridad. Asimismo, se suele asumir erróneamente que la elección interna de un Replica Set de MongoDB sustituye la necesidad de un Operador en Kubernetes.

Esta propuesta define la creación de una guía técnica exhaustiva, práctica y visual para desplegar un clúster de 3 nodos de MongoDB (Replica Set `rs0`) utilizando exclusivamente primitivas nativas de Kubernetes. Se explicará detalladamente la anatomía de red, la inicialización interactiva paso a paso de `rs.initiate()`, y se ejecutará un laboratorio de caos que expondrá las limitaciones de Kubernetes puro (desincronización de `rs.conf()` al escalar, pérdida de quórum y falta de gestión del ciclo de vida). Adicionalmente, incluye el pipeline automatizado para compilar la documentación a un entregable editorial PDF profesional (`k8s-mongodb-statefulset.pdf`) con el mismo estándar visual que la guía de PostgreSQL.

## What Changes

- **Guía Técnica Exhaustiva en Markdown**: Creación de `docs/k8s-mongodb-statefulset.md` estructurada en 9 capítulos detallados, diagramas de arquitectura en ASCII puro, explicaciones teóricas, comandos reproducibles con salidas de consola esperadas, inicialización interactiva paso a paso de `rs.initiate()`, y laboratorio de simulación de fallos (caos, quórum y desincronización de escalado).
- **Manifiestos Kubernetes Nativos**:
  - `manifests/00-local-path-storage.yaml`: Aprovisionamiento dinámico local (`local-path-provisioner`) para clusters Kubeadm on-premise/bare-metal.
  - `manifests/01-mongo-secret.yaml`: Credenciales de superusuario administrativo y Secret con `keyFile` de 756 bytes para autenticación interna de miembros del clúster.
  - `manifests/02-mongo-configmap.yaml`: Archivo de configuración `mongod.conf` optimizado (WiredTiger, replicación `replSetName: rs0` y seguridad con `keyFile` activada).
  - `manifests/03-mongo-service.yaml`: Headless Service (`clusterIP: None`) para resolución DNS determinista de Pods (`mongodb-0.mongodb-headless...`).
  - `manifests/04-mongo-statefulset.yaml`: StatefulSet de 3 réplicas (`mongo:7.0`), `volumeClaimTemplates` dedicados de 1Gi y un `initContainer` que resuelve los permisos estrictos (`chmod 400`, `chown 999:999`) requeridos por el `keyFile` sobre un volumen `emptyDir`.
- **Laboratorio Demostrativo de Caos y Desfase de Orquestación**:
  - Demostración de failover automático interno: caída de `mongodb-0` y elección democrática del nuevo PRIMARY en `mongodb-1` por quórum (2 de 3 votos).
  - Demostración de pérdida de quórum: caída simultánea de 2 nodos, auto-degradación a SECONDARY del nodo superviviente y bloqueo de escrituras.
  - Demostración del dilema de escalado: escalado de pods a 5 réplicas mediante Kubernetes y constatación de la ignorancia del Replica Set (`rs.status()`), evidenciando la necesidad de un Operador.
- **Pipeline de Compilación HTML/PDF**: Creación de `scripts/generate_html_pdf.py` para generar una maquetación HTML editorial A4 (tipografías Inter y JetBrains Mono, bloques de código estilizados, badges) y compilación desatendida a `k8s-mongodb-statefulset.pdf` con árbol de marcadores jerárquicos vía Google Chrome headless y `pypdf`.

## Capabilities

### New Capabilities

- `mongodb-statefulset-cluster`: Especificación del despliegue manual de un clúster MongoDB 7.0 en topología Replica Set de 3 miembros (`rs0`) con autenticación por `keyFile` mediante primitivas nativas de Kubernetes (StatefulSet, Headless Service, PVCs dinámicos, `initContainer` de permisos y bootstrap interactivo `rs.initiate()`).
- `operator-pedagogical-contrast`: Especificación del laboratorio de pruebas de fallo (elección automática, partición y pérdida de quórum, escalado desincronizado) y matriz comparativa profunda frente a Operadores de producción (MongoDB Community Kubernetes Operator y Percona Server for MongoDB Operator).
- `technical-guide-pdf-pipeline`: Especificación del pipeline de documentación técnica y compilación a PDF profesional estructurado con soporte de marcadores e identidad visual homogénea.

### Modified Capabilities

*(Ninguna, proyecto base sin especificaciones previas)*

## Impact

- **Código y Manifiestos**: Nuevos archivos en `docs/`, `manifests/` y `scripts/`.
- **Compatibilidad**: Compatible con clústeres Kubeadm v1.31 (incluyendo clústeres de laboratorio de dos máquinas virtuales), Minikube, Kind o K3s.
- **Dependencias de generación**: Python 3, `pypdf` y Google Chrome o Chromium para la compilación del entregable PDF.
