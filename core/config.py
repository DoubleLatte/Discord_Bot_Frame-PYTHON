import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigError(Exception):
    """설정 파일이 없거나 값이 올바르지 않을 때 발생"""


def _to_id(value: Any, key: str) -> int:
    """Discord ID(snowflake) 값을 int로 변환. 따옴표로 감싼 숫자도 허용"""
    if isinstance(value, bool):
        raise ConfigError(f"'{key}' 값이 올바른 ID가 아닙니다: {value!r}")
    try:
        result = int(value)
    except (TypeError, ValueError):
        raise ConfigError(f"'{key}' 값이 올바른 ID가 아닙니다: {value!r}") from None
    if result <= 0:
        raise ConfigError(f"'{key}' 값이 올바른 ID가 아닙니다: {value!r}")
    return result


def _optional_id(value: Any, key: str) -> int | None:
    return None if value in (None, "") else _to_id(value, key)


@dataclass(frozen=True, slots=True)
class Config:
    """봇 설정 (읽기 전용). Config.load()로 생성"""

    token: str
    application_id: int | None
    dev_guild_id: int | None
    activity: str
    admin_role_ids: frozenset[int]

    def __repr__(self) -> str:
        # 로그에 토큰이 찍히지 않도록 가림
        return (
            f"Config(token='***', application_id={self.application_id}, "
            f"dev_guild_id={self.dev_guild_id}, activity={self.activity!r}, "
            f"admin_role_ids={set(self.admin_role_ids)})"
        )

    @classmethod
    def load(cls, path: Path) -> "Config":
        """YAML 파일에서 설정을 읽고 검증. 토큰은 DISCORD_TOKEN 환경변수가 우선"""
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except FileNotFoundError:
            raise ConfigError(f"{path} 파일을 찾을 수 없습니다.") from None
        except yaml.YAMLError as e:
            raise ConfigError(f"{path} 파일 읽기 실패 - {e}") from None
        if not isinstance(raw, dict):
            raise ConfigError(f"{path} 최상위 구조는 key: value 형식이어야 합니다.")

        token = os.getenv("DISCORD_TOKEN") or raw.get("token")
        if not isinstance(token, str) or not token.strip():
            raise ConfigError("토큰이 없습니다. DISCORD_TOKEN 환경변수나 config.yml의 token을 설정하세요.")

        role_ids = raw.get("administrator_role_ids") or []
        if not isinstance(role_ids, list):
            raise ConfigError("'administrator_role_ids'는 목록(- 항목) 형식이어야 합니다.")

        return cls(
            token=token.strip(),
            application_id=_optional_id(raw.get("application_id"), "application_id"),
            dev_guild_id=_optional_id(raw.get("dev_guild_id"), "dev_guild_id"),
            activity=str(raw.get("activity") or "~~~ 하는중"),
            admin_role_ids=frozenset(_to_id(r, "administrator_role_ids") for r in role_ids),
        )
