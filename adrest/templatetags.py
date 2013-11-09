""" ADRest inclusion tags. """
from django.template import Library, VariableDoesNotExist
from django.template.base import TagHelperNode, parse_bits
from django.template.loader import get_template
from django.utils import simplejson


register = Library()

# Fix django templatetags module loader
__path__ = ""


class AdrestInclusionNode(TagHelperNode):

    """ Service class for tags. """

    def render(self, context):
        """ Render node.

        :return str: Rendered string.

        """
        try:
            args, ctx = self.get_resolved_arguments(context)
            target = args[0]
            if not target:
                return ''
            ctx['content'] = target
        except VariableDoesNotExist:
            return ''

        emitter = context.get('emitter')
        t_name = emitter.get_template_path(target)
        t = get_template(t_name)
        context.dicts.append(ctx)
        response = t.nodelist.render(context)
        context.pop()
        return response


def adrest_include(parser, token):
    """ Include adrest_template for any objects.

    :return str: Rendered string.

    """
    bits = token.split_contents()[1:]
    args, kwargs = parse_bits(
        parser, bits, ['content'], 'args', 'kwargs', tuple(),
        False, 'adrest_include')
    return AdrestInclusionNode(False, args, kwargs)
adrest_include = register.tag(adrest_include)


def adrest_jsonify(content, resource, request):
    """ Serialize any object to JSON .

    :return str: Rendered string.

    """
    transformer = resource.determine_transformer(request)
    return simplejson.dumps(transformer(
        resource, data=content, request=request),
        **getattr(resource._meta, 'emit_options', {}))

adrest_jsonify = register.simple_tag(adrest_jsonify)
