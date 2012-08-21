
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

def contact(request, contact_id):
    pass


def contacts(request):
    pass


def provenance(request, provenance_id):
    pass


def provenances(request):
    # report in column view
    pass

def new(request, status):
    if request.method == 'POST':
        form = forms.ShardForm(request.POST)
        if form.is_valid():
            pass
    else:
        form = forms.ShardForm()
    return render_to_response('main.html',
        RequestContext(request, {
            'title' : 'New shard',
            'form' : form,
            }) )

def edit(request, status):
    shard = request.GET.get('ref', '')
    source = request.GET.get('source', '')
    shard = urllib.unquote(shard).decode('utf8')
    source = urllib.unquote(source).decode('utf8')
    ushardm = get_shard(shard, status, source)
    if request.method == 'POST':
        form = forms.ShardForm(request.POST, current_status=status)
        if form.is_valid():
            pass
        else:
            pass 
    else:
        form = forms.ShardForm(current_status=status)
    return render_to_response('main.html',
        RequestContext(request, {
            'viewname' : 'Edit Shard',
            'status' : 'Status: %s' % status,
            'title' : 'Edit Shard: %s' % shard,
            'detail' : 'Shard: %s' % shard,
            'newshard' : reverse('new', kwargs={'status' : status})
            'form' : form,
            'read_only' : READ_ONLY,
            'prefix_lookup' : mark_safe(
                ','.join(["'%s'" % x for x in prefixes.Prefixes().irilist])),
            }) )

def get_shard(shard, status, source):
    print '2>>>>', shard, status
    qstr = '''
        SELECT ?cfname ?unit ?canon_unit ?longname
        WHERE {
            <%s> cf:units ?unit .
            <%s> cf:name ?cfname .
            ?cfname cf:description ?long_name .
            ?cfname cf:canonical_units ?canon_unit .
            # need a term in here to match stash2cf valid_to versions ???
            # when comparing it to the source graph version
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
    for item in sorted(state.STATES, key=lambda x: x[0]):
        name = item[1].lower()
        itemlist.append( {
            'url' : reverse('list', kwargs={'status' : name}),
            'label' : item[1], 
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
    count_results = get_counts_by_graph()
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
                        reverse('edit', kwargs={'status' : status}),
                        ref=item,
                        source=graph),
            'label' : item,
        })
    return render_to_response('main.html',
        RequestContext(request, {
            'title' : 'Listing %s' % status,
            'viewname' : 'Listing',
            'status' : 'Status: %s' % status.upper(),
            'detail' : 'Datatype: %s' % datatype,
            'itemlist' : itemlist,
            'read_only' : READ_ONLY,
            'count' : 'Records: %s' % type_resultsd.get(split_by_datatype(datatype))
            }) )
    pass

def search(request):
    pass

