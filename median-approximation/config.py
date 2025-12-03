from pydantic_settings import BaseSettings


class Config(BaseSettings):
    TINVEST_TOKEN: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Config()  # pyright: ignore[reportCallIssue]
