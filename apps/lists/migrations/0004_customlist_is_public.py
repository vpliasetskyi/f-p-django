from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lists', '0003_customlistitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='customlist',
            name='is_public',
            field=models.BooleanField(default=False),
        ),
    ]
