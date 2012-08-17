# Python module to hold the master references for Metadata Translation prefixes

import StringIO


class Prefixes(object):

    prefixd = {
        'iso19135' : 'http://reference.metoffice.gov.uk/data/wmo/def/iso19135/',
        'metExtra' : 'http://reference.metoffice.gov.uk/data/wmo/def/met/',
        'rdfs'     : 'http://www.w3.org/2000/01/rdf-schema#',
        'rdf'      : 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'skos'     : 'http://www.w3.org/2004/02/skos/core#',
        'mos'      : 'http://reference.metoffice.gov.uk/data/stash/',
        'mof'      : 'http://reference.metoffice.gov.uk/data/fieldcode/',
        'mon'      : 'http://reference.metoffice.gov.uk/data/none/',
        'fcode'    : 'http://www-hc/~umdoc/pp_package_ibm_docs/fcodes/',
        'cf'       : 'http://cf-pcmdi.llnl.gov/documents/',
    }

    @property
    def sparql(self):
        ios = StringIO.StringIO()
        for key, value in sorted(self.prefixd.items()):
            ios.write('PREFIX %s: <%s>\n' % (key, value))
        ios.write('\n')
        return ios.getvalue()

    @property
    def turtle(self):
        ios = StringIO.StringIO()
        for key, value in sorted(self.prefixd.items()):
            ios.write('@prefix %s: <%s> .\n' % (key, value))
        ios.write('\n')
        return ios.getvalue()

    @property
    def rdf(self):
        ios = StringIO.StringIO()
        for key, value in sorted(self.prefixd.items()):
            ios.write('xmlns:%s="%s"\n' % (key, value))
        ios.write('\n')
        return ios.getvalue()

    @property
    def irilist(self):
        return sorted(self.prefixd.values())


