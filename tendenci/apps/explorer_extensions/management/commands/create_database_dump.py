from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string


class Command(BaseCommand):
    """
    Database Dump

    Usage:
        python manage.py create_database_dump <user_id> <export_format>

        example:
        python manage.py create_database_dump 1 json

    """
    def handle(self, *args, **options):
        import datetime
        import uuid
        from StringIO import StringIO
        from django.core.management import call_command
        from django.core.files import File
        from django.contrib.auth.models import User
        from tendenci.apps.emails.models import Email
        from tendenci.apps.explorer_extensions.models import DatabaseDumpFile, VALID_FORMAT_CHOICES
        from tendenci.apps.site_settings.utils import get_setting

        dump_obj = DatabaseDumpFile()

        user_id = int(args[0])

        if user_id == 0:
            msg = 'User ID is required. Usage: ./manage.py create_database_dump <user_id>'
            raise CommandError(msg)

        author = User.objects.filter(pk=user_id)
        if author.exists():
            author = author[0]
        else:
            author = None

        if not author:
            raise CommandError('Nonexistent user.')

        dump_obj.author = author

        fmt = None
        if len(args) > 1:
            fmt = args[1]

        if not fmt:
            raise CommandError('Format is required. Usage: ./manage.py create_database_dump <user_id>')
        if fmt not in VALID_FORMAT_CHOICES:
            raise CommandError('Format %s is not supported. Please use one of the following: %s' % (fmt, VALID_FORMAT_CHOICES))

        dump_obj.export_format = fmt
        dump_obj.save()

        print "Creating database dump..."

        content = StringIO()
        call_command('dumpdata', format=fmt, stdout=content, exclude=['captcha.captchastore', 'files.multiplefile', 'events.standardregform', 'help_files', 'explorer_extensions'])

        dump_obj.dbfile.save(str(uuid.uuid1()), File(content))

        dump_obj.status = "completed"
        dump_obj.save()

        # File is created.
        # TODO: Send email to author

        print "Done!"
