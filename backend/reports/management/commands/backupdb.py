from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command
import os
import datetime
import shutil

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        base_dir = settings.BASE_DIR
        backups_dir = os.path.join(base_dir, "backups")
        os.makedirs(backups_dir, exist_ok=True)
        engine = settings.DATABASES["default"]["ENGINE"]
        if "sqlite3" in engine:
            name = settings.DATABASES["default"]["NAME"]
            src = name if isinstance(name, str) else str(name)
            dst = os.path.join(backups_dir, f"sqlite-backup-{now}.db")
            shutil.copyfile(src, dst)
            self.stdout.write(self.style.SUCCESS(f"SQLite backup created: {dst}"))
        else:
            out = os.path.join(backups_dir, f"dump-{now}.json")
            with open(out, "w", encoding="utf-8") as f:
                call_command("dumpdata", format="json", indent=2, stdout=f)
            self.stdout.write(self.style.SUCCESS(f"JSON dump created: {out}"))