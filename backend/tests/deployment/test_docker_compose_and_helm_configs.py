"""Automated tests validating Production Docker Compose, Helm Charts, Systemd units, and Deploy configs."""

from pathlib import Path
import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_docker_compose_prod_structure_and_services():
    compose_file = REPO_ROOT / "docker-compose.prod.yml"
    assert compose_file.exists(), "docker-compose.prod.yml must exist"

    with open(compose_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "services" in data
    services = data["services"]

    # Verify all required production services
    required_services = ["postgres", "redis", "backend", "frontend", "prometheus", "grafana"]
    for svc in required_services:
        assert svc in services, f"Service '{svc}' missing from docker-compose.prod.yml"
        assert "healthcheck" in services[svc] or svc in ["grafana", "prometheus"], f"Healthcheck missing for {svc}"

    # Verify persistent volumes
    assert "volumes" in data
    assert "postgres_data" in data["volumes"]
    assert "redis_data" in data["volumes"]
    assert "prometheus_data" in data["volumes"]
    assert "grafana_data" in data["volumes"]


def test_helm_chart_metadata_and_values():
    helm_dir = REPO_ROOT / "deployments" / "helm" / "openquant"
    chart_file = helm_dir / "Chart.yaml"
    values_file = helm_dir / "values.yaml"

    assert chart_file.exists()
    assert values_file.exists()

    with open(chart_file, "r", encoding="utf-8") as f:
        chart_data = yaml.safe_load(f)
    assert chart_data["name"] == "openquant"
    assert chart_data["apiVersion"] == "v2"

    with open(values_file, "r", encoding="utf-8") as f:
        values_data = yaml.safe_load(f)

    assert "backend" in values_data
    assert "frontend" in values_data
    assert "ingress" in values_data
    assert values_data["backend"]["replicaCount"] >= 2
    assert values_data["backend"]["resources"]["limits"]["memory"] is not None
    assert values_data["ingress"]["enabled"] is True


def test_helm_templates_exist():
    templates_dir = REPO_ROOT / "deployments" / "helm" / "openquant" / "templates"
    required_templates = [
        "deployment-backend.yaml",
        "deployment-frontend.yaml",
        "service-backend.yaml",
        "service-frontend.yaml",
        "ingress.yaml",
        "configmap.yaml",
        "secret.yaml",
        "hpa.yaml",
        "_helpers.tpl",
    ]

    for tpl in required_templates:
        tpl_path = templates_dir / tpl
        assert tpl_path.exists(), f"Helm template '{tpl}' missing"


def test_systemd_unit_files_and_security_hardening():
    systemd_dir = REPO_ROOT / "deployments" / "systemd"
    backend_service = systemd_dir / "openquant-backend.service"
    worker_service = systemd_dir / "openquant-worker.service"

    assert backend_service.exists()
    assert worker_service.exists()

    content = backend_service.read_text(encoding="utf-8")
    assert "User=openquant" in content
    assert "NoNewPrivileges=true" in content
    assert "ProtectSystem=full" in content
    assert "Restart=always" in content


def test_production_dockerfiles_and_env_templates():
    backend_dockerfile = REPO_ROOT / "backend" / "Dockerfile.prod"
    frontend_dockerfile = REPO_ROOT / "frontend" / "Dockerfile.prod"
    env_example = REPO_ROOT / ".env.production.example"
    nginx_conf = REPO_ROOT / "frontend" / "nginx.prod.conf"

    assert backend_dockerfile.exists()
    assert frontend_dockerfile.exists()
    assert env_example.exists()
    assert nginx_conf.exists()

    backend_content = backend_dockerfile.read_text(encoding="utf-8")
    assert "USER openquant" in backend_content
    assert "HEALTHCHECK" in backend_content

    frontend_content = frontend_dockerfile.read_text(encoding="utf-8")
    assert "HEALTHCHECK" in frontend_content

    env_content = env_example.read_text(encoding="utf-8")
    assert "OPENQUANT_MASTER_SECRET" in env_content
    assert "JWT_SECRET_KEY" in env_content
    assert "DATABASE_URL" in env_content
