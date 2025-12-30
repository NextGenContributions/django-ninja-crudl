update-test-migrations:
    find tests/test_django/app/migrations/ -name "*.py" -not -name "__init__.py" -delete
    just make-test-migrations

make-test-migrations:
    DJANGO_SETTINGS_MODULE="tests.test_django.settings" django-admin makemigrations
