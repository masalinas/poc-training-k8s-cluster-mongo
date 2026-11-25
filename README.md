# PoC Training: MongoDB en Kubernetes con StatefulSets

<div align="center">

![Kubernetes](https://img.shields.io/badge/Kubernetes-v1.31-326CE5?logo=kubernetes&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-7.0-47A248?logo=mongodb&logoColor=white)
![Storage](https://img.shields.io/badge/StorageClass-local--path-0ea5e9)
![License](https://img.shields.io/badge/Curso-Capítulo_3-blue)
![Deliverable](https://img.shields.io/badge/PDF-k8s--mongodb--statefulset.pdf-red?logo=adobeacrobatreader)

**Laboratorio Práctico y Guía Oficial:** Despliegue manual de un clúster MongoDB 7.0 (Replica Set `rs0` de 3 miembros), anatomía de red con Headless Services, fricción de seguridad con `keyFile`, y demostración empírica de los límites de orquestación de Kubernetes puro sin Operadores.

</div>

---

## 🎯 Objetivo Pedagógico

El propósito fundamental de este repositorio es **desmitificar la orquestación de bases de datos NoSQL y sistemas de consenso distribuido en Kubernetes**.

En la mayoría de cursos y tutoriales modernos se recurre directamente a herramientas de alto nivel como los **Operadores de Kubernetes** (MongoDB Community Kubernetes Operator o Percona Server for MongoDB Operator). Aunque esta es la recomendación indiscutible para entornos productivos, introduce una barrera didáctica que impide comprender cómo se comportan las primitivas nativas de Kubernetes y cómo interactúan con los motores distribuidos.

A través de este proyecto aprenderás:
1. **El Contrato de Estado (`StatefulSets`):** Identidad determinista por ordinal (`mongodb-0`, `mongodb-1`, `mongodb-2`), despliegue secuencial estricto (`OrderedReady`) y adherencia inmutable de almacenamiento tras reinicios.
2. **Red Dirigida (`Headless Services`):** Por qué un servicio balanceado tradicional es un antipatrón en MongoDB y cómo `clusterIP: None` provee nombres DNS individuales en CoreDNS (`mongodb-X.mongodb-headless.default.svc.cluster.local`) para que los drivers resuelvan la topología dinámica mediante *seedlists*.
3. **Persistencia Dinámica Aislada (`volumeClaimTemplates`):** Creación y enlace automático de discos independientes por cada réplica, integrando un aprovisionador dinámico local (`local-path-provisioner`).
4. **Fricción de Seguridad y Bootstrap (`initContainers`):** Cómo resolver el requisito de permisos estrictos del `keyFile` de MongoDB (`chmod 400`, `chown 999:999`) sobre volúmenes `emptyDir` frente a los Secrets de solo lectura de Kubernetes.
5. **Inicialización Interactiva de Consenso:** Ejecución guiada de `rs.initiate()` con `mongosh` y seguimiento de la transición de estados (`STARTUP` -> `SECONDARY` -> `PRIMARY`).
6. **El Experimento del Caos (Límites de Kubernetes Puro):** 
   - Demostración de auto-elección democrática ante la caída de `mongodb-0` gracias al quórum de 2 de 3 votos.
   - Demostración de auto-degradación a SECONDARY y bloqueo de escrituras ante la pérdida de quórum (caída de 2 de 3 nodos).
   - Demostración del desajuste de escalado (`kubectl scale --replicas=5`) donde Kubernetes añade Pods pero MongoDB los ignora en `rs.conf()`, evidenciando la necesidad real de los Operadores.

---

## ⚖️ Comparativa Conceptual: PostgreSQL vs MongoDB en Kubernetes

| Característica | PostgreSQL (Capítulo 2) | MongoDB (Capítulo 3 / Este Repositorio) |
| :--- | :--- | :--- |
| **Modelo de Datos** | Relacional (RDBMS), SQL estructurado | Documental NoSQL (BSON / JSON) |
| **Topología Mínima** | 2 nodos (Primary `0`, Standby `1`) | **3 nodos** (`mongodb-0`, `1`, `2`) para quórum impar |
| **Mecanismo de Replicación** | Streaming de WAL físico (Write-Ahead Logging) | **Oplog** lógico e idempotente distribuido |
| **Elección de Líder (Failover)** | **No nativa**: La réplica no se autopromueve sola | **Nativa integrada**: Elección Raft-like en segundos |
| **Enrutamiento de Red** | Servicios ClusterIP primario (RW) y réplicas (RO) | **Headless Service exclusivo**; drivers usan *seedlist* |
| **Autenticación Interna** | `pg_hba.conf` + usuario `replicator` | **KeyFile compartido** de 756 bytes (`chmod 400`) |
| **El Dilema sin Operador** | Falta de elección automática y riesgo de **Split-Brain** | **Desfase de escalado** (`kubectl scale` vs `rs.conf()`) y pérdida de quórum |

---

## 🏗️ Diagrama de Arquitectura y Topología

```
                                    APLICACIÓN / CLIENTE MONGODB
                                                 |
                URI: mongodb://mongodb-0.mongodb-headless:27017,mongodb-1.../?replicaSet=rs0
                                                 |
                     +---------------------------+---------------------------+
                     |                           |                           |
                     v                           v                           v
+--------------------+---+  +--------------------+---+  +--------------------+---+
| Pod: mongodb-0         |  | Pod: mongodb-1         |  | Pod: mongodb-2         |
| FQDN:                  |  | FQDN:                  |  | FQDN:                  |
| mongodb-0.mongodb-hdls |  | mongodb-1.mongodb-hdls |  | mongodb-2.mongodb-hdls |
|                        |  |                        |  |                        |
| +--------------------+ |  | +--------------------+ |  | +--------------------+ |
| | initContainer:     | |  | | initContainer:     | |  | | initContainer:     | |
| | init-keyfile       | |  | | init-keyfile       | |  | | init-keyfile       | |
| | - Copia de Secret  | |  | | - Copia de Secret  | |  | | - Copia de Secret  | |
| | - chown 999:999    | |  | | - chown 999:999    | |  | | - chown 999:999    | |
| | - chmod 400        | |  | | - chmod 400        | |  | | - chmod 400        | |
| +--------------------+ |  | +--------------------+ |  | +--------------------+ |
|            |           |  |            |           |  |            |           |
|            v           |  |            v           |  |            v           |
| +--------------------+ |  | +--------------------+ |  | +--------------------+ |
| | Container: mongod  | |  | | Container: mongod  | |  | | Container: mongod  | |
| | - Rol: PRIMARY (RW)| |  | | - Rol: SECONDARY(RO| |  | | - Rol: SECONDARY(RO| |
| | - Escribe en Oplog | |<====== Oplog Sync ========|==| - Replica del Oplog| |
| +--------------------+ |  | +--------------------+ |  | +--------------------+ |
+------------+-----------+  +------------+-----------+  +------------+-----------+
             |                           |                           |
 volumeClaimTemplate: 1Gi    volumeClaimTemplate: 1Gi    volumeClaimTemplate: 1Gi
             v                           v                           v
+------------------------+  +------------------------+  +------------------------+
| PVC: data-mongodb-0    |  | PVC: data-mongodb-1    |  | PVC: data-mongodb-2    |
| /opt/local-path-...    |  | /opt/local-path-...    |  | /opt/local-path-...    |
+------------------------+  +------------------------+  +------------------------+
```

---

## 📁 Estructura del Repositorio

```text
poc-training-k8s-cluster-mongo/
├── manifests/
│   ├── 00-local-path-storage.yaml    # Aprovisionamiento dinámico local (Rancher)
│   ├── 01-mongo-secret.yaml          # Credenciales root y keyFile base64 de 756 bytes
│   ├── 02-mongo-configmap.yaml       # mongod.conf con WiredTiger (0.25GB caché) y seguridad
│   ├── 03-mongo-service.yaml         # Headless Service (clusterIP: None)
│   └── 04-mongo-statefulset.yaml     # StatefulSet (3 réplicas, initContainer keyfile, PVCs)
├── docs/
│   ├── k8s-mongodb-statefulset.md    # Guía técnica hiper-detallada (~970 líneas, 9 capítulos)
│   └── k8s-mongodb-statefulset.html  # Documento editorial A4 maquetado para impresión
├── scripts/
│   └── generate_html_pdf.py          # Pipeline desatendido de compilación a PDF con marcadores
├── openspec/
│   ├── specs/                        # Especificaciones normativas de capacidades activas
│   └── changes/archive/              # Historial de cambios completados y validados
├── k8s-mongodb-statefulset.pdf        # Entregable final en formato PDF profesional (22 páginas)
└── README.md                         # Documento de presentación del proyecto
```

---

## 🚀 Despliegue Rápido del Laboratorio

### 1. Preparar el Almacenamiento Dinámico
```bash
kubectl apply -f manifests/00-local-path-storage.yaml
kubectl get storageclass
```

*(En clústeres de laboratorio de 2 nodos, retirar el taint del Control Plane para que los 3 pods puedan programarse)*:
```bash
kubectl taint nodes --all node-role.kubernetes.io/control-plane- 2>/dev/null || true
```

### 2. Desplegar Secretos y Configuración
```bash
kubectl apply -f manifests/01-mongo-secret.yaml
kubectl apply -f manifests/02-mongo-configmap.yaml
```

### 3. Desplegar Red y StatefulSet
```bash
kubectl apply -f manifests/03-mongo-service.yaml
kubectl apply -f manifests/04-mongo-statefulset.yaml
```

Supervisar el arranque secuencial de las 3 réplicas:
```bash
kubectl get pods -l app=mongodb -w
```

### 4. Inicializar el Replica Set con `mongosh`
Conectarse al pod 0 e inicializar el clúster con sus FQDNs de CoreDNS:
```bash
kubectl exec -it mongodb-0 -- mongosh
```

Ejecutar dentro del shell:
```javascript
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongodb-0.mongodb-headless.default.svc.cluster.local:27017" },
    { _id: 1, host: "mongodb-1.mongodb-headless.default.svc.cluster.local:27017" },
    { _id: 2, host: "mongodb-2.mongodb-headless.default.svc.cluster.local:27017" }
  ]
})
```

Verificar el estado del clúster (`myState: 1` = PRIMARY):
```javascript
rs.status()
```

### 5. Inserción de Datos y Comprobación de Replicación
Dentro de `mongodb-0` (PRIMARY):
```javascript
use escuela_devops
db.alumnos.insertMany([
  { nombre: "Miguel Serrano", modulo: "Kubernetes StatefulSets" },
  { nombre: "Laura Gomez", modulo: "CoreDNS y Headless Services" }
])
exit
```

Comprobar lectura y protección contra escrituras en `mongodb-1` (SECONDARY):
```bash
kubectl exec -it mongodb-1 -- mongosh --eval "use escuela_devops; db.alumnos.find()"
# Intento de inserción en secundario (debe fallar con NotWritablePrimary):
kubectl exec -it mongodb-1 -- mongosh --eval "use escuela_devops; db.alumnos.insertOne({ test: 'fail' })"
```

---

## 💥 Laboratorio de Caos: Límites de Kubernetes Puro

### Experimento 1: Caída de `mongodb-0` y Elección Automática
```bash
kubectl delete pod mongodb-0 --now
# Comprobar que mongodb-1 asciende a PRIMARY en 2-3 segundos por quórum (2 de 3 votos):
kubectl exec -it mongodb-1 -- mongosh --eval "rs.status().members.map(m => ({ name: m.name.split('.')[0], stateStr: m.stateStr }))"
```

### Experimento 2: Pérdida de Quórum (Caen 2 de 3 nodos)
```bash
kubectl delete pod mongodb-1 mongodb-2 --now
# Comprobar que mongodb-0 se auto-degrada a SECONDARY y bloquea escrituras por falta de mayoría:
kubectl exec -it mongodb-0 -- mongosh --eval "rs.status().members.map(m => ({ name: m.name.split('.')[0], stateStr: m.stateStr }))"
```

### Experimento 3: Desfase de Escalado (`kubectl scale` vs `rs.conf()`)
```bash
kubectl scale statefulset mongodb --replicas=5
kubectl get pods -l app=mongodb
# Kubernetes levanta mongodb-3 y mongodb-4, pero MongoDB los ignora completamente:
kubectl exec -it mongodb-0 -- mongosh --eval "rs.status().members.map(m => m.name.split('.')[0])"
```

---

## 📄 Compilación de la Guía PDF

El entregable oficial [`k8s-mongodb-statefulset.pdf`](file:///home/miguel/git/poc-training-k8s-cluster-mongo/k8s-mongodb-statefulset.pdf) está precompilado en la raíz del repositorio. Para regenerarlo:

```bash
python3 scripts/generate_html_pdf.py
```

* **Dependencias:** Python 3, `pypdf`, `markdown`, y Google Chrome / Chromium.
* **Características:** Maquetación editorial A4 (Inter, JetBrains Mono), reglas `@page` con numeración y pie de página, bloques de código con ajuste de línea, y árbol de marcadores navegables en el panel lateral para los 9 capítulos.
