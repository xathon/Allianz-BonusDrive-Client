import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch


def test_save_tgt_to_env_creates_new_file():
    """Test that save_tgt_to_env creates a .env file if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            # Mock TGT env var to prevent input() prompt at module level
            with patch.dict(os.environ, {"TGT": "existing_tgt"}):
                from allianz_bonusdrive_client.cli import save_tgt_to_env
            
            # Remove any existing .env to test creation
            env_file = Path(tmpdir) / ".env"
            if env_file.exists():
                env_file.unlink()
            
            save_tgt_to_env("test_tgt_token")
            
            env_path = Path(tmpdir) / ".env"
            assert env_path.exists()
            content = env_path.read_text()
            assert "TGT=" in content
            assert "test_tgt_token" in content
        finally:
            os.chdir(original_cwd)


def test_save_tgt_to_env_updates_existing_file():
    """Test that save_tgt_to_env updates an existing .env file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            # Create existing .env file
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("PHOTON_URL=http://example.com\n")
            
            # Mock TGT env var to prevent input() prompt at module level
            with patch.dict(os.environ, {"TGT": "existing_tgt"}):
                from allianz_bonusdrive_client.cli import save_tgt_to_env
            
            save_tgt_to_env("new_tgt_token")
            
            content = env_path.read_text()
            assert "PHOTON_URL=http://example.com" in content
            assert "TGT=" in content
            assert "new_tgt_token" in content
        finally:
            os.chdir(original_cwd)
