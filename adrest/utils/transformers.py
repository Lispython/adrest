""" ADRest transformers. """
import collections
import inspect
from numbers import Number
from datetime import datetime, date, time
from decimal import Decimal

from functools import partial
from django.http import HttpResponse
from django.db.models import Model, Manager
from django.utils.encoding import smart_unicode

from .tools import as_tuple


class BaseTransformer(object):
    """ Abstract class for response transformation
    """
    format_type = None

    def __init__(self, resource, data, request=None):
        self._resource = resource
        self._data = data
        self._request = request

    @property
    def resource(self):
        return self._resource

    def transform(self):
        """ Start transformation
        """
        return self.value

    @property
    def value(self):
        return self._data


class SmartTransformer(BaseTransformer):
    """ Transformer class for simple transformation by meta rules


       Dictionary with transformation's options for relations

       * emit_fields -- Set serialized fields by manual
       * emit_exclude -- Exclude some fields
       * emit_include -- Include some fields
       * emit_related -- Options for relations.
       * emit_simple -- Simple options for simplificator

       Example:

          class SomeResource(TransformerMixin, View):
               class Meta:
                   model = Role
                   emit_fields = 'pk', 'user', 'custom_field'
                   emit_include = 'group_count'
                   emit_exclude = 'password', 'service'
                   emit_related = dict(
                       user = dict(
                               fields = 'username'
                       )
                   )
                   simplificators = [(HttpError, 'simplify_error'),]


    """
    format_type = 'default'

    def __init__(self, resource, data, request=None):
        if isinstance(data, HttpResponse):
            data = data.content
        super(SmartTransformer, self).__init__(resource, data, request)
        self.options = self.init_options(fields=self.meta_option('emit_fields'),
                                         include=self.meta_option('emit_include'),
                                         exclude=self.meta_option('emit_exclude'),
                                         related=self.meta_option('emit_related'))
        self.custom_simplificators = self.meta_option('simplificators') or ()

        self.default_simplificators = ((basestring, self.to_simple_basestring),
                                       (Number, self.to_simple_number),
                                       ((datetime, date, time), self.to_simple_dates),
                                       (collections.MutableMapping, self.to_simple_mutable_maping),
                                       (collections.Iterable, self.to_simple_iterable),
                                       (lambda v: v is None or v is True or v is False, self.to_simple_boolean),
                                       (lambda v: hasattr(v, 'to_simple') and not inspect.isclass(v),
                                        lambda v, **options: self.to_simple(v.to_simple(self, **options), **options)),
                                        (Model, self.to_simple_model))

        self.simplification_rules = self.prepare_rules(self.default_simplificators, self.custom_simplificators)


    def meta_option(self, name):
        """Get option from meta
        """
        return getattr(self.resource._meta, name, None)

    @staticmethod
    def init_options(fields=None, include=None, exclude=None, related=None):
        options = dict(
            fields=set(as_tuple(fields)),
            include=set(as_tuple(include)),
            exclude=set(as_tuple(exclude)),
            related=related or {},
        )
        return options

    def transform(self):
        to_simple = getattr(self.resource, 'to_simple', lambda content, data, transformer: data)
        return to_simple(self.value, self.to_simple(self.value, **self.options), self)

    def to_simple_basestring(self, value, **options):
        """(string, unicode)"""
        return smart_unicode(value)

    def to_simple_number(self, value, **options):
        """(int, long, float, real, complex, decimal)"""
        return float(str(value)) if isinstance(value, Decimal) else value

    def to_simple_dates(self, value, **options):
        """(datetime, data, time)"""
        return self.to_simple_datetime(value)

    def to_simple_mutable_maping(self, value, **options):
        """(dict, ordereddict, mutable mapping)"""
        return dict((k, self.to_simple(v, **options)) for k, v in value.items())

    def to_simple_iterable(self, value, **options):
        """(tuple, list, set, iterators)"""
        return [self.to_simple(o, **options) for o in value]

    def to_simple_boolean(self, value, **options):
        """(None, True, False)"""
        return value

    def prepare_rules(self, default_simplificators, custom_simplificators):
        """Merge simplificators

        """
        rules = []
        for check_rule, simplificator in tuple(custom_simplificators) + default_simplificators:

            if isinstance(check_rule, type(lambda: None)) and check_rule.__name__ == '<lambda>':
                rules.append((check_rule, simplificator))

            else:

                def make_rule(check_rule):
                    def func(value):
                        return isinstance(value, check_rule)
                    return func

                rules.append((make_rule(check_rule), simplificator))

        return rules



    def to_simple(self, value, **options):  # nolint
        " Simplify object. "

        for rule, action in self.simplification_rules:
            if rule(value):
                return action(value, **options)
        return str(value)

    def to_simple_datetime(self, value, **options):
        result = value.isoformat()
        if isinstance(value, datetime):
            if value.microsecond:
                result = result[:23] + result[26:]
            if result.endswith('+00:00'):
                result = result[:-6] + 'Z'
        elif isinstance(value, time) and value.microsecond:
            result = result[:12]
        return result

    def to_simple_model(self, instance, **options): # nolint
        """ Convert model to simple python structure.
        """
        options = self.init_options(**options)
        fields, include, exclude, related = options['fields'], options['include'], options['exclude'], options['related'] # nolint

        result = {}

        m2m_fields = [f.name for f in instance._meta.many_to_many]
        o2m_fields = [f.get_accessor_name()
                      for f in instance._meta.get_all_related_objects()]
        default_fields = set([field.name for field in instance._meta.fields
                              if field.serialize])
        serialized_fields = fields or (default_fields | include) - exclude

        for fname in serialized_fields:

            # Respect `to_simple__<fname>`
            to_simple = getattr(
                self.resource, 'to_simple__{0}'.format(fname), None)

            if to_simple:
                result[fname] = to_simple(instance, transformer=self)
                continue

            related_options = related.get(fname, dict())

            if related_options:
                related_options = self.init_options(**related_options)

            if fname in default_fields and not related_options:
                field = instance._meta.get_field(fname)
                value = field.value_from_object(instance)

            else:
                value = getattr(instance, fname, None)
                if isinstance(value, Manager):
                    value = value.all()

            result[fname] = self.to_simple(
                value, **related_options)


        return result


class SmartDjangoTransformer(SmartTransformer):
    """ Smart transformer for django framework
    """

    def __init__(self, *args, **kwargs):
        super(SmartDjangoTransformer, self).__init__(*args, **kwargs)

    def to_simple_model(self, instance, **options): # nolint
        """ Make dict structure from ``django.db.models.Model`` intance

        :param instance: :class:``django.db.models.Model`` instance
        :param \*\*options: transformation options
        :return: dict
        """
        return {"fields": super(SmartDjangoTransformer, self).to_simple_model(instance, **options),
                "model": self.get_model_name(instance),
                "pk":  self.get_pk(instance)}

    def get_model_name(self, instance):
        """ Get model name to display

        :param model: :class:``django.db.models.Model`` instance
        :return: mode name as string
        """
        return smart_unicode(instance._meta)

    def get_pk(self, instance):
        """Get model pk

        :param model: :class:``django.db.models.Model`` instance
        :return: primary key
        """
        return smart_unicode(
            instance._get_pk_val(), strings_only=True)


# lint_ignore=W901,R0911,W0212,W0622
