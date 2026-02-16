"""
Tests for configuration helpers.

Tests for build_mysql_url_from_env() and validate_database_config() functions
in kiosk_show_replacement/config/__init__.py.
"""

import importlib


class TestBuildMysqlUrlFromEnv:
    """Tests for the build_mysql_url_from_env() helper function."""

    def test_returns_none_when_mysql_host_not_set(self, monkeypatch):
        """Returns None when MYSQL_HOST is not set."""
        monkeypatch.delenv("MYSQL_HOST", raising=False)
        from kiosk_show_replacement.config import build_mysql_url_from_env

        assert build_mysql_url_from_env() is None

    def test_returns_correct_url_with_all_vars(self, monkeypatch):
        """Returns correct MySQL URL when all required vars are set."""
        monkeypatch.setenv("MYSQL_HOST", "dbhost")
        monkeypatch.setenv("MYSQL_USER", "myuser")
        monkeypatch.setenv("MYSQL_PASSWORD", "mypass")
        monkeypatch.setenv("MYSQL_DATABASE", "mydb")
        monkeypatch.delenv("MYSQL_PORT", raising=False)
        from kiosk_show_replacement.config import build_mysql_url_from_env

        result = build_mysql_url_from_env()
        assert result == "mysql+pymysql://myuser:mypass@dbhost:3306/mydb"

    def test_returns_correct_url_with_custom_port(self, monkeypatch):
        """Returns correct URL with a custom MYSQL_PORT."""
        monkeypatch.setenv("MYSQL_HOST", "dbhost")
        monkeypatch.setenv("MYSQL_USER", "myuser")
        monkeypatch.setenv("MYSQL_PASSWORD", "mypass")
        monkeypatch.setenv("MYSQL_DATABASE", "mydb")
        monkeypatch.setenv("MYSQL_PORT", "3307")
        from kiosk_show_replacement.config import build_mysql_url_from_env

        result = build_mysql_url_from_env()
        assert result == "mysql+pymysql://myuser:mypass@dbhost:3307/mydb"

    def test_returns_none_when_user_missing(self, monkeypatch):
        """Returns None when MYSQL_USER is missing."""
        monkeypatch.setenv("MYSQL_HOST", "dbhost")
        monkeypatch.delenv("MYSQL_USER", raising=False)
        monkeypatch.setenv("MYSQL_PASSWORD", "mypass")
        monkeypatch.setenv("MYSQL_DATABASE", "mydb")
        from kiosk_show_replacement.config import build_mysql_url_from_env

        assert build_mysql_url_from_env() is None

    def test_returns_none_when_password_missing(self, monkeypatch):
        """Returns None when MYSQL_PASSWORD is missing."""
        monkeypatch.setenv("MYSQL_HOST", "dbhost")
        monkeypatch.setenv("MYSQL_USER", "myuser")
        monkeypatch.delenv("MYSQL_PASSWORD", raising=False)
        monkeypatch.setenv("MYSQL_DATABASE", "mydb")
        from kiosk_show_replacement.config import build_mysql_url_from_env

        assert build_mysql_url_from_env() is None

    def test_returns_none_when_database_missing(self, monkeypatch):
        """Returns None when MYSQL_DATABASE is missing."""
        monkeypatch.setenv("MYSQL_HOST", "dbhost")
        monkeypatch.setenv("MYSQL_USER", "myuser")
        monkeypatch.setenv("MYSQL_PASSWORD", "mypass")
        monkeypatch.delenv("MYSQL_DATABASE", raising=False)
        from kiosk_show_replacement.config import build_mysql_url_from_env

        assert build_mysql_url_from_env() is None

    def test_url_encodes_special_characters(self, monkeypatch):
        """URL-encodes special characters in user and password."""
        monkeypatch.setenv("MYSQL_HOST", "dbhost")
        monkeypatch.setenv("MYSQL_USER", "my@user")
        monkeypatch.setenv("MYSQL_PASSWORD", "p@ss:w/rd")
        monkeypatch.setenv("MYSQL_DATABASE", "mydb")
        monkeypatch.delenv("MYSQL_PORT", raising=False)
        from kiosk_show_replacement.config import build_mysql_url_from_env

        result = build_mysql_url_from_env()
        assert result == ("mysql+pymysql://my%40user:p%40ss%3Aw%2Frd@dbhost:3306/mydb")


class TestValidateDatabaseConfig:
    """Tests for the validate_database_config() function."""

    def test_no_issues_with_mysql_url_in_production(self, monkeypatch):
        """No issues when production uses a MySQL URL."""
        monkeypatch.delenv("MYSQL_HOST", raising=False)
        from kiosk_show_replacement.config import validate_database_config

        issues = validate_database_config(
            "production", "mysql+pymysql://user:pass@host:3306/db"
        )
        assert issues == []

    def test_no_issues_with_sqlite_in_development(self, monkeypatch):
        """No issues when development uses SQLite without MYSQL_* vars."""
        monkeypatch.delenv("MYSQL_HOST", raising=False)
        from kiosk_show_replacement.config import validate_database_config

        issues = validate_database_config("development", "sqlite:///dev.db")
        assert issues == []

    def test_error_on_sqlite_in_production(self, monkeypatch):
        """Error when production resolves to SQLite."""
        monkeypatch.delenv("MYSQL_HOST", raising=False)
        from kiosk_show_replacement.config import validate_database_config

        issues = validate_database_config("production", "sqlite:///kiosk_show.db")
        assert len(issues) == 1
        assert issues[0][0] == "error"
        assert "Production" in issues[0][1]
        assert "SQLite" in issues[0][1]

    def test_error_on_partial_mysql_config(self, monkeypatch):
        """Error when MYSQL_HOST is set but required vars are missing."""
        monkeypatch.setenv("MYSQL_HOST", "dbhost")
        monkeypatch.delenv("MYSQL_USER", raising=False)
        monkeypatch.setenv("MYSQL_PASSWORD", "pass")
        monkeypatch.delenv("MYSQL_DATABASE", raising=False)
        from kiosk_show_replacement.config import validate_database_config

        issues = validate_database_config("production", "mysql+pymysql://x:x@host/db")
        errors = [i for i in issues if i[0] == "error"]
        assert len(errors) >= 1
        assert "MYSQL_USER" in errors[0][1]
        assert "MYSQL_DATABASE" in errors[0][1]

    def test_warning_on_mysql_vars_with_sqlite_uri(self, monkeypatch):
        """Warning when MYSQL_* vars are set but URI is SQLite."""
        monkeypatch.setenv("MYSQL_HOST", "dbhost")
        monkeypatch.setenv("MYSQL_USER", "user")
        monkeypatch.setenv("MYSQL_PASSWORD", "pass")
        monkeypatch.setenv("MYSQL_DATABASE", "db")
        from kiosk_show_replacement.config import validate_database_config

        issues = validate_database_config("development", "sqlite:///dev.db")
        warnings = [i for i in issues if i[0] == "warning"]
        assert len(warnings) == 1
        assert "MYSQL_*" in warnings[0][1]
        assert "SQLite" in warnings[0][1]

    def test_no_issues_in_testing_with_sqlite(self, monkeypatch):
        """No issues when testing config uses SQLite."""
        monkeypatch.delenv("MYSQL_HOST", raising=False)
        from kiosk_show_replacement.config import validate_database_config

        issues = validate_database_config("testing", "sqlite:///:memory:")
        assert issues == []

    def test_no_issues_with_postgresql_in_production(self, monkeypatch):
        """No issues when production uses PostgreSQL."""
        monkeypatch.delenv("MYSQL_HOST", raising=False)
        from kiosk_show_replacement.config import validate_database_config

        issues = validate_database_config(
            "production", "postgresql://user:pass@host:5432/db"
        )
        assert issues == []


class TestProductionConfigResolution:
    """Tests for ProductionConfig.SQLALCHEMY_DATABASE_URI resolution."""

    def test_uses_database_url_when_set(self, monkeypatch):
        """ProductionConfig uses DATABASE_URL env var when set."""
        monkeypatch.setenv("DATABASE_URL", "mysql+pymysql://u:p@h:3306/db")
        monkeypatch.delenv("MYSQL_HOST", raising=False)
        import kiosk_show_replacement.config as config_module

        importlib.reload(config_module)
        assert (
            config_module.ProductionConfig.SQLALCHEMY_DATABASE_URI
            == "mysql+pymysql://u:p@h:3306/db"
        )

    def test_constructs_from_mysql_vars(self, monkeypatch):
        """ProductionConfig constructs URL from MYSQL_* vars when DATABASE_URL not set."""
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("MYSQL_HOST", "myhost")
        monkeypatch.setenv("MYSQL_USER", "myuser")
        monkeypatch.setenv("MYSQL_PASSWORD", "mypass")
        monkeypatch.setenv("MYSQL_DATABASE", "mydb")
        monkeypatch.delenv("MYSQL_PORT", raising=False)
        import kiosk_show_replacement.config as config_module

        importlib.reload(config_module)
        assert (
            config_module.ProductionConfig.SQLALCHEMY_DATABASE_URI
            == "mysql+pymysql://myuser:mypass@myhost:3306/mydb"
        )

    def test_falls_back_to_sqlite(self, monkeypatch):
        """ProductionConfig falls back to SQLite when nothing configured."""
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("MYSQL_HOST", raising=False)
        import kiosk_show_replacement.config as config_module

        importlib.reload(config_module)
        assert (
            config_module.ProductionConfig.SQLALCHEMY_DATABASE_URI
            == "sqlite:///kiosk_show.db"
        )
