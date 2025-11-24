from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0005_oersource_marcxml_url_alter_oersource_source_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='TalisPushJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('target_url', models.URLField(blank=True, null=True)),
                ('response_code', models.IntegerField(blank=True, null=True)),
                ('response_body', models.TextField(blank=True)),
                ('report_snapshot', models.JSONField(default=list, blank=True)),
            ],
            options={
                'verbose_name': 'Talis Push Job',
                'verbose_name_plural': 'Talis Push Jobs',
                'ordering': ['-created_at'],
            },
        ),
    ]
