from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://kundenportal:kundenportal@localhost:5433/kundenportal"
    log_level: str = "INFO"

    # Auth
    jwt_secret: str = "CHANGE_ME_IN_PRODUCTION_USE_RANDOM_32_CHARS"
    jwt_expire_hours: int = 8
    initial_admin_password: str = "changeme"  # Wird beim ersten Start gesetzt

    # Adapter-Provider
    signature_provider: str = "inhouse"  # einziger Signatur-Provider
    avv_provider: str = "stub"
    target_system_provider: str = "stub"
    notification_provider: str = "stub"

    # Dokumentenablage (generierte/signierte PDFs)
    documents_dir: str = "data/documents"

    # In-Portal-Signatur (signature_provider=inhouse): Siegel-Zertifikat (PKCS#12).
    # Bleibt der Pfad leer, wird beim ersten Signieren ein selbstsigniertes
    # Zertifikat erzeugt und unter <documents_dir>/../signing/ abgelegt.
    signing_cert_path: str = ""
    signing_cert_password: str = ""

    # Deployment
    domain: str = "heihaf.kiste.org"


settings = Settings()
