""" Tests ADRest emitter mixin.
"""
from django.views.generic import View

from ..api import api as API
from adrest.mixin import EmitterMixin, TransformerMixin
from adrest.utils.transformers import SmartTransformer
from adrest.tests import AdrestTestCase
from mixer.backend.django import mixer


class CoreEmitterTest(AdrestTestCase):

    """ Emitter related tests. """

    api = API

    def test_meta(self):
        """ Test a meta attribute generation. """

        class Resource(EmitterMixin, View):

            class Meta:
                model = 'core.pirate'


        self.assertTrue(Resource._meta)
        self.assertTrue(Resource._meta.emitters)

    def test_to_simple(self):
        """ Test resource's to simple method.

        :return :

        """

        pirates = mixer.cycle(2).blend('core.pirate')

        class Resource(View, EmitterMixin):

            class Meta:
                model = 'core.pirate'

            def to_simple(self, content, simple, serializer=None):

                return simple + ['HeyHey!']

            def transform(self, content, request=None):
                return SmartTransformer(self, content, request).transform()

        resource = Resource()


        response = resource.emit(resource.transform(pirates))
        self.assertTrue('HeyHey!' in response.content)

        class Resource(View, EmitterMixin):

            class Meta:
                model = 'core.pirate'

            @staticmethod
            def to_simple__name(pirate, transformer=None):

                return 'Evil ' + pirate.name

            def transform(self, content, request=None):
                return SmartTransformer(self, content, request).transform()

        resource = Resource()
        pirate = pirates[0]

        response = resource.emit(resource.transform(pirate))
        self.assertTrue('Evil ' + pirate.name in response.content)


# lint_ignore=W0212,E0102,C0110
