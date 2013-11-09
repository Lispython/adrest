""" ADRest transformation support. """
import mimeparse
from django.http import HttpResponse

from ..utils.transformers import SmartTransformer, BaseTransformer
from ..utils.meta import MixinBaseMeta
from ..utils.paginator import Paginator
from ..utils.tools import as_tuple


__all__ = 'TransformerMixin',


class Meta:

    """ Transformer options. Setup parameters for resource's transformation.

    ::

        class SomeResource(TransformerMixin, View):

            class Meta:
                transformers = SmartTransformer

    """
    transformers = SmartTransformer



class TransformerMeta(MixinBaseMeta):

    """ Prepare resource's emiters. """

    def __new__(mcs, name, bases, params):
        cls = super(TransformerMeta, mcs).__new__(mcs, name, bases, params)

        cls._meta.transformers = as_tuple(cls._meta.transformers)
        cls._meta.transformers_dict = dict(
            (e.format_type, e) for e in cls._meta.transformers
        )

        if not cls._meta.transformers:
            raise AssertionError("Should be defined at least one transformer.")

        for e in cls._meta.transformers:
            if not issubclass(e, BaseTransformer):
                raise AssertionError(
                    "Transformer should be subclass of "
                    "`adrest.utils.transformers.BaseTransformer`"
                )

        return cls


class TransformerMixin(object):


    __metaclass__ = TransformerMeta

    # Set default options
    Meta = Meta

    def transform(self, content, request=None):
        """ Transform given content by using ``transformer``

        :return: transformed content
        """
        transformer = self.determine_transformer(request)
        return transformer(self, data=content, request=request).transform()


    def determine_transformer(self, request=None):
        """ Get tranformer for request

        :return: :class:``adrest.utils.transformers.BaseTransformer``
        """
        default_transformer = self._meta.transformers[0]
        if not request:
            return default_transformer

        return self._meta.transformers_dict(
            request.META.get('HTTP_X_TRANSFORMER', 'default'),
            default_transformer)


    @staticmethod
    def to_simple(content, simple, transformer=None):
        """ Abstract method for modification a structure before serialization.

        :param content: response from called method
        :param simple: structure is prepared to serialization
        :param transformer: current serializer

        :return object: structure for serialization

        ::

            class SomeResource(ResourceView):
                def get(self, request, **resources):
                    return dict(true=False)

                def to_simple(self, content, simple, serializer):
                    simple['true'] = True
                    return simple

        """
        return simple





