# Farmhub Backend

[![CI](https://github.com/your-org/your-repo/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/your-repo/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/your-org/your-repo/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/your-repo)
[![coverage policy](https://img.shields.io/badge/coverage-global%20%E2%89%A590%25%20%7C%20critical%20%E2%89%A595%25-success)](./.github/workflows/ci.yml)

## Test & Coverage

```bash
pytest \
  --cov=. \
  --cov=accounts \
  --cov=orders \
  --cov=products \
  --cov=menu \
  --cov-report=term-missing \
  --cov-report=xml \
  --cov-fail-under=90
```

## Docker

```bash
docker-compose up --build
```
