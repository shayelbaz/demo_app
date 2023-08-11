# HiredScore
# Pizza-app Helm Chart

Pizza-app is an python app for managing pizza orders written in Flask framework.

# Intruduction

This chart was designed to be deployed on local standalone cluster in HA mode with shared PV.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- PV provisioner support in the underlying infrastructure

## Deploy release in local

1. Clone the repo localy.
2. Prepare folder to be mounted as local PV.
3. deploy the chart as bellow -
    ```console
    helm template my-release charts/pizza_app --set persistence.local.hostPath.path=/local-folder
    ```
