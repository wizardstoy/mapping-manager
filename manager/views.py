
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


# Create your views here.
import sys
import os
import re
import urllib
from itertools import groupby
import datetime

import forms
import models
import query

import prefixes

from settings import READ_ONLY

from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.utils.safestring import mark_safe
from django.forms.formsets import formset_factory
from django.forms.models import inlineformset_factory

def contact(request, contact_id):
    pass


def contacts(request):
    pass


def provenance(request, provenance_id):
    pass


def provenances(request):
    # report in column view
    pass

def newshard(request, status, datatype):
    ShardFormSet = formset_factory(forms.ProvenanceForm, extra=0)
    if request.method == 'POST':
        formset = ShardFormSet(request.POST)
        if formset.is_valid():
            pass
    else:
        shard = request.GET.get('ref', '')
        shard = urllib.unquote(shard).decode('utf8')

        formset = ShardFormSet(initial=[
            {
            'current_status' : status.lower(),
            'last_edit' : datetime.datetime.now(),
            }])
    return render_to_response('main.html',
        RequestContext(request, {
            'title' : 'New shard',
            'viewname' : 'New shard',
            'status' : 'status: %s' % status.upper(),
            'detail' : 'Datatype: %s' % datatype,
            'read_only' : READ_ONLY,
            'formset' : formset,
            }) )

def edit(request, status, datatype):
    shard = request.GET.get('ref', '')
    shard = urllib.unquote(shard).decode('utf8')
    state = models.State(state=status)
    paths = shard.split('/')
    prefix = '/'.join(paths[:-2]) + '/'
    localname = paths[-2]
    pre = prefixes.Prefixes()
    md_element = pre.value2key(prefix)

    # will we need to call custom code here for different types?
    ShardFormSet = formset_factory(forms.ProvenanceForm, extra=0)
    warning_msg = ''
    if request.method == 'POST':
        formset = ShardFormSet(request.POST)
        if formset.is_valid():
            pass
        else:
            print formset.errors
    else:
        ushardm = get_shard(shard, status, datatype)
        if len(ushardm) > 1:
            warning_msg = (
                'Warning: '
                'More than one Data Shard with the same name at status "%s" found.' % status.upper())
        initial_data_set = []
        for item in ushardm:
            data_set = {}
            data_set = dict(
                metadata_element = md_element,
                local_name = localname,
                current_status = state,
                standard_name = item.get('cfname'),
                unit = item.get('unit'),
                long_name = '')
            initial_data_set.append(data_set)
        formset = ShardFormSet(initial=initial_data_set)
    return render_to_response('main.html',
        RequestContext(request, {
            'viewname' : 'Edit Shard',
            'status' : 'Status: %s, datatype: %s' % (status.upper(), datatype),
            'title' : 'Edit Shard: %s' % shard,
            'detail' : 'Shard: %s' % shard,
            'formset' : formset,
            'read_only' : READ_ONLY,
            'error' : warning_msg,
            }) )

# what shall we do here for multiple cfnames?
def get_shard(shard, status, datatype):
    qstr = '''
    SELECT DISTINCT ?cfname ?unit ?canon_unit 
    WHERE
    {
        {
        # drawing upon stash2cf.ttl as linkage
        <%s> cf:units ?unit ;
                cf:name ?cfname .
        # drawing upon cf-standard-name.ttl as endpoint
        ?cfname cf:canonical_units ?canon_unit .
        }
        UNION
        {
        # drawing upon stash2cf.ttl as linkage
        <%s> a mon:none .
        BIND( URI(mon:none) as ?cfname ) .
        }
    } 
    ''' % (shard, shard)
    results = query.run_query(qstr)
    return results

def shards(request):
    # report in column view
    pass


def shard_bulk_load(request):
    # CSV file upload and report in column view for validation
    pass

def get_counts_by_graph(graphurl=''):
    qstr = '''
        SELECT ?g (COUNT(DISTINCT ?s) as ?count)
        WHERE {
            GRAPH ?g { ?s ?p ?o } .
            FILTER( REGEX(str(?g), '%s') ) .
        }
        GROUP by ?g
        ORDER by ?g
    ''' % graphurl
    results = query.run_query(qstr)
    return results

def count_by_group(results, keyfunc):
    uniquetype = {}
    for k, g in groupby(results, keyfunc):
        uniquetype[k] = reduce(lambda x,y: int(x) + int(y), [x.get('count') for x in g], 0)
    return uniquetype

def split_by_datatype(name):
    return name.split('.')[0]

def split_by_type(item):
    name = item.get('g').split('/')[3]
    return split_by_datatype(name)

def split_by_status(item):
    name = item.get('g').split('/')[2]
    return name

def split_by_localname(item):
    name = item.get('g').split('/')[-1]
    return name

def tasks(request):
    state = models.State()
    itemlist = []
    resultsd = count_by_group(get_counts_by_graph(), split_by_status)
    for item in state.get_states:
        name = item.lower()
        itemlist.append( {
            'url' : reverse('list', kwargs={'status' : name}),
            'label' : item, 
            'count' : resultsd.get(name, 0),
        } )
    return render_to_response('tasks.html',
        RequestContext(request, {
            'title' : 'Tasks',
            'itemlist' : itemlist,
            }) )
    
def url_with_querystring(path, **kwargs):
    return path + '?' + urllib.urlencode(kwargs)

def list(request, status):
    reportq = '''
        SELECT DISTINCT ?g
        WHERE {
            GRAPH ?g { ?s ?p ?o } .
            FILTER( REGEX(str(?g), 'http://%s/') ) .
        }
    ''' % (status.lower(), )
    results = query.run_query(reportq)
    itemlist = []
    count_results = get_counts_by_graph('http://%s/' % status.lower())
    status_resultsd = count_by_group(count_results, split_by_status)
    for item in results:
        url = reverse('listtype', kwargs={
            'status' : status, 
            'datatype' : split_by_localname(item) })
        itemlist.append({
            'url'   : url, 
            'label' : '%s' % item.get('g'), 
            'count' : count_by_group(count_results, 
                lambda x:x.get('g')).get(item.get('g')),
        })
    return render_to_response('lists.html',
        RequestContext(request, {
            'title' : status.upper(),
            'viewname' : 'List',
            'status' : 'status: %s' % status.upper(),
            'itemlist' : sorted(itemlist, key=lambda x:x['label']),
            'read_only' : READ_ONLY,
            'count' : 'Records: %s' % status_resultsd.get(status),
            }) )

def listtype(request, status, datatype):
    graph = 'http://%s/%s' % (status.lower(), datatype)
    qstr = '''
        SELECT DISTINCT ?subject
        WHERE {
            GRAPH <%s> {
                ?subject ?p ?o .
            }
            FILTER( ?p != mos:header )
        }
        ORDER BY ?subject
    ''' % graph
    results = query.run_query(qstr)
    type_resultsd = count_by_group(get_counts_by_graph(datatype), split_by_type)
    itemlist = []
    for item in [x.get('subject') for x in results]:
        itemlist.append({
            'url'   : url_with_querystring(
                        reverse('edit', kwargs={'status' : status, 'datatype' : datatype}),
                        ref=item),
            'label' : item,
        })
    return render_to_response('main.html',
        RequestContext(request, {
            'title' : 'Listing %s' % status.upper(),
            'viewname' : 'Listing',
            'status' : 'Status: %s' % status.upper(),
            'detail' : 'Datatype: %s' % datatype,
            'itemlist' : itemlist,
            'read_only' : READ_ONLY,
            'count' : 'Records: %s' % type_resultsd.get(split_by_datatype(datatype)),
            'newshard' : reverse('newshard', kwargs={'status' : status, 'datatype' : datatype}),
            }) )

def search(request):
    pass

