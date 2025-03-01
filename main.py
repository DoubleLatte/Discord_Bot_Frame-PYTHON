import sys
import os
import yaml
import discord
from discord.ext import commands
from discord import Game, Status

def resource_path(relative_path: str) -> str:
    """리소스 파일의 절대 경로 반환 (개발 및 PyInstaller 환경 지원)"""
    try:
        base_path = sys._MEIPASS  # PyInstaller 환경
    except AttributeError:
        base_path = os.path.abspath(".")  # 일반 실행 환경
    return os.path.join(base_path, relative_path)

def load_config() -> dict:
    """config.yml 파일에서 설정 불러오기"""
    config_path = "config.yml"
    try:
        with open(config_path, "r", encoding="utf-8") as config_file:
            return yaml.safe_load(config_file)
    except FileNotFoundError:
        sys.exit(f"오류: {config_path} 파일을 찾을 수 없습니다.")
    except yaml.YAMLError as e:
        sys.exit(f"오류: {config_path} 파일 읽기 실패 - {e}")

class MyBot(commands.Bot):
    def __init__(self, config: dict):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix="!",
            intents=intents,
            application_id=config.get("application_id")
        )
        self.config = config
        self.extensions_list = ["command.paper", "command.dev"]  # 확장 기능 리스트
    
    async def setup_hook(self):
        """봇 초기 설정 및 확장 기능 로드"""
        for ext in self.extensions_list:
            try:
                await self.load_extension(ext)
                print(f"확장 기능 로드 성공: {ext}")
            except commands.ExtensionError as e:
                print(f"오류: 확장 기능 {ext} 로드 실패 - {e}")

        try:
            synced = await self.tree.sync()
            print(f"{len(synced)}개 명령어 동기화 완료")
        except discord.HTTPException as e:
            print(f"명령어 트리 동기화 오류: {e}")

    async def on_ready(self):
        """봇이 준비되었을 때 실행되는 이벤트"""
        print(f"\n==============="
              f"\n봇 온라인 상태"
              f"\n이름: {self.user.name}"
              f"\nID: {self.user.id}"
              f"\n===============")
        await self.change_presence(status=Status.online, activity=Game("~~~ 하는중"))

def main():
    """봇 실행 함수"""
    config = load_config()
    bot = MyBot(config)
    try:
        print("봇 시작 중...")
        bot.run(config["token"])
    except KeyError:
        sys.exit("오류: config.yml에서 'token'을 찾을 수 없습니다.")
    except discord.LoginFailure:
        sys.exit("오류: 로그인 실패. 토큰이 올바른지 확인하세요.")
    except Exception as e:
        sys.exit(f"예상치 못한 오류 발생: {e}")

if __name__ == "__main__":
    main()
