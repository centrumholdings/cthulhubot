from django.template import Library, Node, TemplateSyntaxError, Variable

register = Library()

@register.tag
def mongoid(parser, token):
    """
    Print mongo's _id attribute or store it in variable.

    Usage:
        {% mongoid <variable> %}
        {% mongoid <variable> as <variable_id> %}

    Example:
        {% mongoid db.builder %}
        {% mongoid db.builder as builder_id %}
    """

    input = token.split_contents()

    if len(input) not in (2, 4):
        raise TemplateSyntaxError("One or three arguments expected")

    var_name = input[1]
    storage_var_name = None

    if len(input) > 2:
        if not input[2] == "as":
            raise TemplateSyntaxError("Second argument must be 'as' keyword")

        storage_var_name = input[3]

    return MongoIdentifierNode(var_name=var_name, storage_var_name=storage_var_name)

class MongoIdentifierNode(Node):
    def __init__(self, var_name, storage_var_name=None):
        self.var_name = var_name
        self.storage_var_name = storage_var_name

    def render(self, context):
        var = Variable(self.var_name).resolve(context)

        if not var or not '_id' in var:
            id = ''
        else:
            id = var['_id']

        if self.storage_var_name:
            context[self.storage_var_name] = id
            return ''
        else:
            return id


