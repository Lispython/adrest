""" Collect URLS from apps. """

try:
    from django.conf.urls import patterns, include
except ImportError:
    from django.conf.urls.defaults import patterns, include


from ..main.api import API as main
from ..main.resources import DummyResource
from ..rpc.api import API as rpc
from .api import api as pirates, api2 as pirates2


urlpatterns = main.urls + patterns(
    '',
    DummyResource.as_url(),
    (r'^rpc/', include(rpc.urls)),

    (r'^pirates/', include(pirates.urls)),
    (r'^pirates2/', include(pirates2.urls)),

)
