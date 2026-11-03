from django.core.management import call_command
from django.db import migrations


def create_cache_table(apps, schema_editor):
    # Table behind CACHES["default"], which stores the API throttle counters.
    # Does nothing if the table already exists.
    call_command("createcachetable", database=schema_editor.connection.alias)


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_cache_table, migrations.RunPython.noop),
    ]
