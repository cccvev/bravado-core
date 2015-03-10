import jsonref

from bravado.mapping.exception import SwaggerMappingError


JSONSCHEMA_PRIMITIVE_VALIDATIONS = {
    'string': ('minLength', 'maxLength', 'pattern', 'format', 'enum', 'default'),  # noqa
    'integer': ('multipleOf', 'minimum', 'maximum', 'exclusiveMaximum', 'exclusiveMinimum', 'enum', 'default', 'format'),  # noqa
    'number': ('multipleOf', 'minimum', 'maximum', 'exclusiveMaximum', 'exclusiveMinimum', 'enum', 'default', 'format'),   # noqa
    'boolean': ('enum', 'default'),
    'null': (),
}

SWAGGER_PRIMITIVES = (
    'integer',
    'number',
    'string',
    'boolean',
    'null',
)


def has_default(schema_object_spec):
    return 'default' in schema_object_spec


def get_default(schema_object_spec):
    return schema_object_spec.get('default', None)


def is_required(schema_object_spec):
    return 'required' in schema_object_spec


def has_format(schema_object_spec):
    return 'format' in schema_object_spec


def get_format(schema_object_spec):
    return schema_object_spec.get('format', None)


def to_primitive_schema(primitive_spec):
    """Given the swagger spec for a primitive type, create the equivalent
    jsonschema object for the primitive type.

    :type primitive_spec: dict
    :returns: jsonschema object
    :rtype; dict
    """
    # identify the validation keys in the swager spec that are supported by
    # jsonschema for the given primitive type
    primitive_type = primitive_spec['type']
    transferable_keys = ['name', 'type', 'description']
    transferable_keys += JSONSCHEMA_PRIMITIVE_VALIDATIONS[primitive_type]
    schema = {}
    for key, value in primitive_spec.iteritems():
        if key in transferable_keys:
            schema[key] = value
    return schema


def to_array_schema(array_spec):
    """Given the swagger spec for an array type, create the equivalent
    jsonschema object for the array type.

    See section 5.3 in http://json-schema.org/latest/json-schema-validation.html

    :type: array_spec: dict
    :returns: jsconschema object
    :rtype: dict
    """
    # JsonSchema arrays
    # =================
    # additionalItems => boolean or object schema
    # items => object - implies list of arbitrary length with items of the same
    #                   type. ignore additionalItems.
    #          array  - implies tuple with items of different type matching
    #                   schema at ordinal. observe additionalItems - means
    #                   extra items in the array allowed or not
    #
    # SwaggerSpec arrays
    # ==================
    #   Parameter arrays
    #     - doesn't support additionalItems
    #     - all arrays are are treated as lists, not tuples hence 'items' can
    #       not be '[subschema1, subschema2, ...]'
    #     - 'items' has to be one of "string", "number", "integer", "boolean",
    #       or "array"
    #     - depending on 'items' type, validations for that type are supported
    #       as keys. ex: item of string -> (minLength, maxLength, enum, etc)
    #                ex: item of array  -> (minItems, maxItems, etc)
    #     - have to implement support for 'default' keyword
    #     - have to implement support for 'collectionFormat'
    #     - have to implmenet support for 'required'
    transferable_keys = (
        'type',
        'items',
        'minItems',
        'maxItems',
        'uniqueItems',
        'name',
        'description'
    )
    schema = {}
    for key, value in array_spec.iteritems():
        if key in transferable_keys:
            schema[key] = value
            if key == 'items':
                items_spec = value
                items_type = items_spec['type']
                if items_type in SWAGGER_PRIMITIVES:
                    schema[key] = to_primitive_schema(items_spec)
                elif items_type == 'array':
                    # nested arrays
                    schema[key] = to_array_schema(items_spec)
                else:
                    raise SwaggerMappingError(
                        'Item type {0} not supported'.format(items_type))
    return schema


def is_dict_like(spec):
    """Since we're using jsonref, identifying dicts while inspecting a swagger
    spec is no longer limited to the dict type. This takes into account
    jsonref's proxy objects that dereference to a dict.

    :param spec: swagger object specification in dict form
    :rtype: boolean
    """
    if type(spec) == dict:
        return True
    if type(spec) == jsonref.JsonRef and type(spec.__subject__) == dict:
        return True
    return False


def is_list_like(spec):
    """Since we're using jsonref, identifying arrays while inspecting a swagger
    spec is no longer limited to the list type. This takes into account
    jsonref's proxy objects that dereference to a list.

    :param spec: swagger object specification in dict form
    :rtype: boolean
    """
    if type(spec) == list:
        return True
    if type(spec) == jsonref.JsonRef and type(spec.__subject__) == list:
        return True
    return False