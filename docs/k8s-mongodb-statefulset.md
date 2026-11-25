# Guía Práctica de MongoDB en Kubernetes con StatefulSets
## Despliegue Manual de Alta Disponibilidad con Replica Set, Anatomía de Red y el Dilema de Orquestación sin Operadores

**Autor:** Equipo Docente de Kubernetes y Arquitectura de Datos  
**Documento Oficial del Curso:** Capítulo 3 - Gestión de Cargas con Estado NoSQL y Consenso Distribuido  
**Entregable:** `k8s-mongodb-statefulset.pdf`

---

## Tabla de Contenidos

1. [Fundamentos y Arquitectura de Estado en Kubernetes](#1-fundamentos-y-arquitectura-de-estado-en-kubernetes)
   - [1.1 El Contrato de Estado: Deployment vs StatefulSet](#11-el-contrato-de-estado-deployment-vs-statefulset)
   - [1.2 Diagrama de Topología y Flujo de Replicación del Replica Set](#12-diagrama-de-topología-y-flujo-de-replicación-del-replica-set)
   - [1.3 Matriz de Componentes del Clúster](#13-matriz-de-componentes-del-clúster)
2. [Preparación del Almacenamiento Dinámico (StorageClass)](#2-preparación-del-almacenamiento-dinámico-storageclass)
   - [2.1 El Problema del Almacenamiento en Clústeres Kubeadm / Bare-Metal](#21-el-problema-del-almacenamiento-en-clústeres-kubeadm--bare-metal)
   - [2.2 Despliegue de Rancher `local-path-provisioner`](#22-despliegue-de-rancher-local-path-provisioner)
   - [2.3 Verificación de la StorageClass por Defecto](#23-verificación-de-la-storageclass-por-defecto)
   - [2.4 Ajuste de Tolerancias del Nodo Master (Control Plane)](#24-ajuste-de-tolerancias-del-nodo-master-control-plane)
3. [Configuración Base y Gestión de Credenciales](#3-configuración-base-y-gestión-de-credenciales)
   - [3.1 Secret de Autenticación para Superusuario y Clúster KeyFile](#31-secret-de-autenticación-para-superusuario-y-clúster-keyfile)
   - [3.2 ConfigMap con `mongod.conf` (WiredTiger, Replicación y Seguridad)](#32-configmap-con-mongodconf-wiredtiger-replicación-y-seguridad)
4. [La Capa de Red: Headless Service y el Paradigma de Conexión de MongoDB](#4-la-capa-de-red-headless-service-y-el-paradigma-de-conexión-de-mongodb)
   - [4.1 Por qué un Servicio Estándar no Sirve: El Headless Service (`clusterIP: None`)](#41-por-qué-un-servicio-estándar-no-sirve-el-headless-service-clusterip-none)
   - [4.2 Resolución DNS Individual por Pod en CoreDNS](#42-resolución-dns-individual-por-pod-en-coredns)
   - [4.3 El Antipatrón del Servicio Primario Estático y el Rol de los Drivers (Seedlist)](#43-el-antipatrón-del-servicio-primario-estático-y-el-rol-de-los-drivers-seedlist)
5. [Despliegue del StatefulSet y Mecánica del InitContainer](#5-despliegue-del-statefulset-y-mecánica-del-initcontainer)
   - [5.1 Anatomía del StatefulSet: `replicas: 3`, `serviceName` y `OrderedReady`](#51-anatomía-del-statefulset-replicas-3-servicename-y-orderedready)
   - [5.2 Aislamiento de Volúmenes con `volumeClaimTemplates`](#52-aislamiento-de-volúmenes-con-volumeclaimtemplates)
   - [5.3 Desmontando la Fricción de Seguridad: El InitContainer para el `keyFile` (`chmod 400`)](#53-desmontando-la-fricción-de-seguridad-el-initcontainer-para-el-keyfile-chmod-400)
   - [5.4 Despliegue Secuencial y Seguimiento del Arranque](#54-despliegue-secuencial-y-seguimiento-del-arranque)
6. [Inicialización Guiada y Verificación del Replica Set](#6-inicialización-guiada-y-verificación-del-replica-set)
   - [6.1 Acceso Interactivo con `mongosh` al Pod Inicial (`mongodb-0`)](#61-acceso-interactivo-con-mongosh-al-pod-inicial-mongodb-0)
   - [6.2 Inicialización del Replica Set (`rs.initiate()`) paso a paso con FQDNs](#62-inicialización-del-replica-set-rsinitiate-paso-a-paso-con-fqdns)
   - [6.3 Creación de Base de Datos, Colección y Documentos de Prueba](#63-creación-de-base-de-datos-colección-y-documentos-de-prueba)
   - [6.4 Validación de Replicación Oplog en Secundarios, Lectura y Protección contra Escrituras](#64-validación-de-replicación-oplog-en-secundarios-lectura-y-protección-contra-escrituras)
7. [El Experimento del Caos: Resiliencia y Límites de Kubernetes Puro](#7-el-experimento-del-caos-resiliencia-y-límites-de-kubernetes-puro)
   - [7.1 Fase 1: Caída del Nodo Primario (`mongodb-0`) y Elección Automática por Quórum](#71-fase-1-caída-del-nodo-primario-mongodb-0-y-elección-automática-por-quórum)
   - [7.2 Fase 2: Simulación de Pérdida de Quórum (Caída de 2 de 3 nodos) y Auto-Degradación](#72-fase-2-simulación-de-pérdida-de-quórum-caída-de-2-de-3-nodos-y-auto-degradación)
   - [7.3 Fase 3: El Dilema del Escalado en StatefulSets (`kubectl scale` a 5 réplicas vs `rs.conf()`)](#73-fase-3-el-dilema-del-escalado-en-statefulsets-kubectl-scale-a-5-réplicas-vs-rsconf)
   - [7.4 Por qué las Primitivas Nativas no Pueden Resolver la Gestión del Ciclo de Vida](#74-por-qué-las-primitivas-nativas-no-pueden-resolver-la-gestión-del-ciclo-de-vida)
8. [La Brecha hacia la Producción: Por Qué Usamos Operadores](#8-la-brecha-hacia-la-producción-por-qué-usamos-operadores)
   - [8.1 Matriz Comparativa: StatefulSet Manual vs. Operadores de Producción](#81-matriz-comparativa-statefulset-manual-vs-operadores-de-producción)
   - [8.2 Capacidades Esenciales de un Operador (MongoDB Community Operator y Percona PSMDB)](#82-capacidades-esenciales-de-un-operador-mongodb-community-operator-y-percona-psmdb)
9. [Resolución de Problemas Frecuentes (Troubleshooting)](#9-resolución-de-problemas-frecuentes-troubleshooting)
   - [9.1 Error 1: Permisos Abiertos en Keyfile (`permissions on keyfile are too open`)](#91-error-1-permisos-abiertos-en-keyfile-permissions-on-keyfile-are-too-open)
   - [9.2 Error 2: Operación Rechazada en Secundario (`NotWritablePrimary`)](#92-error-2-operación-rechazada-en-secundario-notwritableprimary)
   - [9.3 Error 3: Pods en `Pending` por Ausencia de StorageClass o Taints](#93-error-3-pods-en-pending-por-ausencia-de-storageclass-o-taints)
   - [9.4 Error 4: Fallo de Resolución DNS durante `rs.initiate()`](#94-error-4-fallo-de-resolución-dns-durante-rsinitiate)

---

## 1. Fundamentos y Arquitectura de Estado en Kubernetes

### 1.1 El Contrato de Estado: Deployment vs StatefulSet

En la computación nativa en la nube, las aplicaciones web y APIs son predominantemente **apátridas** (*stateless*). Para este tipo de cargas de trabajo, el controlador idóneo en Kubernetes es el `Deployment`. Un `Deployment` asume que:
* Todos los Pods son idénticos e intercambiables entre sí.
* Los Pods reciben identificadores con cadenas hash aleatorias (por ejemplo, `api-79b8f645d-9kx2l`).
* El arranque, reinicio y escalado de Pods se ejecuta concurrentemente sin un orden determinista.
* Si un Pod es destruido, el nuevo Pod resultante no conserva ninguna identidad de red ni afinidad estricta con el volumen previo.

Por el contrario, los sistemas de bases de datos distribuidas con consenso como **MongoDB** son sistemas de **fuerte acoplamiento de estado** (*stateful*). Cada nodo cumple un rol en el clúster (nodo Primario para escrituras y lecturas, o nodos Secundarios para replicación y lectura distribuida), y requiere una identidad que no cambie jamás tras un reinicio.

```
+-----------------------------------------------------------------------------------------+
|                  COMPARATIVA DE IDENTIDAD: DEPLOYMENT VS STATEFULSET                    |
+-------------------------+--------------------------------+------------------------------+
|  Característica         | Deployment (Stateless)         | StatefulSet (Stateful)       |
+-------------------------+--------------------------------+------------------------------+
|  Identidad de Red       | Efímera y aleatoria            | Determinista y Fija          |
|                         | (api-6bf9d7c8-4z9q)            | (mongodb-0, mongodb-1, ...)  |
+-------------------------+--------------------------------+------------------------------+
|  Orden de Despliegue    | Concurrente / Arbitrario       | Secuencial y Estricto        |
|                         | (Todos a la vez)               | (0 -> 1 -> 2 ...)            |
+-------------------------+--------------------------------+------------------------------+
|  Almacenamiento (PVC)   | Compartido o Efímero           | 1 PVC dedicado por Réplica   |
|                         | (Todos leen del mismo disco)   | (data-mongodb-0, ...)        |
+-------------------------+--------------------------------+------------------------------+
|  Enlace tras Reinicio   | Nuevo Pod = Volumen nuevo      | Nuevo Pod = Se re-vincula al |
|                         | o no determinista              | MISMO volumen persistente    |
+-------------------------+--------------------------------+------------------------------+
```

El controlador **`StatefulSet`** garantiza tres invariantes indispensables para MongoDB:
1. **Identidad de Red Estable:** Cada Pod recibe un ordinal secuencial `[0, 1, 2]`. El primer Pod siempre será `mongodb-0`, el segundo `mongodb-1` y el tercero `mongodb-2`.
2. **Ciclo de Vida Secuencial (`OrderedReady`):** Kubernetes no inicia `mongodb-1` hasta que `mongodb-0` esté en estado `Running` y haya superado sus *Readiness Probes*.
3. **Almacenamiento Adherente (`volumeClaimTemplates`):** Cada réplica dispone de su propio volumen dinámico. Si el nodo físico donde reside `mongodb-0` se reinicia, el nuevo Pod `mongodb-0` volverá a reclamar exactamente el PVC `data-mongodb-0`.

---

### 1.2 Diagrama de Topología y Flujo de Replicación del Replica Set

A continuación se detalla la arquitectura que implementaremos paso a paso en este laboratorio:

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

### 1.3 Matriz de Componentes del Clúster

Para conseguir que este clúster opere sin operadores ni software externo, coordinamos cinco recursos nativos de Kubernetes:

| Recurso Kubernetes | Nombre | Namespace | Función Pedagógica Principal |
| :--- | :--- | :--- | :--- |
| **StorageClass** | `local-path` | Clúster | Aprovisionamiento dinámico local sobre el sistema de archivos del nodo anfitrión (`/opt/local-path-provisioner`). |
| **Secret** | `mongo-secret` | `default` | Almacenamiento seguro de credenciales de superusuario (`admin`) y archivo `keyfile` criptográfico para autenticación de Replica Set. |
| **ConfigMap** | `mongo-config` | `default` | Archivo declarativo `mongod.conf` con parámetros de almacenamiento WiredTiger, límite de caché, puerto y replicación. |
| **Service (Headless)**| `mongodb-headless`| `default` | `clusterIP: None`. Provee nombres DNS directos y estables para cada Pod en CoreDNS (`mongodb-X.mongodb-headless`). |
| **StatefulSet** | `mongodb` | `default` | Orquesta las 3 réplicas, ejecuta el `initContainer` de seguridad y reclama volúmenes dedicados. |

---

## 2. Preparación del Almacenamiento Dinámico (StorageClass)

### 2.1 El Problema del Almacenamiento en Clústeres Kubeadm / Bare-Metal

En servicios gestionados en la nube pública (como Google Kubernetes Engine - GKE, AWS EKS o Azure AKS), el proveedor incluye de fábrica un controlador CSI (*Container Storage Interface*) que aprovisiona automáticamente discos virtuales cuando se solicita un PVC.

Sin embargo, en un clúster instalado desde cero mediante `kubeadm` (como el configurado en máquinas virtuales Ubuntu), **no existe ningún aprovisionador de almacenamiento configurado por defecto**. 

> [!WARNING]
> Si intentas aplicar un `StatefulSet` con `volumeClaimTemplates` en un clúster Kubeadm sin StorageClass, los PVCs quedarán congelados en estado `Pending` con el evento:
> `waiting for a volume to be created, either by dynamic provisioning or by manually creating a PersistentVolume`.

Para resolver esto en entornos de laboratorio de manera ligera y confiable, utilizaremos **Rancher `local-path-provisioner`**. Este controlador escucha eventos de creación de PVCs y crea automáticamente carpetas dedicadas en el sistema de archivos del nodo físico (`/opt/local-path-provisioner`), vinculándolas de forma transparente como un `PersistentVolume` con modo de acceso `ReadWriteOnce`.

---

### 2.2 Despliegue de Rancher `local-path-provisioner`

El archivo [`manifests/00-local-path-storage.yaml`](file:///home/miguel/git/poc-training-k8s-cluster-mongo/manifests/00-local-path-storage.yaml) contiene la definición completa: ServiceAccount, ClusterRoles con permisos de gestión de volumen, ConfigMap con scripts de montaje (`setup`/`teardown`), el Deployment del controlador y el objeto `StorageClass`.

Aplicamos el aprovisionador con el siguiente comando:

```bash
kubectl apply -f manifests/00-local-path-storage.yaml
```

**Salida esperada:**
```text
namespace/local-path-storage created
serviceaccount/local-path-provisioner-service-account created
clusterrole.rbac.authorization.k8s.io/local-path-provisioner-role created
clusterrolebinding.rbac.authorization.k8s.io/local-path-provisioner-bind created
configmap/local-path-config created
deployment.apps/local-path-provisioner created
storageclass.storage.k8s.io/local-path created
```

---

### 2.3 Verificación de la StorageClass por Defecto

Verificamos que el StorageClass está disponible y configurado como el aprovisionador predeterminado (`(default)`):

```bash
kubectl get storageclass
```

**Salida esperada:**
```text
NAME                   PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
local-path (default)   rancher.io/local-path   Delete          WaitForFirstConsumer   false                  15s
```

Comprobamos que el Pod del aprovisionador está en ejecución:

```bash
kubectl get pods -n local-path-storage
```

**Salida esperada:**
```text
NAME                                      READY   STATUS    RESTARTS   AGE
local-path-provisioner-6795b5f9d8-m7q2b   1/1     Running   0          25s
```

---

### 2.4 Ajuste de Tolerancias del Nodo Master (Control Plane)

En un entorno de formación con recursos acotados (por ejemplo, un clúster de dos máquinas virtuales: `k8s-master` y `k8s-worker`), el nodo Master posee por defecto un *Taint* que impide la ejecución de cargas de trabajo de usuario:

```text
node-role.kubernetes.io/control-plane:NoSchedule
```

Dado que desplegaremos un Replica Set de **3 Pods**, y un único worker de 2 GB de RAM se vería sobrecargado, retiramos el *Taint* del nodo Master para que ambos nodos puedan alojar réplicas:

```bash
kubectl taint nodes --all node-role.kubernetes.io/control-plane- 2>/dev/null || true
```

**Salida esperada:**
```text
node/k8s-master untainted
```

---

## 3. Configuración Base y Gestión de Credenciales

### 3.1 Secret de Autenticación para Superusuario y Clúster KeyFile

A diferencia de PostgreSQL (que utiliza `pg_hba.conf` y contraseñas por usuario), MongoDB exige dos capas de seguridad distintas:
1. **Autenticación de Aplicaciones y Usuarios:** Usuario administrativo (`admin`) y contraseña de superusuario (`MONGO_INITDB_ROOT_PASSWORD`).
2. **Autenticación Interna entre Nodos (*Internal Membership Authentication*):** Todos los miembros de un Replica Set deben compartir un archivo criptográfico idéntico denominado **`keyFile`**. Este archivo actúa como una clave compartida (*pre-shared key*) que cifra y autentica los mensajes del protocolo de replicación y las votaciones de quórum.

Generamos la clave interna de 756 bytes mediante `openssl` y creamos el archivo [`manifests/01-mongo-secret.yaml`](file:///home/miguel/git/poc-training-k8s-cluster-mongo/manifests/01-mongo-secret.yaml):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mongo-secret
  namespace: default
type: Opaque
stringData:
  MONGO_INITDB_ROOT_USERNAME: "admin"
  MONGO_INITDB_ROOT_PASSWORD: "MongoSecret2026!"
  keyfile: |
    MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC7rWJ2qU9xQ2L0
    ... (clave de 756 bytes) ...
```

Aplicamos el Secret en el clúster:

```bash
kubectl apply -f manifests/01-mongo-secret.yaml
```

**Salida esperada:**
```text
secret/mongo-secret created
```

---

### 3.2 ConfigMap con `mongod.conf` (WiredTiger, Replicación y Seguridad)

Kubernetes nos permite desacoplar la configuración del motor de base de datos utilizando un `ConfigMap`. El archivo [`manifests/02-mongo-configmap.yaml`](file:///home/miguel/git/poc-training-k8s-cluster-mongo/manifests/02-mongo-configmap.yaml) define el archivo de configuración estándar de MongoDB:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mongo-config
  namespace: default
data:
  mongod.conf: |
    storage:
      dbPath: /data/db
      journal:
        enabled: true
      wiredTiger:
        engineConfig:
          cacheSizeGB: 0.25

    net:
      port: 27017
      bindIpAll: true

    replication:
      replSetName: rs0

    security:
      keyFile: /etc/mongo-keyfile/keyfile
      authorization: enabled
```

> [!TIP]
> **Optimización de Memoria:** Por defecto, el motor WiredTiger intenta consumir el 50% de la RAM del host menos 1 GB. En un entorno de máquinas virtuales compartidas, 3 Pods de MongoDB consumirían rápidamente toda la memoria disponible, provocando el desalojo de contenedores por `OOMKilled`. El parámetro `wiredTiger.engineConfig.cacheSizeGB: 0.25` limita la caché a 256 MB por instancia, garantizando total estabilidad.

Aplicamos el ConfigMap:

```bash
kubectl apply -f manifests/02-mongo-configmap.yaml
```

**Salida esperada:**
```text
configmap/mongo-config created
```

---

## 4. La Capa de Red: Headless Service y el Paradigma de Conexión de MongoDB

### 4.1 Por qué un Servicio Estándar no Sirve: El Headless Service (`clusterIP: None`)

Un `Service` normal de Kubernetes asigna una dirección IP virtual (`ClusterIP`) y actúa como un balanceador de carga de nivel 4 (L4) distribuyendo paquetes TCP de forma aleatoria o round-robin entre los Pods detrás del selector.

Este comportamiento es inútil para la replicación de MongoDB:
* Los miembros del Replica Set necesitan comunicarse punto a punto con cada nodo específico para comprobar latidos (*heartbeats*), consultar el Oplog y emitir votos.
* Si un nodo intentara sincronizarse con una IP virtual balanceada, cada paquete TCP llegaría a un miembro aleatorio diferente, rompiendo la coherencia de estado.

Para resolver esto, creamos un **Headless Service** especificando explícitamente `clusterIP: None` en [`manifests/03-mongo-service.yaml`](file:///home/miguel/git/poc-training-k8s-cluster-mongo/manifests/03-mongo-service.yaml):

```yaml
apiVersion: v1
kind: Service
metadata:
  name: mongodb-headless
  namespace: default
  labels:
    app: mongodb
spec:
  clusterIP: None
  ports:
    - name: mongodb
      port: 27017
      targetPort: 27017
  selector:
    app: mongodb
```

Aplicamos el servicio de red:

```bash
kubectl apply -f manifests/03-mongo-service.yaml
```

**Salida esperada:**
```text
service/mongodb-headless created
```

---

### 4.2 Resolución DNS Individual por Pod en CoreDNS

Al combinar un `StatefulSet` (`serviceName: mongodb-headless`) con un Headless Service, el servidor CoreDNS de Kubernetes crea de forma automática registros DNS de tipo `A` que vinculan cada Pod individual con su nombre ordinal:

```text
<nombre-pod>.<nombre-servicio>.<namespace>.svc.<dominio-cluster>
```

Para nuestro clúster, los tres nombres de dominio completos (FQDN) generados son:
1. `mongodb-0.mongodb-headless.default.svc.cluster.local`
2. `mongodb-1.mongodb-headless.default.svc.cluster.local`
3. `mongodb-2.mongodb-headless.default.svc.cluster.local`

Estos FQDNs son deterministas y permanentes: si el Pod `mongodb-1` muere y es recreado en otro nodo con una IP completamente distinta, CoreDNS actualizará el registro DNS apuntando a la nueva IP, preservando la identidad del miembro del clúster sin necesidad de reconfigurar MongoDB.

---

### 4.3 El Antipatrón del Servicio Primario Estático y el Rol de los Drivers (Seedlist)

En arquitecturas tradicionales como PostgreSQL, es habitual definir un servicio `postgresql-primary` con selector fijo a `statefulset.kubernetes.io/pod-name: postgresql-0`.

> [!CAUTION]
> **¡Crear un servicio de Kubernetes estático para el Primario en MongoDB es un grave error de diseño!**  
> En MongoDB, el liderazgo es dinámico y democrático: cualquier réplica puede ser elegida PRIMARY ante una caída o mantenimiento. Si crearas un Service apuntando fijamente a `mongodb-0`, cuando `mongodb-1` ascienda a Primario, tu aplicación continuaría enviando escrituras a `mongodb-0` (que ahora es secundario o está caído), recibiendo el error fatal:  
> `MongoServerError: NotWritablePrimary`.

Los drivers oficiales de MongoDB (Node.js, Python PyMongo, Java, Go, etc.) implementan el protocolo SDAM (*Server Discovery and Monitoring*). La aplicación se conecta utilizando una **cadena de conexión de Replica Set con lista de semillas (*seedlist*)**:

```text
mongodb://mongodb-0.mongodb-headless:27017,mongodb-1.mongodb-headless:27017,mongodb-2.mongodb-headless:27017/?replicaSet=rs0
```

1. El driver se conecta a cualquiera de las semillas disponibles.
2. Ejecuta el comando `hello` (antiguamente `isMaster`).
3. El clúster le responde con la topología completa y le informa **quién es el PRIMARY en ese instante exacto**.
4. El driver enruta automáticamente todas las operaciones de escritura directamente al PRIMARY actual. Si ocurre una elección y el Primario cambia, el driver detecta el cambio en milisegundos y redirige el tráfico sin reiniciar la aplicación.

---

## 5. Despliegue del StatefulSet y Mecánica del InitContainer

### 5.1 Anatomía del StatefulSet: `replicas: 3`, `serviceName` y `OrderedReady`

El archivo [`manifests/04-mongo-statefulset.yaml`](file:///home/miguel/git/poc-training-k8s-cluster-mongo/manifests/04-mongo-statefulset.yaml) reúne la configuración completa del clúster:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongodb
  namespace: default
spec:
  serviceName: mongodb-headless
  replicas: 3
  podManagementPolicy: OrderedReady
  selector:
    matchLabels:
      app: mongodb
...
```

* `serviceName: mongodb-headless`: Asocia la identidad de red de los Pods con el Headless Service definido anteriormente.
* `replicas: 3`: Despliega el quórum electoral mínimo necesario para soportar la caída de 1 nodo sin perder el servicio de escritura.
* `podManagementPolicy: OrderedReady`: Orden de despliegue estricto. El Pod `mongodb-1` no comenzará su arranque hasta que `mongodb-0` haya superado sus pruebas de salud (*readiness*).

---

### 5.2 Aislamiento de Volúmenes con `volumeClaimTemplates`

A diferencia de un Deployment (donde todos los Pods compartirían un volumen NFS con graves riesgos de corrupción en motores transaccionales), el `StatefulSet` utiliza `volumeClaimTemplates`:

```yaml
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes:
          - ReadWriteOnce
        storageClassName: local-path
        resources:
          requests:
            storage: 1Gi
```

Kubernetes creará automáticamente un PVC independiente por cada ordinal:
* `data-mongodb-0`
* `data-mongodb-1`
* `data-mongodb-2`

Cada PVC quedará vinculado dinámicamente a una carpeta local en el nodo anfitrión gestionada por `local-path-provisioner`.

---

### 5.3 Desmontando la Fricción de Seguridad: El InitContainer para el `keyFile` (`chmod 400`)

MongoDB aplica una política estricta de seguridad en el archivo `keyFile`:
> *The keyfile must contain between 6 and 1024 characters and have permissions of 400 or 600 (read-only for owner). Permissions more permissive than 600 will cause mongod to reject the file on startup.*

En Kubernetes, cuando montas un objeto `Secret` como volumen, el sistema de archivos virtual de Kubelet lo monta por defecto perteneciente a `root` y con permisos de lectura para el grupo (`0644`). Si inicias `mongod` apuntando directamente a ese Secret montado, el proceso aborta inmediatamente con:

```text
Fatal Assertion 16996: permissions on /etc/mongo-keyfile/keyfile are too open: 0644
```

Para solucionar este dilema de manera 100% nativa en Kubernetes, incorporamos un **`initContainer`** (`init-keyfile`) con un volumen temporal `emptyDir`:

```yaml
      initContainers:
        - name: init-keyfile
          image: busybox:1.36
          command:
            - sh
            - -c
            - |
              set -e
              echo "==> [INIT] Copiando keyfile desde Secret al volumen compartido..."
              cp /tmp/raw-keyfile/keyfile /etc/mongo-keyfile/keyfile
              echo "==> [INIT] Ajustando propietario a mongodb (999:999) y permisos a 0400..."
              chown 999:999 /etc/mongo-keyfile/keyfile
              chmod 400 /etc/mongo-keyfile/keyfile
              ls -la /etc/mongo-keyfile/keyfile
              echo "==> [INIT] Keyfile preparado exitosamente."
          volumeMounts:
            - name: raw-keyfile
              mountPath: /tmp/raw-keyfile
              readOnly: true
            - name: mongo-keyfile
              mountPath: /etc/mongo-keyfile
```

1. El Secret de sólo lectura se monta en `/tmp/raw-keyfile`.
2. El contenedor auxiliar `busybox` copia el archivo al volumen `emptyDir` montado en `/etc/mongo-keyfile`.
3. Aplica `chown 999:999` (el UID de usuario `mongodb`) y `chmod 400`.
4. El contenedor principal `mongod` arranca y lee el archivo con los permisos exactos que exige el motor.

---

### 5.4 Despliegue Secuencial y Seguimiento del Arranque

Aplicamos el StatefulSet en el clúster:

```bash
kubectl apply -f manifests/04-mongo-statefulset.yaml
```

**Salida esperada:**
```text
statefulset.apps/mongodb created
```

Supervisamos el arranque ordenado de los tres Pods:

```bash
kubectl get pods -l app=mongodb -w
```

**Salida esperada:**
```text
NAME        READY   STATUS     RESTARTS   AGE
mongodb-0   0/1     Init:0/1   0          5s
mongodb-0   0/1     PodInitializing   0   12s
mongodb-0   1/1     Running           0   18s
mongodb-1   0/1     Init:0/1          0   20s
mongodb-1   1/1     Running           0   35s
mongodb-2   0/1     Init:0/1          0   37s
mongodb-2   1/1     Running           0   52s
```

Comprobamos los registros del `initContainer` en `mongodb-0`:

```bash
kubectl logs mongodb-0 -c init-keyfile
```

**Salida esperada:**
```text
==> [INIT] Copiando keyfile desde Secret al volumen compartido...
==> [INIT] Ajustando propietario a mongodb (999:999) y permisos a 0400...
-r--------    1 999      999            756 Nov 25 18:00 /etc/mongo-keyfile/keyfile
==> [INIT] Keyfile preparado exitosamente.
```

Verificamos que los 3 volúmenes persistentes se han creado y vinculado (`Bound`):

```bash
kubectl get pvc -l app=mongodb
```

**Salida esperada:**
```text
NAME             STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
data-mongodb-0   Bound    pvc-3a1b8c2d-1111-2222-3333-444455556666   1Gi        RWO            local-path     1m
data-mongodb-1   Bound    pvc-7e8f9a0b-2222-3333-4444-555566667777   1Gi        RWO            local-path     50s
data-mongodb-2   Bound    pvc-1c2d3e4f-3333-4444-5555-666677778888   1Gi        RWO            local-path     30s
```

---

## 6. Inicialización Guiada y Verificación del Replica Set

En este instante, los tres procesos `mongod` están en ejecución, pero están en estado no inicializado, esperando formar parte de un Replica Set. Procederemos a inicializar el clúster interactivamente con `mongosh`.

### 6.1 Acceso Interactivo con `mongosh` al Pod Inicial (`mongodb-0`)

Nos conectamos mediante el shell oficial moderno `mongosh` al contenedor `mongodb-0`:

```bash
kubectl exec -it mongodb-0 -- mongosh
```

**Salida esperada:**
```text
Current Mongosh Log ID:	6744b2f1e29c81234567890a
Connecting to:		mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000
Using MongoDB:		7.0.14
Using Mongosh:		2.3.1

test>
```

---

### 6.2 Inicialización del Replica Set (`rs.initiate()`) paso a paso con FQDNs

Dentro de la sesión de `mongosh` en `mongodb-0`, ejecutamos el comando de inicialización pasando explícitamente los nombres FQDN de CoreDNS para los tres miembros:

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

**Salida esperada:**
```json
{ "ok": 1 }
```

Tras presionar Enter, el prompt de la consola cambiará automáticamente:
* Primero mostrará: `rs0 [direct: secondary] test>`
* Y tras 2-3 segundos, una vez finalizada la auto-elección inicial: `rs0 [direct: primary] test>`

Comprobamos el estado del quórum y los miembros con `rs.status()`:

```javascript
rs.status()
```

**Salida observada (Campos clave de consenso):**
```json
{
  "set": "rs0",
  "date": ISODate("2026-11-25T18:05:00.000Z"),
  "myState": 1,
  "term": Long("1"),
  "members": [
    {
      "_id": 0,
      "name": "mongodb-0.mongodb-headless.default.svc.cluster.local:27017",
      "health": 1,
      "state": 1,
      "stateStr": "PRIMARY"
    },
    {
      "_id": 1,
      "name": "mongodb-1.mongodb-headless.default.svc.cluster.local:27017",
      "health": 1,
      "state": 2,
      "stateStr": "SECONDARY"
    },
    {
      "_id": 2,
      "name": "mongodb-2.mongodb-headless.default.svc.cluster.local:27017",
      "health": 1,
      "state": 2,
      "stateStr": "SECONDARY"
    }
  ],
  "ok": 1
}
```

¡El Replica Set está activo, coordinado y sincronizado!

---

### 6.3 Creación de Base de Datos, Colección y Documentos de Prueba

Sin salir de `mongosh` en el nodo PRIMARY (`mongodb-0`), creamos una base de datos formativa e insertamos documentos:

```javascript
use escuela_devops

db.alumnos.insertMany([
  { nombre: "Miguel Serrano", modulo: "Kubernetes StatefulSets", fecha: new Date() },
  { nombre: "Laura Gomez", modulo: "CoreDNS y Headless Services", fecha: new Date() },
  { nombre: "Carlos Fernandez", modulo: "Consenso Distribuido MongoDB", fecha: new Date() }
])

db.alumnos.find()
```

**Salida esperada:**
```text
{ acknowledged: true, insertedIds: { '0': ObjectId("..."), '1': ObjectId("..."), '2': ObjectId("...") } }
[
  { _id: ObjectId("..."), nombre: 'Miguel Serrano', modulo: 'Kubernetes StatefulSets', fecha: ... },
  { _id: ObjectId("..."), nombre: 'Laura Gomez', modulo: 'CoreDNS y Headless Services', fecha: ... },
  { _id: ObjectId("..."), nombre: 'Carlos Fernandez', modulo: 'Consenso Distribuido MongoDB', fecha: ... }
]
```

Salimos con `exit`.

---

### 6.4 Validación de Replicación Oplog en Secundarios, Lectura y Protección contra Escrituras

Accedemos interactivamente al nodo secundario `mongodb-1`:

```bash
kubectl exec -it mongodb-1 -- mongosh
```

**Salida esperada:**
```text
rs0 [direct: secondary] test>
```

Intentamos consultar los datos insertados en el Primario:

```javascript
use escuela_devops
db.alumnos.find()
```

> [!NOTE]
> En versiones modernas de `mongosh` (2.x+), el shell activa automáticamente la preferencia de lectura secundaria si te conectas en modo directo a un nodo secundario. Verás los 3 documentos inmediatamente, demostrando que el **Oplog** se ha sincronizado en tiempo real.

Ahora intentamos realizar una escritura en el nodo Secundario:

```javascript
db.alumnos.insertOne({ nombre: "Intruso", modulo: "Prueba Fallida" })
```

**Salida esperada (Rechazo Inmediato del Motor):**
```text
MongoServerError: NotWritablePrimary
```

MongoDB protege de manera estricta la coherencia de datos: **solo el nodo PRIMARY tiene potestad de escribir en el almacenamiento**.

Salimos con `exit`.

---

## 7. El Experimento del Caos: Resiliencia y Límites de Kubernetes Puro

Llegamos al núcleo analítico del laboratorio. Hemos desplegado un clúster de base de datos con alta disponibilidad y replicación activa utilizando únicamente primitivas nativas de Kubernetes... **¿Por qué entonces la industria desaconseja operar bases de datos en producción sin un Operador?**

Vamos a someter al clúster a tres escenarios de fallo para descubrirlo.

---

### 7.1 Fase 1: Caída del Nodo Primario (`mongodb-0`) y Elección Automática por Quórum

A diferencia de PostgreSQL (donde la réplica queda paralizada en solo lectura y no sabe ascender sola), MongoDB cuenta con un algoritmo de elección de líder integrado basado en consenso.

Simulamos la destrucción fulminante del nodo Primario actual (`mongodb-0`):

```bash
kubectl delete pod mongodb-0 --now
```

**Salida esperada:**
```text
pod "mongodb-0" deleted
```

Inmediatamente, nos conectamos al Pod `mongodb-1` y observamos su prompt:

```bash
kubectl exec -it mongodb-1 -- mongosh --eval "rs.status().members.map(m => ({ name: m.name.split('.')[0], stateStr: m.stateStr }))"
```

**Salida observada:**
```json
[
  { "name": "mongodb-0", "stateStr": "(not reachable/healthy)" },
  { "name": "mongodb-1", "stateStr": "PRIMARY" },
  { "name": "mongodb-2", "stateStr": "SECONDARY" }
]
```

**¿Qué ha ocurrido?**
1. `mongodb-1` y `mongodb-2` detectaron la ausencia de latidos (*heartbeats*) de `mongodb-0`.
2. Como hay 3 nodos configurados en el clúster, la mayoría estricta para formar quórum es:
   $$\text{Quórum} = \left\lfloor \frac{3}{2} \right\rfloor + 1 = 2 \text{ votos}$$
3. Los nodos 1 y 2 reunieron 2 votos sobre 3 (`66.6% > 50%`).
4. Iniciaron una elección y **promovieron democráticamente a `mongodb-1` como nuevo PRIMARY en menos de 3 segundos**.
5. Mientras tanto, el controlador StatefulSet de Kubernetes volvió a arrancar el contenedor `mongodb-0`, re-vinculó su PVC `data-mongodb-0`, y cuando `mongodb-0` despertó, descubrió que había un nuevo Primario legítimo y se incorporó pacíficamente como `SECONDARY`.

---

### 7.2 Fase 2: Simulación de Pérdida de Quórum (Caída de 2 de 3 nodos) y Auto-Degradación

Ahora provocamos un fallo de mayor envergadura: simulamos la pérdida simultánea de dos nodos (por ejemplo, corte de red o caída física de un hipervisor con dos VMs).

Escalamos temporalmente el StatefulSet o eliminamos dos pods a la vez:

```bash
kubectl delete pod mongodb-1 mongodb-2 --now
```

Nos conectamos a `mongodb-0` mientras los otros dos nodos están inaccesibles:

```bash
kubectl exec -it mongodb-0 -- mongosh --eval "rs.status().members.map(m => ({ name: m.name.split('.')[0], stateStr: m.stateStr }))"
```

**Salida observada:**
```json
[
  { "name": "mongodb-0", "stateStr": "SECONDARY" },
  { "name": "mongodb-1", "stateStr": "(not reachable/healthy)" },
  { "name": "mongodb-2", "stateStr": "(not reachable/healthy)" }
]
```

**El Descubrimiento Crucial:**
* `mongodb-0` está vivo, sano y con su almacenamiento intacto.
* Sin embargo, **se ha auto-degradado a `SECONDARY` y rechaza todas las escrituras**.
* ¿Por qué? Porque solo tiene `1` voto de `3` (`33% < 50%`). Para evitar inconsistencias (*split-brain*), MongoDB prohíbe terminantemente la existencia de un Primario si no se puede demostrar la mayoría de la red.
* **Lección para producción:** Un clúster con 2 réplicas no tolera la pérdida de 1 nodo para escrituras; un clúster con 3 réplicas tolera la pérdida de 1 nodo; y si caen 2 nodos, el servicio de escritura queda completamente bloqueado.

---

### 7.3 Fase 3: El Dilema del Escalado en StatefulSets (`kubectl scale` a 5 réplicas vs `rs.conf()`)

Este es el experimento que desmantela la ilusión de gestionar MongoDB con Kubernetes nativo. Supongamos que tu equipo experimenta un incremento de tráfico y decide escalar el StatefulSet a 5 réplicas:

```bash
kubectl scale statefulset mongodb --replicas=5
```

**Salida esperada:**
```text
statefulset.apps/mongodb scaled
```

Comprobamos que Kubernetes crea los nuevos Pods y PVCs:

```bash
kubectl get pods -l app=mongodb
```

**Salida esperada:**
```text
NAME        READY   STATUS    RESTARTS   AGE
mongodb-0   1/1     Running   0          10m
mongodb-1   1/1     Running   0          8m
mongodb-2   1/1     Running   0          6m
mongodb-3   1/1     Running   0          25s
mongodb-4   1/1     Running   0          10s
```

Kubernetes reporta orgullosamente 5 réplicas operativas (`5/5 Running`).  
Ahora consultamos el catálogo interno del Replica Set de MongoDB desde cualquiera de los nodos:

```bash
kubectl exec -it mongodb-0 -- mongosh --eval "rs.status().members.map(m => m.name.split('.')[0])"
```

**Salida REAL del Motor de Base de Datos:**
```json
[
  "mongodb-0",
  "mongodb-1",
  "mongodb-2"
]
```

> [!WARNING]
> **¡El Clúster de MongoDB NO reconoce a `mongodb-3` ni a `mongodb-4`!**  
> Para MongoDB, esos dos Pods nuevos son simplemente instancias huérfanas que consumen CPU, RAM y almacenamiento sin formar parte del Replica Set, sin sincronizar datos y sin participar en las elecciones de quórum.  
> 
> Y lo que es peor: si ejecutas `kubectl scale statefulset mongodb --replicas=1`, Kubernetes destruirá implacablemente `mongodb-2` y `mongodb-1`. El Replica Set no habrá sido reconfigurado previamente, `mongodb-0` detectará que faltan 2 miembros de su catálogo de 3, perderá el quórum y **el clúster quedará perpetuamente bloqueado en solo lectura**.

---

### 7.4 Por qué las Primitivas Nativas no Pueden Resolver la Gestión del Ciclo de Vida

El experimento demuestra una divergencia arquitectónica insalvable entre Kubernetes y los sistemas distribuidos:

```
+-----------------------------------------------------------------------------------------+
|                  EL DESACUMPLIMIENTO ENTRE KUBERNETES Y EL MOTOR DE BD                  |
+-----------------------------------------------------------------------------------------+
|                                                                                         |
|   PLANO DE KUBERNETES:                 PLANO DEL MOTOR DISTRIBUIDO:                     |
|   - Solo gestiona contenedores         - Gestiona topología interna (rs.conf)           |
|   - Conoce Pods [0..N]                 - Requiere votación para añadir miembros         |
|   - Escala matando procesos            - Exige rs.stepDown() ordenado antes de parar    |
|   - Ignora la coherencia del Oplog     - Requiere quórum estricto (Mayoría > 50%)       |
|                                                                                         |
|             \                                       /                                   |
|              \                                     /                                    |
|               +-----------------------------------+                                     |
|               |       LA BRECHA OPERACIONAL       |                                     |
|               |  Kubernetes no entiende MongoDB.  |                                     |
|               |  MongoDB no entiende Kubernetes.  |                                     |
|               +-----------------------------------+                                     |
|                                 |                                                       |
|                                 v                                                       |
|                     EL OPERADOR DE KUBERNETES                                           |
|       (El puente de reconciliación que une ambos mundos en tiempo real)                 |
+-----------------------------------------------------------------------------------------+
```

---

## 8. La Brecha hacia la Producción: Por Qué Usamos Operadores

### 8.1 Matriz Comparativa: StatefulSet Manual vs. Operadores de Producción

En entornos empresariales, el despliegue manual con StatefulSet se sustituye por Operadores especializados. A continuación se desglosan las diferencias operativas críticas:

| Capacidad Operativa | StatefulSet Manual (Laboratorio) | Operador de Producción (Enterprise) |
| :--- | :--- | :--- |
| **Escalado Horizontal** | Manual con intervención humana en `rs.conf()` (`rs.add()` / `rs.remove()`). Riesgo de quórum. | **Automático y Atómico**: Modifica `rs.conf()` antes de apagar o instanciar pods. |
| **Mantenimiento y Rolling Updates**| El reinicio del primario corta transacciones abruptamente provocando elecciones forzadas. | **Graceful StepDown**: Ejecuta `rs.stepDown()` preventivo promoviendo un nuevo líder antes de drenar el pod. |
| **Gestión de Usuarios y BDs** | Manual interactiva con `mongosh` dentro del contenedor primario. | **Declarativa (CRDs)**: Recursos `MongoDBUser` gestionados por GitOps y RBAC. |
| **Seguridad y Cifrado TLS** | Montajes manuales de Secrets con scripts frágiles de `chmod 400` en initContainers. | **Cert-Manager Integrado**: Rotación automática y sin reinicio de certificados TLS/x509. |
| **Copias de Seguridad (Backups)** | Scripts en cron con `mongodump` propensos a inconsistencias de Oplog. | **Consistencia Point-in-Time (PITR)**: Snapshots coordinados con Oplog continuo en S3/GCS. |
| **Sharding Distribuido** | Arquitectura inmanejable a mano (decenas de StatefulSets para `mongos`, Config y Shards). | **Nativo en CRD**: Despliega routers `mongos`, Config Servers y N Shards con una sola línea YAML. |

---

### 8.2 Capacidades Esenciales de un Operador (MongoDB Community Operator y Percona PSMDB)

En el ecosistema cloud-native actual existen dos grandes referentes:
1. **MongoDB Community Kubernetes Operator:** Desarrollado por MongoDB Inc., ideal para orquestar Replica Sets de la versión libre de MongoDB mediante el CRD `MongoDBCommunity`.
2. **Percona Server for MongoDB Operator (PSMDB):** Proyecto de código abierto de grado empresarial desarrollado por Percona. Destaca por integrar de serie:
   * **Percona Backup for MongoDB (PBM):** Motor de copias consistentes en caliente con restauración en cualquier punto del tiempo (*Point-in-Time Recovery*).
   * **Monitoreo con PMM:** Métricas profundas de latencia de WiredTiger y consultas lentas exportadas automáticamente a Prometheus y Grafana.
   * **Cero Bloqueo de Fabricante (*No Vendor Lock-in*):** Funcionalidades de nivel corporativo (cifrado en reposo, auditoría y sharding) sin requerir licencias cerradas de Ops Manager.

---

## 9. Resolución de Problemas Frecuentes (Troubleshooting)

### 9.1 Error 1: Permisos Abiertos en Keyfile (`permissions on keyfile are too open`)

* **Síntoma:** El contenedor `mongodb` entra en ciclo de reinicio continuo (`CrashLoopBackOff`).
* **Diagnóstico en logs (`kubectl logs mongodb-0 -c mongodb`):**
  ```text
  Fatal Assertion 16996 at src/mongo/db/initialize_server_global_state.cpp:420
  permissions on /etc/mongo-keyfile/keyfile are too open: 0644
  ```
* **Causa Raíz:** El archivo se montó directamente desde un Secret de Kubernetes sin normalizar sus permisos octales.
* **Solución Definitiva:** Asegurarse de que el `initContainer` (`init-keyfile`) copie el archivo a un volumen `emptyDir` y ejecute `chmod 400 /etc/mongo-keyfile/keyfile && chown 999:999 /etc/mongo-keyfile/keyfile`.

---

### 9.2 Error 2: Operación Rechazada en Secundario (`NotWritablePrimary`)

* **Síntoma:** Las aplicaciones clientes devuelven errores 500 y rechazan inserciones:
  ```text
  MongoServerError: NotWritablePrimary
  ```
* **Causa Raíz:** La aplicación está intentando escribir en un nodo con rol `SECONDARY` porque utiliza una IP estática o un servicio de Kubernetes en lugar de la URI con `replicaSet=rs0`.
* **Solución Definitiva:** Actualizar la cadena de conexión de la aplicación para que apunte a las semillas FQDN a través del Headless Service:
  ```text
  mongodb://mongodb-0.mongodb-headless:27017,mongodb-1.mongodb-headless:27017,mongodb-2.mongodb-headless:27017/?replicaSet=rs0
  ```

---

### 9.3 Error 3: Pods en `Pending` por Ausencia de StorageClass o Taints

* **Síntoma:** El Pod `mongodb-0` o `mongodb-2` permanece en estado `Pending` indefinidamente.
* **Diagnóstico con `kubectl describe pod mongodb-0`:**
  * Si el evento indica: `0/2 nodes available: 1 node(s) had untolerated taint {node-role.kubernetes.io/control-plane}`:  
    Ejecutar: `kubectl taint nodes --all node-role.kubernetes.io/control-plane-` para permitir la programación en el nodo Master.
  * Si el evento indica: `waiting for a volume to be created, either by dynamic provisioning`:  
    Confirmar que Rancher `local-path-provisioner` está instalado y que su StorageClass está anotada como predeterminada:
    ```bash
    kubectl apply -f manifests/00-local-path-storage.yaml
    ```

---

### 9.4 Error 4: Fallo de Resolución DNS durante `rs.initiate()`

* **Síntoma:** Al ejecutar `rs.initiate()`, la consola devuelve el error:
  ```text
  No host described in new configuration was acceptable: mongodb-1.mongodb-headless...: NodeNotFound
  ```
* **Causa Raíz:** Se intentó inicializar el Replica Set antes de que CoreDNS registrara los Pods o antes de que los contenedores `mongodb-1` y `mongodb-2` estuvieran en estado `Running`.
* **Solución Definitiva:** Verificar con `kubectl get pods -l app=mongodb` que las 3 réplicas muestran `1/1 Running` antes de lanzar `rs.initiate()`.
