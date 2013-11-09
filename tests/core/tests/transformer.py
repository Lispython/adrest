""" Tests ADRest emitter mixin.
"""
from django.views.generic import View

from ..api import api as API
from adrest.mixin import EmitterMixin, TransformerMixin
from adrest.tests import AdrestTestCase
from mixer.backend.django import mixer
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict # nolint

from datetime import datetime
from decimal import Decimal

class CoreTransformerTest(AdrestTestCase):

    """ Transformer related tests. """

    api = API

    def test_meta(self):
        """ Test a meta attribute generation. """

        class Resource(View, TransformerMixin):

            class Meta:
                model = 'core.pirate'

        self.assertTrue(Resource._meta)
        self.assertTrue(Resource._meta.transformers)

    def test_base_transformer(self):
        """Test base data transformation
        """
        from adrest.utils.transformers import BaseTransformer
        class Resource(View, TransformerMixin):

            class Meta:
                model = 'core.pirate'

        resource = Resource()
        data = {"Hello": "world"}
        transformer = BaseTransformer(resource, data)

        self.assertRaises(NotImplementedError, transformer.transform)
        self.assertEqual(transformer.resource, resource)
        self.assertEqual(transformer.value, data)

    def test_smart_transformer(self):

        from adrest.utils.transformers import SmartTransformer
        class Resource(View, TransformerMixin):

            class Meta:
                model = 'core.pirate'

        resource = Resource()

        data = dict(
            string_='test',
            unicode_=unicode('test'),
            datetime_=datetime(2007, 01, 01),
            odict_=OrderedDict(value=1),
            dict_=dict(
                list_=[1, 2.35, Decimal(3), False]
            )
        )
        transformer = SmartTransformer(resource, data)

        result = transformer.transform()
        self.assertEqual(result, data)

        self.assertRaises(NotImplementedError, transformer.transform)
        self.assertEqual(transformer.resource, resource)
        self.assertEqual(transformer.value, data)

    def test_django_transformer(self):
        from adrest.utils.transformers import DjangoSmartTransformer
        class Resource(View, TransformerMixin):

            class Meta:
                model = 'core.pirate'
                emit_include = 'pk'
                emit_exclude = 'fake',
                emit_related = dict(
                    pirate=dict(fields='character')
                    )

        resource = Resource()

        pirate = mixer.blend('core.pirate', name='Billy')

        data = [
            mixer.blend('core.boat', pirate=pirate),
            mixer.blend('core.boat', pirate=pirate),
            28, 'string']

        transformer = DjangoSmartTransformer(resource, data)
        self.assertEqual(transformer.options['exclude'], set(['fake']))
        result = transformer.transform()

        self.assertEqual(result[0]['pk'], data[0].pk)
        self.assertEqual(result[0]['fields']['pirate']['fields']['character'], data[0].pirate.character)

        # Test, m2o
        class Resource(View, TransformerMixin):

            class Meta:
                model = 'core.pirate'
                emit_include = 'boat_set'
                emit_related = dict(
                    pirate=dict(boat_set={
                        'fields': []
                        })
                    )

        resource = Resource()

        transformer = DjangoSmartTransformer(resource, data)
        self.assertEqual(transformer.options['include'], set(['boat_set']))
        result = transformer.transform()

        self.assertEquals(len(result['fields']['boat_set']), 2)
        for boat in result['fields']['boat_set']:
            self.assertEquals(boat['fields']['pirate'], pirate.pk)
            self.assertTrue('title' in boat['fields'].keys())

        result = transformer.to_simple(pirate)
        self.assertTrue('model' in result)

        result = transformer.to_simple(pirate, include=['boat_set'])
        self.assertTrue(result['fields']['boat_set'])
        self.assertEqual(len(list(result['fields']['boat_set'])), 2)


    def test_to_simple(self):
        """ Test resource's to simple method.

        :return :

        """

        pirates = mixer.cycle(2).blend('core.pirate')

        class Resource(View, TransformerMixin):

            class Meta:
                model = 'core.pirate'

            def to_simple(self, content, simple, transformer=None):

                return simple + ['HeyHey!']

        resource = Resource()
        response = resource.emit(pirates)
        self.assertTrue('HeyHey!' in response.content)

        class Resource(View, EmitterMixin):

            class Meta:
                model = 'core.pirate'

            @staticmethod
            def to_simple__name(pirate, transformer=None):

                return 'Evil ' + pirate.name

        resource = Resource()
        pirate = pirates[0]
        response = resource.emit(pirate)
        self.assertTrue('Evil ' + pirate.name in response.content)

# lint_ignore=W0212,E0102,C0110
