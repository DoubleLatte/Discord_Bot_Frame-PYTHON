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
- `main.py` — 진입점. `command/` 폴더의 `.py`를 자동 로드 (`_`로 시작하는 파일 제외)
- `command/dev.py` — `/dev reload|load|unload|sync|extensions` (관리자 전용, 확장 이름 자동완성 지원)
- `command/example.py` — 새 명령어 작성 예시
- `core/config.py` — 설정 로드·검증 (읽기 전용 `Config`)
- `core/bot.py` — `MyBot` (Cog 자동 로드, 동기화, 공통 오류 처리, `is_admin`)
- `core/checks.py` — `has_admin_role()` 권한 체크

`/dev`는 기본적으로 **관리자(Administrator) 권한**이 있는 사용자에게만 보입니다.
`administrator_role_ids`의 역할이 관리자 권한 없이 `/dev`를 쓰게 하려면, 서버 관리자가
**서버 설정 > 연동(Integrations) > 봇**에서 해당 역할에 명령어 사용을 허용해야 합니다.

슬래시 명령어 전용이라 메시지 캐시(`max_messages`)와 입력 중(typing) 이벤트는 꺼져 있습니다.
`on_message_edit`처럼 캐시가 필요한 이벤트를 쓰려면 `core/bot.py`에서 조정하세요.
