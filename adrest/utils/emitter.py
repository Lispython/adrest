""" ADRest emitters. """

from datetime import datetime
from os import path as op
from time import mktime

from django.db.models.base import ModelBase, Model
from django.template import RequestContext, loader
from django.utils import simplejson
from django.http import HttpResponse

from ..utils import UpdatedList
from .paginator import Paginator
from .response import SerializedHttpResponse, DirtyHttpResponse
from .status import HTTP_200_OK


class EmitterMeta(type):

    """ Preload format attribute. """

    def __new__(mcs, name, bases, params):
        cls = super(EmitterMeta, mcs).__new__(mcs, name, bases, params)
        if not cls.format and cls.media_type:
            cls.format = str(cls.media_type).split('/')[-1]
        return cls


class BaseEmitter(object):

    """ Base class for emitters.

    All emitters must extend this class, set the media_type attribute, and
    override the serialize() function.

    """

    __metaclass__ = EmitterMeta

    media_type = None
    format = None

    def __init__(self, resource, request=None, response=None):
        self.resource = resource
        self.request = request

        # Response without serialized content
        self.dirty_response = response


    def emit(self):
        """ Serialize response.

        :return response: Instance of django.http.Response

        """
        # Response already serialized
        if isinstance(self.dirty_response, SerializedHttpResponse):
            return self.dirty_response

        if isinstance(self.dirty_response, HttpResponse):
            return self.dirty_response

        elif isinstance(self.dirty_response, DirtyHttpResponse):
            status_code = self.dirty_response.status_code
            serialized_content = self.serialize(self.dirty_response.content)
        else:
            status_code = HTTP_200_OK
            serialized_content = self.serialize(self.dirty_response)


        response = HttpResponse(serialized_content,
                                content_type=self.media_type,
                                status=status_code)
        return response


    def serialize(self, content):
        """ Low level serialization.

        :return response:

        """
        return content


class NullEmitter(BaseEmitter):

    """ Return data as is. """

    media_type = 'unknown/unknown'

    def emit(self):
        """ Do nothing.

        :return response:

        """
        return self.dirty_response


class TextEmitter(BaseEmitter):

    """ Serialize to unicode. """

    media_type = 'text/plain'

    @staticmethod
    def serialize(content):
        """ Get content and return string.

        :return unicode:

        """
        return unicode(content)


class JSONEmitter(BaseEmitter):

    """ Serialize to JSON. """

    media_type = 'application/json'

    def serialize(self, content):
        """ Serialize to JSON.

        :return string: serializaed JSON

        """
        return simplejson.dumps(content, **(getattr(self.resource._meta, 'emit_options', {}) or {}))


class JSONPEmitter(JSONEmitter):

    """ Serialize to JSONP. """

    media_type = 'text/javascript'

    def serialize(self, content):
        """ Serialize to JSONP.

        :return string: serializaed JSONP

        """
        content = super(JSONPEmitter, self).serialize(content)
        callback = self.request.GET.get('callback', 'callback')
        return u'%s(%s)' % (callback, content)


class XMLEmitter(BaseEmitter):

    """ Serialize to XML. """

    media_type = 'application/xml'
    xmldoc_tpl = '<?xml version="1.0" encoding="utf-8"?>\n<response success="%s" version="%s" timestamp="%s">%s</response>' # nolint

    def serialize(self, content):
        """ Serialize to XML.

        :return string: serialized XML

        """
        is_error = False

        if isinstance(self.dirty_response, (HttpResponse, DirtyHttpResponse)):
            is_error = self.dirty_response.status_code != HTTP_200_OK

        return self.xmldoc_tpl % (
            'true' if not is_error else 'false',
            str(self.resource.api or ''),
            int(mktime(datetime.now().timetuple())),
            self.dump_content(content)
        )

    def dump_content(self, content):
        """Convert dict to xml

        :param content: dict
        """
        return ''.join(s for s in self._dumps(content))

    def _dumps(self, value):  # nolint
        tag = it = None

        if isinstance(value, list):
            tag = 'items'
            it = iter(value)

        elif isinstance(value, dict) and 'model' in value:
            tag = value.get('model').split('.')[1]
            it = value.iteritems()

        elif isinstance(value, dict):
            it = value.iteritems()

        elif isinstance(value, tuple):
            tag = str(value[0])
            it = (i for i in value[1:])

        else:
            yield str(value)

        if tag:
            yield "<%s>" % tag

        if it:
            try:
                while True:
                    v = next(it)
                    yield ''.join(self._dumps(v))
            except StopIteration:
                yield ''

        if tag:
            yield "</%s>" % tag


class TemplateEmitter(BaseEmitter):

    """ Serialize by django templates. """

    def serialize(self, content):
        """ Render Django template.

        :return string: rendered content

        """

        if (isinstance(self.dirty_response, (HttpResponse, DirtyHttpResponse)) and
            self.dirty_response.status_code != HTTP_200_OK):

            template_name = op.join('api', 'error.%s' % self.format)
        else:
            template_name = (self.resource._meta.emit_template
                             or self.get_template_path(content))

        template = loader.get_template(template_name)

        return template.render(RequestContext(self.request, dict(
            content=content,
            emitter=self,
            resource=self.resource)))

    def get_template_path(self, content=None):
        """ Find template.

        :return string: remplate path

        """
        if (isinstance(content, dict) and 'resources' in content and \
            'num_pages' in content) or isinstance(content, Paginator):
            return op.join('api', 'paginator.%s' % self.format)

        if isinstance(content, UpdatedList):
            return op.join('api', 'updated.%s' % self.format)

        app = ''
        name = self.resource._meta.name

        if not content:
            content = self.resource._meta.model

        if isinstance(content, (Model, ModelBase)):
            app = content._meta.app_label # nolint
            name = content._meta.module_name # nolint

        basedir = 'api'
        if getattr(self.resource, 'api', None):
            basedir = self.resource.api.prefix

        return op.join(
            basedir,
            str(self.resource.api or ''), app, "%s.%s" % (name, self.format)
        )


class JSONTemplateEmitter(TemplateEmitter):

    """ Template emitter with JSON media type. """

    media_type = 'application/json'


class JSONPTemplateEmitter(TemplateEmitter):

    """ Template emitter with javascript media type. """

    media_type = 'text/javascript'
    format = 'json'

    def serialize(self, content):
        """ Move rendered content to callback.

        :return string: JSONP

        """
        content = super(JSONPTemplateEmitter, self).serialize(content)
        callback = self.request.GET.get('callback', 'callback')
        return '%s(%s)' % (callback, content)


class HTMLTemplateEmitter(TemplateEmitter):

    """ Template emitter with HTML media type. """

    media_type = 'text/html'


class XMLTemplateEmitter(TemplateEmitter):

    """ Template emitter with XML media type. """

    media_type = 'application/xml'
    xmldoc_tpl = '<?xml version="1.0" encoding="utf-8"?>\n<response success="%s" version="%s" timestamp="%s">%s</response>' # nolint

    def serialize(self, content):
        """ Serialize to xml.

        :return string:

        """
        is_error = False

        if isinstance(self.dirty_response, (DirtyHttpResponse, HttpResponse)):
            is_error = self.dirty_response.status_code != HTTP_200_OK

        return self.xmldoc_tpl % (
            'true' if not is_error else 'false',
            str(self.resource.api or ''),
            int(mktime(datetime.now().timetuple())),
            super(XMLTemplateEmitter, self).serialize(content)
        )


try:
    from bson import BSON

    class BSONEmitter(BaseEmitter):
        media_type = 'application/bson'

        @staticmethod
        def serialize(content):
            return BSON.encode(content)

except ImportError:
    pass

# pymode:lint_ignore=F0401,W0704
