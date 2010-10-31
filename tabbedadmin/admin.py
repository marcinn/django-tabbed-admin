from django.contrib import admin
from django.forms.models import modelform_factory
from django.contrib.admin.util import flatten_fieldsets
from django.core.exceptions import ImproperlyConfigured
import forms
import sets

class TabbedModelAdmin(admin.ModelAdmin):
    form = forms.TabbedForm
    change_form_template = 'admin/change_form_tabbed.html'
    tabs_order = []

    def __init__(self, model, admin_site):
        self.current_tab = 'common'
        self.tab_inline_instances = {}
        self.old_inline_instances = []
        super(TabbedModelAdmin, self).__init__(model, admin_site)
        for tab_name in self.tabs:
            if self.tabs[tab_name].has_key('inlines'):
                self.tab_inline_instances[tab_name] = []
                for inline_class in self.tabs[tab_name]['inlines']:
                    inline_instance = inline_class(self.model, self.admin_site)
                    self.tab_inline_instances[tab_name].append(inline_instance)
        if self.prepopulated_fields:
            raise ImproperlyConfigured("""Invalid configuration."""
                    """Move prepopulated fields to tabs section""")

    def __call__(self, request, url):
        # fixme: use first declared, not hardcoded common
        self.current_tab  = request._get_request().get('tab',self.current_tab) 
        return super(TabbedModelAdmin, self).__call__(request, url)

    def response_change(self, request, obj):
        response = super(TabbedModelAdmin, self).response_change(request,obj)
        if request._get_request().has_key('tab'):
            response['Location'] += '?tab=%s' % request._get_request()['tab']
        return response

    def get_fieldsets(self, request, obj=None):
        if self.tabs.has_key(self.current_tab) and self.tabs[self.current_tab].has_key('fieldsets'):
            return self.tabs[self.current_tab]['fieldsets']
        raise Http404(_('Tab does not exists: %(name)r') % {'name': self.current_tab})

    def get_formsets(self, request, obj=None):
        for inline in self.tab_inline_instances.get(self.current_tab, []):
            yield inline.get_formset(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        """
        Returns a Form class for use in the admin add view. This is used by
        add_view and change_view.
        """
        if self.declared_fieldsets is not None:
            fields = flatten_fieldsets(self.declared_fieldsets)
        else:
            fields = None
        if self.exclude is None:
            exclude = []
        else:
            exclude = list(self.exclude)
        defaults = {
            "form": self.form,
            "fields": fields,
            "exclude": exclude + kwargs.get("exclude", []),
            "formfield_callback": self.formfield_for_dbfield,
        }
        defaults.update(kwargs)
        form = modelform_factory(self.model, **defaults)

        # dirty hack for not declared fields in current tab
        if fields is not None and not fields:
            form.fields = []
            form.base_fields = {}
        return form

    def change_view(self, request, object_id, extra_context=None):
        self.current_tab  = request._get_request().get('tab','common') 
        extra_context = extra_context or {}
        tab_list = []
        for t in self.tabs_order or self.tabs.keys():
            tab_list.append((t, self.tabs[t]['title'] if self.tabs[t].has_key('title') else _(t)))
        extra_context.update({
            'tabs': tab_list,
            'current_tab': self.current_tab,
            })
        return super(TabbedModelAdmin, self).change_view(request, object_id, extra_context)

    def _declared_fieldsets(self):
        if self.current_tab:
            if self.tabs.has_key(self.current_tab) and self.tabs[self.current_tab].has_key('fieldsets'):
                return self.tabs[self.current_tab]['fieldsets']
        raise ImproperlyConfigured('Invalid fieldsets configuration')

    def _get_inline_instances(self):
        if self.current_tab:
            return self.tab_inline_instances.get(self.current_tab, [])
        return self.old_inline_instances

    def _set_inline_instances(self, val):
        if self.current_tab:
            self.tab_inline_instances[self.current_tab] = val
        else:
            self.old_inline_instances = val

    """
    def _prepopulated_fields(self):
        if self.tabs.has_key(self.current_tab) and self.tabs[self.current_tab].has_key('prepopulated_fields'):
            return self.tabs[self.current_tab]['prepopulated_fields']
        return {}
    """

    inline_instances = property(_get_inline_instances, _set_inline_instances)
    declared_fieldsets = property(_declared_fieldsets)
    """
    prepopulated_fields = property(_prepopulated_fields)
    """


