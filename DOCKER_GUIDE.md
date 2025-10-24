# PR-Agent Docker 사용 가이드

이 가이드는 PR-Agent를 Docker로 빌드하고 실행하는 방법을 상세히 설명합니다.

## 목차
- [사전 요구사항](#사전-요구사항)
- [Docker 이미지 빌드](#docker-이미지-빌드)
- [실행 방법](#실행-방법)
- [환경 변수 설정](#환경-변수-설정)
- [배포 타입별 가이드](#배포-타입별-가이드)
- [Docker Compose 사용](#docker-compose-사용)
- [문제 해결](#문제-해결)

---

## 사전 요구사항

### 1. Docker 설치
```bash
# Docker 버전 확인
docker --version

# Docker Compose 버전 확인 (선택사항)
docker compose version
```

### 2. 필요한 API 키/토큰
- **OpenAI API Key**: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **GitHub Personal Access Token**: [https://github.com/settings/tokens](https://github.com/settings/tokens)
  - 필요한 권한: `repo` (전체 저장소 접근)

### 3. 프로젝트 클론
```bash
git clone https://github.com/Codium-ai/pr-agent.git
cd pr-agent
```

---

## Docker 이미지 빌드

PR-Agent는 **멀티 스테이지 빌드**를 사용하여 여러 배포 타입을 지원합니다.

### 사용 가능한 빌드 타겟

| 타겟 | 용도 | 포트 | 실행 방식 |
|------|------|------|-----------|
| `cli` | CLI 명령어 실행 | - | 일회성 |
| `github_app` | GitHub 웹훅 서버 | 3000 | 데몬 |
| `gitlab_webhook` | GitLab 웹훅 서버 | 3000 | 데몬 |
| `bitbucket_app` | Bitbucket 앱 서버 | 3000 | 데몬 |
| `gitea_app` | Gitea 앱 서버 | 3000 | 데몬 |
| `azure_devops_webhook` | Azure DevOps 웹훅 | 3000 | 데몬 |
| `github_polling` | GitHub 폴링 서버 | - | 데몬 |
| `test` | 테스트 실행 | - | 일회성 |

### 1. CLI 용 빌드 (권장 - 시작용)

```bash
docker build \
  -f docker/Dockerfile \
  -t pr-agent:cli \
  --target cli \
  .
```

**설명:**
- `-f docker/Dockerfile`: Dockerfile 경로 지정
- `-t pr-agent:cli`: 이미지 이름과 태그
- `--target cli`: 빌드할 스테이지 지정
- `.`: 빌드 컨텍스트 (프로젝트 루트)

### 2. GitHub App 서버 빌드

```bash
docker build \
  -f docker/Dockerfile \
  -t pr-agent:github_app \
  --target github_app \
  .
```

### 3. GitLab Webhook 서버 빌드

```bash
docker build \
  -f docker/Dockerfile \
  -t pr-agent:gitlab_webhook \
  --target gitlab_webhook \
  .
```

### 4. 모든 타겟 한번에 빌드

```bash
#!/bin/bash
# build-all.sh

TARGETS=("cli" "github_app" "gitlab_webhook" "bitbucket_app" "gitea_app" "test")

for target in "${TARGETS[@]}"; do
  echo "Building $target..."
  docker build \
    -f docker/Dockerfile \
    -t pr-agent:$target \
    --target $target \
    .
done

echo "All images built successfully!"
docker images | grep pr-agent
```

### 5. ARM Mac에서 AMD64 빌드 (배포용)

```bash
# Apple Silicon Mac에서 x86_64용 빌드
docker buildx build \
  --platform linux/amd64 \
  -f docker/Dockerfile \
  -t pr-agent:github_app \
  --target github_app \
  .
```

---

## 실행 방법

### 1. CLI 모드로 실행

#### 기본 사용법
```bash
docker run --rm -it \
  -e OPENAI.KEY=sk-xxxxxxxxxxxxx \
  -e GITHUB.USER_TOKEN=ghp_xxxxxxxxxxxxx \
  pr-agent:cli \
  --pr_url https://github.com/owner/repo/pull/123 \
  review
```

**옵션 설명:**
- `--rm`: 컨테이너 종료 시 자동 삭제
- `-it`: 대화형 모드 (로그 출력)
- `-e`: 환경 변수 설정

#### 다양한 명령어 예제

```bash
# PR 리뷰
docker run --rm -it \
  -e OPENAI.KEY=$OPENAI_KEY \
  -e GITHUB.USER_TOKEN=$GITHUB_TOKEN \
  pr-agent:cli \
  --pr_url https://github.com/owner/repo/pull/123 \
  review

# PR 설명 생성
docker run --rm -it \
  -e OPENAI.KEY=$OPENAI_KEY \
  -e GITHUB.USER_TOKEN=$GITHUB_TOKEN \
  pr-agent:cli \
  --pr_url https://github.com/owner/repo/pull/123 \
  describe

# 코드 개선 제안
docker run --rm -it \
  -e OPENAI.KEY=$OPENAI_KEY \
  -e GITHUB.USER_TOKEN=$GITHUB_TOKEN \
  pr-agent:cli \
  --pr_url https://github.com/owner/repo/pull/123 \
  improve

# PR에 질문하기
docker run --rm -it \
  -e OPENAI.KEY=$OPENAI_KEY \
  -e GITHUB.USER_TOKEN=$GITHUB_TOKEN \
  pr-agent:cli \
  --pr_url https://github.com/owner/repo/pull/123 \
  ask "이 PR의 주요 변경사항은?"

# 확장 모드로 개선 제안 (더 자세한 분석)
docker run --rm -it \
  -e OPENAI.KEY=$OPENAI_KEY \
  -e GITHUB.USER_TOKEN=$GITHUB_TOKEN \
  pr-agent:cli \
  --pr_url https://github.com/owner/repo/pull/123 \
  improve --extended
```

### 2. 웹훅 서버 모드로 실행

#### GitHub App 서버

```bash
docker run -d \
  --name pr-agent-github \
  -p 3000:3000 \
  -e OPENAI.KEY=$OPENAI_KEY \
  -e GITHUB.USER_TOKEN=$GITHUB_TOKEN \
  --restart unless-stopped \
  pr-agent:github_app
```

**옵션 설명:**
- `-d`: 백그라운드 실행 (데몬 모드)
- `--name`: 컨테이너 이름 지정
- `-p 3000:3000`: 포트 매핑 (호스트:컨테이너)
- `--restart unless-stopped`: 자동 재시작

**서버 관리 명령어:**
```bash
# 로그 확인
docker logs -f pr-agent-github

# 컨테이너 중지
docker stop pr-agent-github

# 컨테이너 시작
docker start pr-agent-github

# 컨테이너 재시작
docker restart pr-agent-github

# 컨테이너 삭제
docker rm -f pr-agent-github
```

#### GitLab Webhook 서버

```bash
docker run -d \
  --name pr-agent-gitlab \
  -p 3000:3000 \
  -e OPENAI.KEY=$OPENAI_KEY \
  -e CONFIG.GIT_PROVIDER=gitlab \
  -e GITLAB.PERSONAL_ACCESS_TOKEN=$GITLAB_TOKEN \
  -e GITLAB.URL=https://gitlab.com \
  --restart unless-stopped \
  pr-agent:gitlab_webhook
```

#### Bitbucket App 서버

```bash
docker run -d \
  --name pr-agent-bitbucket \
  -p 3000:3000 \
  -e OPENAI.KEY=$OPENAI_KEY \
  -e CONFIG.GIT_PROVIDER=bitbucket \
  -e BITBUCKET.BEARER_TOKEN=$BITBUCKET_TOKEN \
  --restart unless-stopped \
  pr-agent:bitbucket_app
```

### 3. 테스트 실행

```bash
# 전체 테스트 실행
docker run --rm \
  pr-agent:test \
  pytest tests/

# 특정 테스트만 실행
docker run --rm \
  pr-agent:test \
  pytest tests/unittest/test_configuration.py

# 커버리지와 함께 실행
docker run --rm \
  pr-agent:test \
  pytest --cov=pr_agent tests/
```

---

## 환경 변수 설정

### 1. .env 파일 사용 (권장)

`.env` 파일 생성:
```bash
cat > .env <<EOF
# AI Model Configuration
OPENAI.KEY=sk-xxxxxxxxxxxxx
CONFIG.MODEL=gpt-4

# Git Provider Configuration
CONFIG.GIT_PROVIDER=github
GITHUB.USER_TOKEN=ghp_xxxxxxxxxxxxx
GITHUB.DEPLOYMENT_TYPE=user

# Optional: GitHub Enterprise
# GITHUB.BASE_URL=https://github.mycompany.com/api/v3

# Optional: Logging
CONFIG.LOG_LEVEL=INFO
CONFIG.VERBOSITY_LEVEL=1

# Optional: Custom settings
PR_REVIEWER.NUM_MAX_FINDINGS=5
PR_REVIEWER.EXTRA_INSTRUCTIONS=보안 이슈에 집중
EOF

# 파일 권한 설정 (중요!)
chmod 600 .env
```

**.env 파일로 실행:**
```bash
docker run --rm -it \
  --env-file .env \
  pr-agent:cli \
  --pr_url https://github.com/owner/repo/pull/123 \
  review
```

### 2. 환경 변수 형식

PR-Agent는 두 가지 형식을 지원합니다:

```bash
# 형식 1: 점(.) 구분자 (Docker에서 권장)
-e OPENAI.KEY=sk-xxx
-e GITHUB.USER_TOKEN=ghp-xxx
-e CONFIG.GIT_PROVIDER=github

# 형식 2: 언더스코어(__) 구분자
-e OPENAI__KEY=sk-xxx
-e GITHUB__USER_TOKEN=ghp-xxx
-e CONFIG__GIT_PROVIDER=github
```

### 3. 주요 환경 변수

#### AI Model 설정
```bash
OPENAI.KEY=sk-xxxxxxxxxxxxx
CONFIG.MODEL=gpt-4                    # 기본 모델
CONFIG.FALLBACK_MODELS=["gpt-3.5-turbo"]  # 폴백 모델
```

#### Git Provider 설정

**GitHub:**
```bash
CONFIG.GIT_PROVIDER=github
GITHUB.USER_TOKEN=ghp-xxxxxxxxxxxxx
GITHUB.DEPLOYMENT_TYPE=user
# GitHub Enterprise용:
GITHUB.BASE_URL=https://github.company.com/api/v3
```

**GitLab:**
```bash
CONFIG.GIT_PROVIDER=gitlab
GITLAB.PERSONAL_ACCESS_TOKEN=glpat-xxxxxxxxxxxxx
GITLAB.URL=https://gitlab.com
```

**Bitbucket:**
```bash
CONFIG.GIT_PROVIDER=bitbucket
BITBUCKET.BEARER_TOKEN=xxxxxxxxxxxxx
```

**Azure DevOps:**
```bash
CONFIG.GIT_PROVIDER=azure_devops
AZURE_DEVOPS.ORG=myorg
AZURE_DEVOPS.PAT=xxxxxxxxxxxxx
```

#### 기타 설정
```bash
# 로깅
CONFIG.LOG_LEVEL=DEBUG                # DEBUG, INFO, WARNING, ERROR
CONFIG.VERBOSITY_LEVEL=2              # 0, 1, 2

# 리뷰어 설정
PR_REVIEWER.NUM_MAX_FINDINGS=3        # 최대 발견 사항 수
PR_REVIEWER.REQUIRE_TESTS_REVIEW=true
PR_REVIEWER.REQUIRE_SECURITY_REVIEW=true

# 토큰 제한
CONFIG.MAX_MODEL_TOKENS=32000
```

---

## 배포 타입별 가이드

### 1. CLI 모드 (로컬 개발/CI/CD)

**사용 사례:**
- 로컬에서 PR 분석
- CI/CD 파이프라인에서 자동 리뷰
- 배치 처리

**Bash 스크립트 예제:**
```bash
#!/bin/bash
# review-pr.sh

if [ -z "$1" ]; then
    echo "Usage: $0 <PR_URL>"
    exit 1
fi

PR_URL=$1

docker run --rm -it \
    --env-file .env \
    pr-agent:cli \
    --pr_url "$PR_URL" \
    review

echo "Review completed for $PR_URL"
```

**실행:**
```bash
chmod +x review-pr.sh
./review-pr.sh https://github.com/owner/repo/pull/123
```

**GitHub Actions 통합:**
```yaml
# .github/workflows/pr-agent-docker.yml
name: PR Agent Docker Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build PR-Agent
        run: |
          docker build \
            -f docker/Dockerfile \
            -t pr-agent:cli \
            --target cli \
            .

      - name: Run PR Review
        run: |
          docker run --rm \
            -e OPENAI.KEY=${{ secrets.OPENAI_KEY }} \
            -e GITHUB.USER_TOKEN=${{ secrets.GITHUB_TOKEN }} \
            pr-agent:cli \
            --pr_url ${{ github.event.pull_request.html_url }} \
            review
```

### 2. GitHub App 서버 (웹훅)

**사용 사례:**
- PR 이벤트에 자동 응답
- 조직 전체에 배포
- 지속적인 모니터링

**프로덕션 배포:**
```bash
# 1. 이미지 빌드
docker build -f docker/Dockerfile -t pr-agent:github_app --target github_app .

# 2. 서버 실행
docker run -d \
  --name pr-agent-prod \
  -p 3000:3000 \
  -e OPENAI.KEY=$OPENAI_KEY \
  -e GITHUB.USER_TOKEN=$GITHUB_TOKEN \
  -e CONFIG.LOG_LEVEL=INFO \
  --restart unless-stopped \
  --health-cmd "curl -f http://localhost:3000/health || exit 1" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  pr-agent:github_app

# 3. 로그 모니터링
docker logs -f pr-agent-prod
```

**nginx 리버스 프록시 설정:**
```nginx
# /etc/nginx/sites-available/pr-agent
server {
    listen 80;
    server_name pr-agent.yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. GitLab Webhook 서버

```bash
docker run -d \
  --name pr-agent-gitlab \
  -p 3000:3000 \
  -e OPENAI.KEY=$OPENAI_KEY \
  -e CONFIG.GIT_PROVIDER=gitlab \
  -e GITLAB.PERSONAL_ACCESS_TOKEN=$GITLAB_TOKEN \
  -e GITLAB.URL=https://gitlab.mycompany.com \
  -e GITLAB.SHARED_SECRET=$WEBHOOK_SECRET \
  --restart unless-stopped \
  pr-agent:gitlab_webhook
```

### 4. 테스트 환경

```bash
# 개발 환경에서 빌드
docker build -f docker/Dockerfile -t pr-agent:test --target test .

# 전체 테스트 스위트 실행
docker run --rm \
  -v $(pwd)/test-results:/app/test-results \
  pr-agent:test \
  pytest --junit-xml=/app/test-results/junit.xml tests/

# 특정 테스트만 실행
docker run --rm -it \
  pr-agent:test \
  pytest -v tests/unittest/test_configuration.py::test_settings
```

---

## Docker Compose 사용

### 1. 기본 docker-compose.yml

```yaml
version: '3.8'

services:
  # CLI 서비스 (일회성 실행용)
  pr-agent-cli:
    build:
      context: .
      dockerfile: docker/Dockerfile
      target: cli
    image: pr-agent:cli
    env_file: .env
    profiles: ["cli"]

  # GitHub App 서버
  pr-agent-github:
    build:
      context: .
      dockerfile: docker/Dockerfile
      target: github_app
    image: pr-agent:github_app
    container_name: pr-agent-github
    ports:
      - "3000:3000"
    env_file: .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    profiles: ["github"]

  # GitLab Webhook 서버
  pr-agent-gitlab:
    build:
      context: .
      dockerfile: docker/Dockerfile
      target: gitlab_webhook
    image: pr-agent:gitlab_webhook
    container_name: pr-agent-gitlab
    ports:
      - "3001:3000"
    environment:
      - CONFIG.GIT_PROVIDER=gitlab
    env_file: .env
    restart: unless-stopped
    profiles: ["gitlab"]

  # 테스트 서비스
  pr-agent-test:
    build:
      context: .
      dockerfile: docker/Dockerfile
      target: test
    image: pr-agent:test
    volumes:
      - ./test-results:/app/test-results
    command: pytest --junit-xml=/app/test-results/junit.xml tests/
    profiles: ["test"]
```

### 2. Docker Compose 명령어

```bash
# 빌드
docker compose build

# GitHub App 서버 시작
docker compose --profile github up -d

# GitLab Webhook 서버 시작
docker compose --profile gitlab up -d

# 로그 확인
docker compose logs -f pr-agent-github

# 서버 중지
docker compose --profile github down

# 테스트 실행
docker compose --profile test run --rm pr-agent-test

# CLI 실행 (일회성)
docker compose run --rm pr-agent-cli \
  --pr_url https://github.com/owner/repo/pull/123 \
  review

# 모든 서비스 중지 및 삭제
docker compose down
```

### 3. 프로덕션용 docker-compose.yml

```yaml
version: '3.8'

services:
  pr-agent:
    build:
      context: .
      dockerfile: docker/Dockerfile
      target: github_app
    image: pr-agent:github_app
    container_name: pr-agent-production
    ports:
      - "3000:3000"
    env_file: .env
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
    networks:
      - pr-agent-network
    volumes:
      - pr-agent-logs:/var/log/pr-agent

  # 선택사항: nginx 리버스 프록시
  nginx:
    image: nginx:alpine
    container_name: pr-agent-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - pr-agent
    restart: always
    networks:
      - pr-agent-network

networks:
  pr-agent-network:
    driver: bridge

volumes:
  pr-agent-logs:
```

**실행:**
```bash
# 프로덕션 환경 시작
docker compose -f docker-compose.prod.yml up -d

# 스케일 아웃 (여러 인스턴스)
docker compose -f docker-compose.prod.yml up -d --scale pr-agent=3

# 로그 확인
docker compose -f docker-compose.prod.yml logs -f

# 중지 및 정리
docker compose -f docker-compose.prod.yml down -v
```

---

## 고급 사용법

### 1. 볼륨 마운트로 설정 파일 사용

```bash
# 설정 파일을 호스트에서 관리
docker run --rm -it \
  -v $(pwd)/pr_agent/settings/.secrets.toml:/app/pr_agent/settings/.secrets.toml:ro \
  -v $(pwd)/custom-config.toml:/app/pr_agent/settings/configuration.toml:ro \
  pr-agent:cli \
  --pr_url https://github.com/owner/repo/pull/123 \
  review
```

### 2. 로그 파일 수집

```bash
docker run -d \
  --name pr-agent-github \
  -p 3000:3000 \
  -v $(pwd)/logs:/var/log/pr-agent \
  --env-file .env \
  pr-agent:github_app
```

### 3. 네트워크 격리

```bash
# 네트워크 생성
docker network create pr-agent-net

# 컨테이너 실행
docker run -d \
  --name pr-agent \
  --network pr-agent-net \
  -p 3000:3000 \
  --env-file .env \
  pr-agent:github_app
```

### 4. 리소스 제한

```bash
docker run -d \
  --name pr-agent \
  --memory="2g" \
  --memory-swap="2g" \
  --cpus="1.5" \
  -p 3000:3000 \
  --env-file .env \
  pr-agent:github_app
```

### 5. 보안 강화

```bash
docker run -d \
  --name pr-agent \
  --read-only \
  --tmpfs /tmp \
  --security-opt no-new-privileges:true \
  --cap-drop ALL \
  -p 3000:3000 \
  --env-file .env \
  pr-agent:github_app
```

---

## 문제 해결

### 1. 빌드 실패

**문제:** `ERROR [internal] load metadata for docker.io/library/python:3.12.10-slim`

**해결:**
```bash
# Docker 데몬 재시작
sudo systemctl restart docker

# 또는 캐시 없이 빌드
docker build --no-cache -f docker/Dockerfile -t pr-agent:cli --target cli .
```

### 2. 실행 시 모듈 없음 에러

**문제:** `ModuleNotFoundError: No module named 'litellm'`

**원인:** 잘못된 빌드 타겟 또는 불완전한 빌드

**해결:**
```bash
# 이미지 삭제 후 재빌드
docker rmi pr-agent:cli
docker build -f docker/Dockerfile -t pr-agent:cli --target cli .
```

### 3. 권한 에러

**문제:** `403 {"message": "Must have admin rights to Repository."}`

**원인:** GitHub 토큰의 권한 부족

**해결:**
1. GitHub 토큰 재생성 시 `repo` 전체 권한 선택
2. Organization 저장소의 경우 `read:org` 권한 추가
3. 토큰 확인:
```bash
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

### 4. API 키 에러

**문제:** `APIError: OpenAIException - Connection error`

**해결:**
```bash
# 환경 변수 확인
docker run --rm -it \
  --env-file .env \
  pr-agent:cli \
  env | grep -E "OPENAI|GITHUB"

# 직접 환경 변수로 테스트
docker run --rm -it \
  -e OPENAI.KEY=sk-test123 \
  -e GITHUB.USER_TOKEN=ghp-test123 \
  pr-agent:cli \
  --pr_url https://github.com/owner/repo/pull/123 \
  review
```

### 5. 포트 충돌

**문제:** `Error starting userland proxy: listen tcp4 0.0.0.0:3000: bind: address already in use`

**해결:**
```bash
# 포트 사용 중인 프로세스 확인
lsof -i :3000

# 다른 포트 사용
docker run -d -p 3001:3000 --env-file .env pr-agent:github_app
```

### 6. 컨테이너 로그 확인

```bash
# 실시간 로그
docker logs -f pr-agent-github

# 최근 100줄
docker logs --tail 100 pr-agent-github

# 타임스탬프 포함
docker logs -t pr-agent-github

# 에러만 필터링
docker logs pr-agent-github 2>&1 | grep -i error
```

### 7. 컨테이너 디버깅

```bash
# 실행 중인 컨테이너 접속
docker exec -it pr-agent-github /bin/bash

# 컨테이너 내부 확인
docker exec pr-agent-github ls -la /app/pr_agent
docker exec pr-agent-github cat /app/pr_agent/settings/configuration.toml

# 환경 변수 확인
docker exec pr-agent-github env
```

### 8. 네트워크 문제

```bash
# 컨테이너 네트워크 확인
docker inspect pr-agent-github | grep -A 10 Networks

# 포트 매핑 확인
docker port pr-agent-github

# 컨테이너 내부에서 테스트
docker exec pr-agent-github curl -I http://localhost:3000/health
```

---

## 유용한 스크립트

### 1. 완전 정리 스크립트

```bash
#!/bin/bash
# cleanup.sh - PR-Agent Docker 완전 정리

echo "Stopping all PR-Agent containers..."
docker ps -a | grep pr-agent | awk '{print $1}' | xargs -r docker stop

echo "Removing all PR-Agent containers..."
docker ps -a | grep pr-agent | awk '{print $1}' | xargs -r docker rm

echo "Removing all PR-Agent images..."
docker images | grep pr-agent | awk '{print $3}' | xargs -r docker rmi -f

echo "Removing unused volumes..."
docker volume prune -f

echo "Cleanup complete!"
docker images | grep pr-agent
```

### 2. 빠른 재배포 스크립트

```bash
#!/bin/bash
# redeploy.sh - GitHub App 빠른 재배포

set -e

echo "Stopping existing container..."
docker stop pr-agent-github 2>/dev/null || true
docker rm pr-agent-github 2>/dev/null || true

echo "Rebuilding image..."
docker build -f docker/Dockerfile -t pr-agent:github_app --target github_app .

echo "Starting new container..."
docker run -d \
  --name pr-agent-github \
  -p 3000:3000 \
  --env-file .env \
  --restart unless-stopped \
  pr-agent:github_app

echo "Waiting for container to be healthy..."
sleep 5

docker logs --tail 20 pr-agent-github

echo "Deployment complete!"
```

### 3. 헬스 체크 스크립트

```bash
#!/bin/bash
# health-check.sh - 서버 상태 확인

CONTAINER_NAME="pr-agent-github"
HEALTH_URL="http://localhost:3000/health"

if ! docker ps | grep -q $CONTAINER_NAME; then
    echo "❌ Container $CONTAINER_NAME is not running"
    exit 1
fi

if curl -sf $HEALTH_URL > /dev/null; then
    echo "✅ PR-Agent is healthy"
    exit 0
else
    echo "❌ PR-Agent health check failed"
    docker logs --tail 50 $CONTAINER_NAME
    exit 1
fi
```

---

## 참고 자료

- [Dockerfile 문서](docker/Dockerfile)
- [공식 문서](https://qodo-merge-docs.qodo.ai/)
- [GitHub 설치 가이드](https://qodo-merge-docs.qodo.ai/installation/github/)
- [GitLab 설치 가이드](https://qodo-merge-docs.qodo.ai/installation/gitlab/)
- [설정 옵션](pr_agent/settings/configuration.toml)

---

## 라이선스

Apache 2.0 - 자세한 내용은 [LICENSE](LICENSE) 참조
