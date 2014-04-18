from django.http import HttpResponse

from .status import HTTP_200_OK


class DirtyHttpResponse(object):

    def __init__(self, data, status_code=None, content_type=None):
        self.data = data
        self.status_code = status_code
        self.content_type = content_type

    def __repr__(self):
        return "<DirtyHttpResponse %s>" % self.status_code

    @property
    def content(self):
        return self.data

    def to_simple(self, transformer, **options):
        """
        :param transformer: data transformator
        :return: response unserialized content
        """
        return self.content

    @property
    def error(self):
        return self.status_code != HTTP_200_OK



class SerializedMeta(type):

    def __call__(cls, content, *args, **kwargs):
        """ Don't create clones.
        """
        if isinstance(content, HttpResponse):
            return content

        return super(SerializedMeta, cls).__call__(
            content, *args, **kwargs
        )


class SerializedHttpResponse(HttpResponse): # nolint
    """ Response has will be serialized.
        Django http response will be returned as is.

        :param error: Force error in response.
    """
    __metaclass__ = SerializedMeta

    def __init__(self, content='', mimetype=None, status=None,
                 content_type=None, error=False):
        """
            Save original response.
        """
        self._error = error
        self._content_type = content_type

        super(SerializedHttpResponse, self).__init__(
            content,
            mimetype=mimetype,
            status=status,
            content_type=content_type)

    @property
    def error(self):
        return self._error or self.status_code != HTTP_200_OK

    def __repr__(self):
        return "<SerializedHttpResponse %s>" % self.status_code

# pymode:lint_ignore=E1103
