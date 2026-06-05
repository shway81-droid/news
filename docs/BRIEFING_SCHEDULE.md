# 아침 브리핑 정시 트리거 설정

데일리 브리핑 봇(`main_briefing.py`, 워크플로우 `daily_briefing.yml`)을
**매일 06:30 KST에 정확히** 실행하기 위한 설정 안내입니다.

## 배경: 왜 외부 트리거인가

GitHub Actions의 `schedule`(cron)은 무료 러너에서 **정시 실행을 보장하지 않습니다.**
실제 실행 기록을 보면 예약(06:30 KST) 대비 **1~2시간씩 지연**되어 8시 가까이 발송됐습니다.

| 예약(KST) | 실제 실행(KST) | 지연 |
|-----------|---------------|------|
| 06:30 | 07:31 ~ 08:17 | +1.0 ~ +1.8시간 |

반면 **`workflow_dispatch`(수동/API 트리거)로 시작된 실행은 수 초 내에 시작**됩니다.
그래서 외부 크론 서비스가 정해진 시각에 GitHub API를 호출해 워크플로우를 트리거하면
지연 없이 정시에 브리핑이 도착합니다.

```
외부 크론(정시) ──POST workflow_dispatch──▶ GitHub Actions(즉시 실행) ──▶ 텔레그램
```

> 그래서 `daily_briefing.yml`에서 `schedule` 트리거는 제거했습니다.
> (외부 트리거와 함께 두면 지연된 schedule이 한 번 더 돌아 **매일 중복 발송**됩니다.)

## ⚠️ 실행 시각 제약 (증시 데이터)

브리핑의 미국 증시 항목은 **전일 종가**를 사용합니다. 미국 증시 마감 시각은

- 여름(서머타임): **05:00 KST**
- 겨울: **06:00 KST**

이므로 **외부 크론을 06:00 KST보다 이르게 잡으면 안 됩니다.**
(장이 안 닫힌 시각에 돌리면 종가가 어제 게 아니라 그제 것이 되거나 값이 틀어집니다.)
권장 시각은 **06:30 KST** — 겨울 마감 + 데이터 반영 여유까지 확보됩니다.
더 당기고 싶어도 06:05 KST 아래로는 내리지 마세요.

---

## 1. GitHub 토큰 발급 (1회)

워크플로우를 API로 트리거하려면 토큰이 필요합니다. **Fine-grained PAT**(최소 권한) 권장.

GitHub → **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**

- **Resource owner**: `shway81-droid`
- **Repository access**: *Only select repositories* → **`news`**
- **Repository permissions** → **Actions: Read and write**
  (Metadata: Read-only은 자동 포함)
- **Expiration**: 원하는 만료일 (만료 전 갱신 필요 — 길게 잡거나 만료 알림 설정)

생성된 토큰 문자열을 복사해 둡니다. (다시 볼 수 없으니 안전하게 보관)

> 텔레그램/Groq 키(`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GROQ_API_KEY`)는
> 기존처럼 **저장소 Secrets**에서 읽으므로 별도 작업이 없습니다. 이 토큰은 *트리거 전용*입니다.

## 2-A. 방법 A — cron-job.org (무료, 추천)

[cron-job.org](https://cron-job.org) 가입 후 **Create cronjob**:

| 항목 | 값 |
|------|----|
| **Title** | `Daily Briefing Trigger` |
| **URL** | `https://api.github.com/repos/shway81-droid/news/actions/workflows/daily_briefing.yml/dispatches` |
| **Schedule** | 매일 **06:30**, Timezone **Asia/Seoul** |

이어서 **Advanced / Common settings**에서:

- **Request method**: `POST`
- **Headers** (커스텀 헤더 추가):
  - `Accept: application/vnd.github+json`
  - `Authorization: Bearer <발급한_토큰>`
  - `X-GitHub-Api-Version: 2022-11-28`
  - `Content-Type: application/json`
- **Request body**:
  ```json
  {"ref":"main"}
  ```

저장하면 끝입니다. (`ref`는 워크플로우 파일이 있는 기본 브랜치 `main`)

## 2-B. 방법 B — Google Cloud Scheduler

GCP 콘솔 → **Cloud Scheduler → Create job**:

- **Frequency**: `30 6 * * *`  (Timezone: `Asia/Seoul`)
- **Target type**: `HTTP`
- **URL**: `https://api.github.com/repos/shway81-droid/news/actions/workflows/daily_briefing.yml/dispatches`
- **HTTP method**: `POST`
- **Headers**: 위 cron-job.org와 동일한 4개
- **Body**: `{"ref":"main"}`

## 3. 동작 확인

설정 직후 바로 테스트하려면 아래 `curl`을 한 번 실행해 보세요 (성공 시 **204 No Content**):

```bash
curl -L -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer <발급한_토큰>" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/shway81-droid/news/actions/workflows/daily_briefing.yml/dispatches \
  -d '{"ref":"main"}'
```

GitHub 저장소 → **Actions → Daily Briefing Bot** 탭에서
**`workflow_dispatch` 이벤트로 새 실행**이 즉시 시작되는지 확인합니다.
텔레그램으로 브리핑이 오면 정상입니다.

## 권장 적용 순서 (발송 공백·중복 방지)

`workflow_dispatch`는 현재 `main`에도 이미 켜져 있으므로, 다음 순서를 권장합니다.

1. 위 1~3단계로 외부 크론을 먼저 설정·테스트한다. (이때 기존 schedule이 살아 있어 공백 없음)
2. 06:30 정시 도착이 확인되면, `schedule`을 제거한 변경(이 PR)을 머지한다. → 이후 중복 없음.

## (선택) 폴백을 두고 싶다면

외부 크론 장애에 대비하려면 `daily_briefing.yml`의 주석 처리된 `schedule`을
**늦은 시각**(예: `00 23 * * *` = 08:00 KST)으로 되살릴 수 있습니다.
단, 외부 트리거와 중복 발송되지 않도록 **"오늘 이미 성공 실행됐으면 건너뛰기"** 같은
중복 방지 단계를 함께 추가해야 합니다.
