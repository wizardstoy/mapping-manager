
# (C) British Crown Copyright 2011 - 2012, Met Office
#
# This file is part of metOcean-mapping.
#
# metOcean-mapping is free software: you can redistribute it and/or 
# modify it under the terms of the GNU Lesser General Public License 
# as published by the Free Software Foundation, either version 3 of 
# the License, or (at your option) any later version.
#
# metOcean-mapping is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with metOcean-mapping. If not, see <http://www.gnu.org/licenses/>.


from models import BaseShard, State, Provenance

import prefixes

from settings import READ_ONLY
from django import forms


class BulkLoadForm(forms.Form):
    file = forms.FileField(
        label = 'Select a CSV file to upload',
        help_text = 'maximum size 2MB',
        required=False) 


class ShardForm(forms.ModelForm):
    class Meta:
        model = BaseShard
        exclude = ('baseshardMD5',)

    def __init__(self, *args, **kwargs):
        super(ShardForm, self).__init__(*args, **kwargs)
        self.fields['current_status'] = forms.CharField(max_length=15)
        if self.initial.has_key('metadata_element'):
            self.fields['metadata_element'].widget.attrs['readonly'] = True
            #self.fields['metadata_element'].widget.attrs['disabled'] = "disabled"
        if READ_ONLY:
            for fieldname in self.fields:
                self.fields[fieldname].widget.attrs['readonly'] = True
                self.fields[fieldname].widget.attrs['disabled'] = 'disabled'

    def clean(self):
        if READ_ONLY:
            raise ValidationError('System in Read-Only mode') 
        else:
            return self.cleaned_data


class ProvenanceForm(forms.ModelForm):
    required_css_class = 'required'
    error_css_class = 'error'
    class Meta:
        model = Provenance
        exclude = ('provenanceMD5', 'baseshardMD5', 'owners')
        widgets = {
            'standard_name' : forms.TextInput(attrs={'size' : 60}),
            'local_name' : forms.TextInput(attrs={'size' : 60}),
            'long_name' : forms.TextInput(attrs={'size' : 60}),
            'comment' : forms.TextInput(attrs={'size' : 60}),
            'reason' : forms.TextInput(attrs={'size' : 60}),
        }

    def __init__(self, *args, **kwargs):
        super(ProvenanceForm, self).__init__(*args, **kwargs)
        self.fields['current_status'].widget.attrs['readonly'] = True
        self.fields['last_edit'].widget.attrs['readonly'] = True
        self.fields['version'].widget.attrs['readonly'] = True
        # now need to generate the 'editor', 'owners' and 'watchers' fields
        states = State()
        self.fields['next_status'] = forms.ChoiceField(choices=[(x,x) for x in states.get_states])

