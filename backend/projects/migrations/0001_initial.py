from django.db import migrations, models
import django.conf


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('active', 'активен'), ('closed', 'закрыт')], default='active', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Stage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('project', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='stages', to='projects.project')),
            ],
        ),
        migrations.CreateModel(
            name='BuildObject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('type', models.CharField(blank=True, max_length=255)),
                ('address', models.CharField(blank=True, max_length=255)),
                ('description', models.TextField(blank=True)),
                ('project', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='build_objects', to='projects.project')),
            ],
        ),
        migrations.AddField(
            model_name='project',
            name='members',
            field=models.ManyToManyField(blank=True, related_name='projects', to=django.conf.settings.AUTH_USER_MODEL),
        ),
    ]