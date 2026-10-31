# Discord_Bot_Frame-PYTHON

discord.py 2.x 기반 슬래시 명령어 봇 프레임. (Python 3.10 이상)

## 실행
```bash
pip install -r requirements.txt
# config.yml 수정 (또는 토큰은 환경변수로)
set DISCORD_TOKEN=봇토큰   # Windows / Linux·macOS: export DISCORD_TOKEN=...
python main.py
```
Windows 외 환경에서는 `uvloop`가 함께 설치되어 자동으로 사용됩니다.
PyInstaller로 빌드한 경우 `config.yml`은 실행 파일과 같은 폴더에 두세요.

## 설정 (`config.yml`)
- `token` — 봇 토큰. `DISCORD_TOKEN` 환경변수가 있으면 그쪽이 우선
- `application_id` — 비워두면 로그인 시 자동으로 가져옴
- `dev_guild_id` — 설정하면 명령어가 해당 서버에 즉시 반영 (개발용)
- `activity` — 봇 상태 메시지 (비우면 표시 안 함)
- `members_intent` — 멤버 목록·입퇴장 이벤트가 필요할 때만 `true` (개발자 포털에서 Server Members Intent도 켜야 함). 관리자 역할 확인에는 필요 없음
- `administrator_role_ids` — 관리자 역할 ID 목록 (하나만 적어도 됨)

## 구조
```
main.py              진입점
core/                모든 도메인이 함께 쓰는 공통 코드
  bot.py             MyBot (도메인 자동 로드, 동기화, is_admin)
  config.py          설정 로드·검증 (읽기 전용 Config)
  errors.py          슬래시 명령어 공통 오류 처리
domains/             기능(도메인)별 폴더. 하나가 확장 기능 하나
  checks.py          (공용) has_admin_role() 권한 체크
  responses.py       (공용) @respond() — return한 (성공, 메시지)는 ✅/❌로, Embed는 embed로 응답
  admin/             /dev reload|load|unload|sync|extensions (관리자 전용, 자동완성 지원)
    __init__.py      setup() — Cog 등록
    commands.py      슬래시 명령어 (입력·응답)
    service.py       확장 기능 관리 로직 (Discord 응답과 분리)
  example/           새 도메인 작성 예시
    __init__.py
    commands.py
```

`domains/` 안에서 `__init__.py`가 있는 폴더는 시작할 때 자동으로 로드됩니다
(`_`로 시작하는 이름 제외). 새 기능은 `domains/example/`을 복사해 시작하고, `/dev load domains.<이름>`으로
재시작 없이 불러올 수 있습니다.

- 명령어에 `@respond()`를 `@app_commands.command` 아래에 붙이고 `(True, "완료")`나 `discord.Embed`를
  return하세요. 먼저 defer한 뒤 본인에게만 보이는 메시지로 응답합니다 (`@respond(defer=False)`로 끌 수 있음).
- 여러 도메인이 같이 쓰는 코드는 `domains/` 바로 아래 `.py`로 둡니다 (확장 기능으로 로드되지 않음).
  도메인끼리는 서로 import하지 마세요.
- 봇 자체의 기반 코드(설정, 오류 처리, `MyBot`)는 `core/`에 둡니다.
- `/dev reload`는 해당 도메인 폴더만 다시 읽습니다. 공용 모듈을 고쳤다면 봇을 재시작하세요.

`/dev`는 기본적으로 **관리자(Administrator) 권한**이 있는 사용자에게만 보입니다.
`administrator_role_ids`의 역할이 관리자 권한 없이 `/dev`를 쓰게 하려면, 서버 관리자가
**서버 설정 > 연동(Integrations) > 봇**에서 해당 역할에 명령어 사용을 허용해야 합니다.

슬래시 명령어 전용이라 메시지 캐시(`max_messages`)와 입력 중(typing) 이벤트는 꺼져 있습니다.
`on_message_edit`처럼 캐시가 필요한 이벤트를 쓰려면 `core/bot.py`에서 조정하세요.
