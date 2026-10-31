import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigError(Exception):
    """설정 파일이 없거나 값이 올바르지 않을 때 발생"""


def _to_id(value: Any, key: str) -> int:
    """Discord ID(snowflake) 값을 int로 변환. 따옴표로 감싼 숫자도 허용"""
    # bool은 int의 하위 타입, float는 큰 ID에서 정밀도가 손실되므로 거부
    if isinstance(value, (bool, float)):
        raise ConfigError(f"'{key}' 값이 올바른 ID가 아닙니다: {value!r}")
    try:
        result = int(value)
    except (TypeError, ValueError):
        raise ConfigError(f"'{key}' 값이 올바른 ID가 아닙니다: {value!r}") from None
    if result <= 0:
        raise ConfigError(f"'{key}' 값이 올바른 ID가 아닙니다: {value!r}")
    return result


def _optional_id(value: Any, key: str) -> int | None:
    return None if value is None or str(value).strip() == "" else _to_id(value, key)


def _to_bool(value: Any, key: str, default: bool) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ConfigError(f"'{key}' 값은 true 또는 false여야 합니다: {value!r}")
    return value


@dataclass(frozen=True, slots=True)
class Config:
    """봇 설정 (읽기 전용). Config.load()로 생성"""

    token: str
    application_id: int | None
    dev_guild_id: int | None
    activity: str | None
    admin_role_ids: frozenset[int]
    members_intent: bool = False

    def __repr__(self) -> str:
        # 로그에 토큰이 찍히지 않도록 가림
        return (
            f"Config(token='***', application_id={self.application_id}, "
            f"dev_guild_id={self.dev_guild_id}, activity={self.activity!r}, "
            f"admin_role_ids={set(self.admin_role_ids)}, members_intent={self.members_intent})"
        )

    @classmethod
    def load(cls, path: Path) -> "Config":
        """YAML 파일에서 설정을 읽고 검증. 토큰은 DISCORD_TOKEN 환경변수가 우선"""
        try:
            # utf-8-sig: 메모장 등이 붙이는 BOM도 허용
            raw = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
        except FileNotFoundError:
            raise ConfigError(f"{path} 파일을 찾을 수 없습니다.") from None
        except UnicodeDecodeError:
            raise ConfigError(f"{path} 파일을 UTF-8로 저장하세요.") from None
        except OSError as e:
            raise ConfigError(f"{path} 파일 읽기 실패 - {e}") from None
        except yaml.YAMLError as e:
            raise ConfigError(f"{path} 파일 읽기 실패 - {e}") from None
        if not isinstance(raw, dict):
            raise ConfigError(f"{path} 최상위 구조는 key: value 형식이어야 합니다.")

        token = (os.getenv("DISCORD_TOKEN") or "").strip() or raw.get("token")
        if not isinstance(token, str) or not token.strip():
            raise ConfigError("토큰이 없습니다. DISCORD_TOKEN 환경변수나 config.yml의 token을 설정하세요.")

        role_ids = raw.get("administrator_role_ids")
        if role_ids is None:
            role_ids = []
        elif not isinstance(role_ids, list):
            role_ids = [role_ids]  # 하나만 적은 경우도 허용

        activity = raw.get("activity")
        activity = str(activity).strip() if activity is not None else ""

        return cls(
            token=token.strip(),
            application_id=_optional_id(raw.get("application_id"), "application_id"),
            dev_guild_id=_optional_id(raw.get("dev_guild_id"), "dev_guild_id"),
            activity=activity or None,
            admin_role_ids=frozenset(_to_id(r, "administrator_role_ids") for r in role_ids),
            members_intent=_to_bool(raw.get("members_intent"), "members_intent", default=False),
        )
