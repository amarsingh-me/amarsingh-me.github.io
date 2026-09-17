---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-08-12
title: Kubernetes Deployment Pipeline (Local Machine → Production)
tags: [kubernetes, docker, ci-cd, deployment]
categories: [DevOps]
mermaid: true
---

Code goes from a local `Dockerfile` → built image → pushed to a registry → deployed via CI/CD or GitOps using hand-written Kubernetes manifests (never auto-converted from `docker-compose.yml`) → scheduled onto a node → actually started by the kubelet/container runtime → served to real traffic via a Service/Ingress.

{{< mermaid >}}
flowchart TD
  subgraph P1["Phase 1 — your machine"]
    A1["01 Write Dockerfile"] --> A2["02 docker build"] --> A3["03 docker push"]
  end
  subgraph P2["Phase 2 — CI/CD or GitOps"]
    B1["04 Pipeline reads k8s manifests"] --> B2["05 kubectl apply / GitOps sync"]
  end
  subgraph P3["Phase 3 — cluster control plane"]
    C1["06 API server records state"] --> C2["07 Scheduler assigns node"]
  end
  subgraph P4["Phase 4 — on the chosen node"]
    D1["08 kubelet + containerd start container"]
  end
  subgraph P5["Phase 5 — live traffic"]
    E1["09 Service/Ingress routes traffic"]
  end
  A3 --> B1
  B2 --> C1
  C2 --> D1
  D1 --> E1
{{< /mermaid >}}

**Phase 1 — your machine**
1. Write a `Dockerfile` — instructions for building an image: base OS, install deps, copy code, entrypoint.
2. `docker build` — produces a static, versioned image, a snapshot of everything needed to run the app.
3. `docker push` — image is sent to a registry (Docker Hub, ECR, GCR…), tagged, e.g. `myapp:a1b2c3d`.

**Phase 2 — CI/CD or GitOps**
4. A pipeline (or GitOps tool) reads your Kubernetes manifests — hand-written Deployment/Service YAML. This is a **separate set of files from `docker-compose.yml`**, not something auto-generated from it.
5. `kubectl apply -f` — or, more commonly in production, a GitOps tool (ArgoCD/Flux) syncing a git repo of manifests — sends the desired state ("3 replicas of this image") to the cluster.

**Phase 3 — cluster control plane**
6. The API server receives and records the desired state — every change to the cluster passes through here first.
7. The scheduler assigns each Pod to a specific node.

**Phase 4 — on the chosen node**
8. The kubelet talks to the container runtime (containerd) to pull the image and start the container. This is the moment a Pod stops being a YAML wish and becomes a running process.

**Phase 5 — live traffic**
9. A Service/Ingress routes real requests only to Pods that are currently healthy.

**On docker-compose specifically**: it never gets converted into a Pod automatically. Compose describes "run these containers together" for a local machine only. Kubernetes manifests describe the same kind of thing for a cluster, but are written separately — by hand, or templated with Helm. A tool called Kompose can do a rough one-time conversion, but production setups almost never rely on it.
