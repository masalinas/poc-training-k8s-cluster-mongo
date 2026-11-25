# Spec Delta: mongodb-statefulset-cluster

## Purpose

Define el despliegue manual y la arquitectura de un clúster de base de datos MongoDB 7.0 en topología Replica Set de 3 miembros utilizando exclusivamente primitivas nativas de Kubernetes.

## ADDED Requirements

### Requirement: Despliegue de StatefulSet con Tres Réplicas e Identidad Estable
El sistema DEBE (MUST) orquestar exactamente 3 réplicas de MongoDB (`mongodb-0`, `mongodb-1`, `mongodb-2`) utilizando un `StatefulSet` con política `OrderedReady` para garantizar orden de arranque y nombres deterministas.

#### Scenario: Creación secuencial de réplicas
- **WHEN** se aplica el manifiesto del StatefulSet en el namespace `default`
- **THEN** Kubernetes crea los Pods secuencialmente desde el ordinal 0 hasta el 2, asignando a cada uno su identidad de red estable.

### Requirement: Resolución DNS Individual mediante Headless Service
El sistema DEBE (MUST) proveer un servicio de red `Headless` (`clusterIP: None`) con selector hacia los pods de MongoDB para permitir la resolución FQDN de cada réplica en CoreDNS.

#### Scenario: Resolución de nombres por réplica
- **WHEN** un pod consulta el nombre `mongodb-0.mongodb-headless.default.svc.cluster.local`
- **THEN** CoreDNS resuelve directamente la dirección IP individual asignada al pod `mongodb-0`.

### Requirement: Preparación de Permisos del KeyFile mediante InitContainer
El sistema DEBE (MUST) utilizar un `initContainer` en cada Pod para copiar la clave compartida (`keyFile`) desde un Secret a un volumen compartido `emptyDir`, asignando permisos octales `0400` y usuario `999:999`.

#### Scenario: Inicialización exitosa de permisos de clave
- **WHEN** el Pod arranca y ejecuta el contenedor de inicialización
- **THEN** el archivo `/etc/mongo-keyfile/keyfile` queda configurado con permisos de solo lectura para el proceso `mongod`, evitando errores de aborto por clave abierta.

### Requirement: Aislamiento Dinámico de Almacenamiento con VolumeClaimTemplates
El sistema DEBE (MUST) solicitar almacenamiento dinámico persistente de 1Gi por cada réplica mediante `volumeClaimTemplates` utilizando la StorageClass `local-path`.

#### Scenario: Enlace automático de volúmenes persistentes
- **WHEN** el StatefulSet instancia cada una de las réplicas
- **THEN** el aprovisionador crea un PVC en estado `Bound` vinculado a una ruta local persistente en el nodo anfitrión.

### Requirement: Inicialización Guiada e Interactiva del Replica Set
El sistema DEBE (MUST) permitir la inicialización explícita del Replica Set `rs0` mediante el comando `rs.initiate()` ejecutado interactivamente con `mongosh` desde el Pod `mongodb-0`, especificando los 3 miembros con sus FQDNs.

#### Scenario: Transición exitosa a PRIMARY y SECONDARIES
- **WHEN** el operador ejecuta `rs.initiate()` con las semillas FQDN en `mongodb-0`
- **THEN** `mongodb-0` asume el rol de `PRIMARY` y los pods `mongodb-1` y `mongodb-2` sincronizan sus catálogos pasando a estado `SECONDARY`.
