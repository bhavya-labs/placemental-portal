"""
Administrative CLI bootstrap tool for AP-CPIP platform.

Provides protected, explicitly-invoked server-side administration operations
such as initial administrator provisioning.

Usage:
    python -m backend.app.cli create-admin --email admin@institution.edu --name "Administrator Name"
"""
import sys
import re
import argparse
import getpass
from typing import Optional
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal
from backend.app.models import User
from backend.app.auth import get_password_hash


EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
MIN_PASSWORD_LENGTH = 8


def validate_email(email: str) -> str:
    cleaned = email.strip().lower()
    if not EMAIL_REGEX.match(cleaned):
        raise ValueError(f"Invalid email address format: '{email}'")
    return cleaned


def validate_password(password: str) -> str:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
        )
    return password


def provision_admin(
    db: Session,
    email: str,
    name: str,
    password: str
) -> User:
    """
    Securely provisions an administrator account in the database.
    
    Validates uniqueness, enforces PBKDF2-HMAC-SHA256 password hashing,
    and returns the created User object without exposing credentials.
    """
    clean_email = validate_email(email)
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Administrator name cannot be empty.")
    
    validate_password(password)

    # Check email uniqueness
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise ValueError(f"User account with email '{clean_email}' already exists.")

    password_hash = get_password_hash(password)
    admin_user = User(
        email=clean_email,
        name=clean_name,
        password_hash=password_hash,
        role="admin"
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    return admin_user


def handle_create_admin(args):
    db = SessionLocal()
    try:
        email = args.email
        name = args.name

        password = args.password
        if not password:
            # Secure interactive password input without echo
            password = getpass.getpass("Enter administrator password: ")
            confirm = getpass.getpass("Confirm administrator password: ")
            if password != confirm:
                print("Error: Passwords do not match.", file=sys.stderr)
                sys.exit(1)

        user = provision_admin(db, email=email, name=name, password=password)
        print(f"Administrator account '{user.email}' (ID: {user.id}) provisioned successfully.")
    except ValueError as ve:
        print(f"Validation Error: {ve}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Provisioning Failed: {e}", file=sys.stderr)
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        prog="python -m backend.app.cli",
        description="Administrative CLI tool for AP-CPIP platform."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_admin_parser = subparsers.add_parser(
        "create-admin",
        help="Securely provision an initial or additional platform administrator."
    )
    create_admin_parser.add_argument(
        "--email",
        required=True,
        help="Official administrator email address."
    )
    create_admin_parser.add_argument(
        "--name",
        required=True,
        help="Full name of the administrator."
    )
    create_admin_parser.add_argument(
        "--password",
        required=False,
        default=None,
        help="Password for the account (optional; prompts securely if omitted)."
    )
    create_admin_parser.set_defaults(func=handle_create_admin)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
