import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0002_contentitem_vote_average'),
        ('lists', '0002_customlist'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomListItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('custom_poster', models.ImageField(blank=True, null=True, upload_to='custom_posters/')),
                ('custom_title', models.CharField(blank=True, max_length=255)),
                ('order', models.PositiveIntegerField(default=0)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('content_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='custom_list_entries', to='content.contentitem')),
                ('custom_list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='list_items', to='lists.customlist')),
            ],
            options={
                'ordering': ['order', 'added_at'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='customlistitem',
            unique_together={('custom_list', 'content_item')},
        ),
        migrations.RemoveField(
            model_name='customlist',
            name='items',
        ),
        migrations.AddField(
            model_name='customlist',
            name='items',
            field=models.ManyToManyField(blank=True, related_name='in_lists', through='lists.CustomListItem', to='content.contentitem'),
        ),
    ]
