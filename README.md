# Discord_Bot_Frame-PYTHON

discord.py 2.x 기반 슬래시 명령어 봇 프레임.

## 실행
```bash
pip install -r requirements.txt
# config.yml 수정 (또는 토큰은 환경변수로)
set DISCORD_TOKEN=봇토큰   # Windows / Linux·macOS: export DISCORD_TOKEN=...
python main.py
```

## 구조
- `main.py` — 봇 본체. `command/` 폴더의 `.py`를 자동 로드 (`_`로 시작하는 파일 제외)
- `command/dev.py` — `/dev reload|load|unload|sync|extensions` (관리자 전용)
- `command/example.py` — 새 명령어 작성 예시
- `utils/checks.py` — `has_admin_role()` 권한 체크

개발 중엔 `config.yml`의 `dev_guild_id`를 설정하면 명령어가 해당 서버에 즉시 반영됩니다.
