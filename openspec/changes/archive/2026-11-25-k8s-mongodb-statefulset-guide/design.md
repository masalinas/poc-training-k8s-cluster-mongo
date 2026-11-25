# Design: Guía Práctica de MongoDB en Kubernetes con StatefulSet y Contraste de Operadores

## Context

Los cursos y laboratorios de infraestructura a menudo abordan el despliegue de bases de datos en Kubernetes saltando directamente a soluciones basadas en Operadores (CRDs y controladores). Aunque esta es la recomendación indiscutible para entornos productivos, genera un vacío pedagógico: los alumnos no llegan a comprender cómo interactúan las primitivas básicas de Kubernetes (StatefulSets, Headless Services, volumeClaimTemplates e initContainers), ni tampoco comprenden las particularidades de los sistemas de consenso distribuido como el protocolo de elecciones de MongoDB.

En el capítulo previo de la serie formativa (`poc-training-k8s-cluster-postgresql`), se analizó el comportamiento de PostgreSQL, donde el failover automático es inexistente sin software externo y el riesgo crítico es el *split-brain*. En MongoDB, el motor sí posee un mecanismo nativo de elección de líder (Raft-like) mediante quórum. Sin embargo, su despliegue manual en Kubernetes introduce dilemas arquitectónicos distintos: el desfase entre el número de réplicas en el StatefulSet y los miembros registrados en `rs.conf()`, el enrutamiento dinámico de red mediante drivers frente a servicios de Kubernetes, y los requisitos estrictos de permisos del `keyFile`.

## Goals / Non-Goals

**Goals:**
- Proporcionar una guía didáctica hiper-detallada, práctica y visual que enseñe paso a paso la orquestación manual de un clúster MongoDB 7.0 (Replica Set `rs0` de 3 miembros) sobre Kubernetes estándar.
- Detallar la teoría y mecánica interna de:
  - `StatefulSets`: Ordinales deterministas, inicio secuencial (`OrderedReady`) y vinculación persistente de almacenamiento.
  - `Headless Services`: Asignación de identidades de red FQDN por Pod y cómo los drivers de MongoDB usan la *seedlist* para descubrir al PRIMARY.
  - `volumeClaimTemplates`: Aislamiento de volúmenes persistentes desacoplados del ciclo de vida del Pod mediante `local-path-provisioner`.
  - `initContainers`: Patrón de preparación de archivos protegidos (`keyFile` con `chmod 400` y `chown 999:999` sobre `emptyDir`).
- Guiar la inicialización interactiva paso a paso del Replica Set (`rs.initiate()`) con `mongosh`, inspeccionando la transición de estados (`STARTUP`, `SECONDARY`, `PRIMARY`).
- Ejecutar un laboratorio de caos que demuestre empíricamente:
  - La elección automática y transparente de un nuevo PRIMARY tras eliminar forzosamente `mongodb-0`.
  - La pérdida de quórum al caer 2 de 3 nodos, provocando la auto-degradación a SECONDARY y el rechazo de escrituras.
  - El desfase de orquestación al escalar el StatefulSet a 5 réplicas sin actualización de `rs.conf()`.
- Elaborar una matriz comparativa profunda entre la gestión manual y los Operadores de producción (MongoDB Community Kubernetes Operator y Percona Server for MongoDB Operator).
- Proporcionar un script en Python que compile la guía a HTML editorial e imprima de forma desatendida el archivo `k8s-mongodb-statefulset.pdf` con el mismo estándar visual y jerarquía de marcadores que el capítulo de PostgreSQL.

**Non-Goals:**
- No se pretende construir un entorno para producción (en producción se debe emplear un Operador o servicio gestionado).
- No se implementará sharding distribuido (`mongos` + ConfigReplSet + ShardReplSets) dentro del laboratorio práctico para mantenerlo ligero y apto para máquinas virtuales de 2 GB de RAM; el sharding se analizará a nivel conceptual y arquitectónico en la comparativa de operadores.
- No se automatizarán backups remotos hacia almacenamiento en la nube (S3/GCS) en este laboratorio básico.

## Decisions

### Decisión 1: Imagen base oficial MongoDB 7.0 (`mongo:7.0`)
- **Elección**: Utilizar la imagen oficial `mongo:7.0`.
- **Razón**: Es la versión moderna estándar de MongoDB, incluye el shell moderno `mongosh` (reemplazando al antiguo y deprecado `mongo`), incorpora el motor de almacenamiento WiredTiger optimizado y cuenta con el protocolo de consenso actual de replicación.
- **Alternativas consideradas**: `mongo:6.0` (válida, pero 7.0 ofrece soporte a largo plazo y mejor telemetría en `rs.status()`), o imágenes precompiladas de Bitnami (las imágenes de Bitnami incluyen scripts de auto-configuración que ocultan la mecánica interna que justamente queremos enseñar).

### Decisión 2: Topología de Replica Set de 3 Miembros (`mongodb-0`, `1`, `2`)
- **Elección**: Desplegar 3 réplicas completas con datos.
- **Razón**: MongoDB requiere una mayoría estricta (`floor(N/2) + 1`) para el quórum electoral. Un clúster de 3 nodos permite tolerar la caída de 1 nodo manteniendo quórum (`2/3 > 50%`).
- **Alternativas consideradas**: 2 nodos de datos + 1 árbitro (reduce consumo de disco pero añade asimetría innecesaria a un laboratorio donde cada nodo tiene un PVC de solo 1Gi) o 2 nodos sin árbitro (no permite elección automática ante fallo del primario, desvirtuando el experimento de failover).

### Decisión 3: Gestión de Seguridad del KeyFile con InitContainer y EmptyDir
- **Elección**: Almacenar la clave de 756 bytes generada con `openssl rand -base64 756` en un Secret de Kubernetes, y emplear un `initContainer` en cada Pod que la copie a un volumen `emptyDir` aplicando `chmod 400` y `chown 999:999`.
- **Razón**: Los Secrets de Kubernetes se montan con permisos de solo lectura (`0644` o gestionados por root). MongoDB rechaza arrancar con la directiva `security.keyFile` si el archivo tiene permisos abiertos (`permissions on keyfile are too open`). El patrón de `initContainer` con `emptyDir` es la forma canónica y limpia de solventar este conflicto en Kubernetes nativo.
- **Alternativas consideradas**: Desactivar autenticación de clúster (inseguro y poco didáctico) o usar un contenedor con Dockerfile personalizado (añade pasos de build innecesarios para el estudiante).

### Decisión 4: Headless Service Exclusivo y Conexión de Clientes por Seedlist
- **Elección**: Desplegar únicamente un `Headless Service` (`mongodb-headless`, `clusterIP: None`) y documentar que las aplicaciones deben conectarse mediante la URI de Replica Set (`mongodb://mongodb-0.mongodb-headless...,mongodb-1...,mongodb-2.../?replicaSet=rs0`).
- **Razón**: En PostgreSQL es común tener un Service `postgresql-primary` apuntando al Pod 0. En MongoDB, esto es un grave antipatrón porque cualquier réplica puede ser elegida PRIMARY. Si el Pod 0 cae y el Pod 1 asciende a PRIMARY, un Service tradicional seguiría dirigiendo escrituras al Pod 0 (provocando errores de `NotWritablePrimary`). Los drivers de MongoDB están diseñados para recibir la lista de semillas, consultar el comando `hello` y enrutar dinámicamente las escrituras al PRIMARY actual.
- **Alternativas consideradas**: Crear servicios NodePort individuales (añade complejidad innecesaria al clúster de laboratorio).

### Decisión 5: Inicialización Interactiva con `mongosh` (`rs.initiate()`)
- **Elección**: Detallar el proceso de inicialización ejecutando `rs.initiate()` de forma manual e interactiva dentro del Pod `mongodb-0`.
- **Razón**: Permite al estudiante comprender la estructura del documento de configuración `rs.conf()`, observar cómo se asignan los `_id` numéricos y cómo los FQDNs de Kubernetes se registran en el catálogo interno de MongoDB.
- **Alternativas consideradas**: Automatizar la inicialización mediante un Job o script en postStart (reduce la visibilidad didáctica del paso).

### Decisión 6: Laboratorio de Caos en Tres Fases
- **Elección**: Diseñar el experimento de caos en tres etapas:
  1. Caída de `mongodb-0`: Demostrar la resiliencia nativa de MongoDB (elección de nuevo líder en segundos por quórum 2/3).
  2. Pérdida de quórum: Detener `mongodb-1` y `mongodb-2`. Demostrar cómo `mongodb-0` se auto-degrada a SECONDARY para proteger la integridad y rechaza escrituras.
  3. Escalado en StatefulSets: Escalar a 5 réplicas con `kubectl scale` y evidenciar que los nuevos Pods no forman parte de `rs.status()`, justificando por qué los Operadores son indispensables.
- **Razón**: Proporciona una progresión pedagógica completa que va desde el funcionamiento esperado hasta los límites insalvables de las primitivas nativas de Kubernetes.

### Decisión 7: Pipeline de Compilación HTML/PDF idéntico al de PostgreSQL
- **Elección**: Replicar la arquitectura de `scripts/generate_html_pdf.py` adaptándola a MongoDB, utilizando Chrome/Chromium headless y `pypdf` para inyectar marcadores jerárquicos.
- **Razón**: Mantiene la coherencia visual absoluta, los márgenes de impresión A4, el esquema tipográfico (Inter y JetBrains Mono) y el diseño de la colección documental del curso.

## Risks / Trade-offs

- **[Riesgo] Recursos de memoria limitados en el nodo Worker (2 GB RAM)** → **Mitigación**: Configurar límites y reservas en el StatefulSet (`resources.requests` y `resources.limits`) y parametrizar en `mongod.conf` el tamaño de caché de WiredTiger (`wiredTiger.engineConfig.cacheSizeGB: 0.25`) para evitar caídas por OOMKilled cuando coexistan los 3 pods.
- **[Riesgo] Taint del nodo Control Plane (Master)** → **Mitigación**: Explicar en el capítulo de preparación cómo tolerar o retirar el taint del nodo master en clústeres de 2 máquinas virtuales para permitir que los 3 pods se programen adecuadamente.
- **[Riesgo] Ausencia de dependencias de renderizado en el host del usuario** → **Mitigación**: El script `scripts/generate_html_pdf.py` incluye detección automática de binarios de Chrome/Chromium en Linux y macOS e imprime mensajes claros sobre cómo instalar `pypdf` mediante `pip`.

## Migration Plan

1. Aprovisionar StorageClass `local-path` en el clúster (`00-local-path-storage.yaml`).
2. Crear Secrets con usuario root y keyFile (`01-mongo-secret.yaml`).
3. Aplicar ConfigMap con `mongod.conf` (`02-mongo-configmap.yaml`).
4. Desplegar Headless Service (`03-mongo-service.yaml`).
5. Desplegar StatefulSet de 3 réplicas (`04-mongo-statefulset.yaml`).
6. Ejecutar inicialización interactiva del Replica Set (`rs.initiate()`) y verificar con `rs.status()`.
7. Ejecutar pruebas de inserción, lectura en réplicas y experimentos de caos.
8. Compilar la documentación a PDF (`python3 scripts/generate_html_pdf.py`).
