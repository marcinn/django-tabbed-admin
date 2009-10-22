from django import forms
from django.conf import settings


class TabbedForm(forms.ModelForm):

    class Media:
        css = {'all': ('%s/tabbedadmin/css/tabs.css' % settings.ADMIN_MEDIA_PREFIX,) }

