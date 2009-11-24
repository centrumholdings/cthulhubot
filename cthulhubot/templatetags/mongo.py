from django.template import Library, Node, TemplateSyntaxError, Variable

register = Library()

@register.tag
def mongoid(parser, token):
    """
    Print mongo's _id attribute. 

    Usage:
        {% mongoid <variable> %}

    Example:
        {% mongoid db.builder %}
    """

    input = token.split_contents()

    if len(input) != 2:
        raise TemplateSyntaxError("Exactly one argument expected")

    var_name = input[1]

    return MongoIdentifierNode(var_name)

class MongoIdentifierNode(Node):
    def __init__(self, var_name):
        self.var_name = var_name

    def render(self, context):
        var = Variable(self.var_name).resolve(context)
        if not '_id' in var:
            return ''
        return var['_id']

