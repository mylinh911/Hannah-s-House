#!/usr/bin/env python3
"""Django's command-line utility for administrative tasks."""
import os
import sys
import webbrowser

# Địa chỉ URL mặc định sau khi chạy runserver
default_url = 'http://127.0.0.1:8000/'

# Mở trình duyệt tự động với URL mặc định
webbrowser.open(default_url)

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerceSite.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
