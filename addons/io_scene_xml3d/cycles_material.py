from string import Template
from .jscodegen import generate
import json


class NotSupportedError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class NodeContext:
    def __init__(self):
        self.body = []
        self.funcs = []
        self.name_hint = []
        self.bound_variables = set()
        self.env = {}

    def create_variable(self, postfix):
        prefix = "" if not len(self.name_hint) else self.name_hint[-1] + "_"
        variable_name = prefix + postfix
        i = 0
        while variable_name in self.bound_variables:
            variable_name = prefix + postfix + str(i)
            i += 1
        self.bound_variables.add(variable_name)
        return variable_name


class CyclesMaterial:
    def __init__(self, tree):
        self.tree = tree
        self.bound_sockets = {}

    def output_material(self, node, ctx):
        surface_calls = self.walk_socket(node.inputs["Surface"], ctx)
        if not isinstance(surface_calls, list):
            surface_calls = [surface_calls]

        last_member = NewExpression(Identifier("Shade"))
        for shader in surface_calls:
            assert isinstance(shader, CallExpression)
            member_expr = MemberExpression(last_member, shader['callee'])
            shader['callee'] = member_expr
            last_member = shader

        return ReturnStatement(last_member)

    def mix_shader(self, node, ctx):
        result = [self.walk_socket(socket, ctx) for socket in node.inputs]

        # (1 - α) * closure1
        args = result[1]['arguments']
        r1 = CallExpression(MemberExpression(args[0], Identifier("mul")), [BinaryExpression(Literal(1), '-', result[0])])
        args[0] = r1

        # α * closure2
        args = result[2]['arguments']
        r1 = CallExpression(MemberExpression(args[0], Identifier("mul")), [result[0]])
        args[0] = r1

        return [result[1], result[2]]

    def tex_image(self, node, ctx):
        # TODO: Write image into env object
        print(node.image)
        local_var = ctx.create_variable("texture")
        sample = MemberExpression(Identifier("env"), Identifier(local_var))
        sample = MemberExpression(sample, Identifier("sample2d"))
        # TODO: Walk along input "Vector" input
        sample = CallExpression(sample, [MemberExpression(Identifier("env"), Identifier("texcoord"))])
        sample = ExpressionStatement(AssignmentExpression(Identifier(local_var), sample))
        ctx.body.append(sample)
        return Identifier(local_var)

    def bsdf_diffuse(self, node, ctx):
        ctx.name_hint.append("diffuse")
        arguments = [
            self.walk_socket(node.inputs[0], ctx),
            self.walk_socket(node.inputs[2], ctx, MemberExpression(Identifier("env"), Identifier("normal"))),
            self.walk_socket(node.inputs[1], ctx),
        ]
        ctx.name_hint.pop()
        return CallExpression(Identifier("diffuse"), arguments)


    def bsdf_glossy(self, node, ctx):
        arguments = [
            self.walk_socket(node.inputs[0], ctx),
            self.walk_socket(node.inputs[2], ctx, MemberExpression(Identifier("env"), Identifier("normal"))),
            Literal(1.7),
            self.walk_socket(node.inputs[1], ctx),
        ]
        return CallExpression(Identifier("cookTorrance"), arguments)

    def to_shade_type(self, value, socket_type):
        if isinstance(value, float):
            return Literal(value)
        if socket_type == "RGBA":
            return self.create_shade_vec3(value)
        print(type(value), socket_type)
        return Identifier(value)

    def create_shade_vec3(self, vec3):
        print(vec3)
        return NewExpression(Identifier("Vec3"), [Literal(c) for c in vec3[:3]])


    def walk_socket(self, socket, ctx, default=None):
        if socket.is_linked:
            return self.walk(socket.links[0].from_node, ctx)
        elif default:
            return default
        else:
            return self.to_shade_type(socket.default_value, socket.type)

    def walk(self, node, ctx):
        node_type = node.bl_static_type
        try:
            attr = getattr(self, node_type.lower())
        except AttributeError:
            raise NotSupportedError("Cycles node not (yet) supported: '%s'" % node_type)
        return attr(node, ctx)

    def create(self):

        body = []
        shade_func = FunctionDeclaration("shade", [Identifier("env")], BlockStatement(body))

        program = Program([shade_func])
        processed_nodes = []

        def node_generator(node):
            if not processed_nodes.count(node):
                yield node
                processed_nodes.append(node)

            for socket in node.inputs:
                for node_link in socket.links:
                    yield from node_generator(node_link.from_node)

        start_node = next((node for node in self.tree.nodes if node.bl_static_type == "OUTPUT_MATERIAL"))

        try:
            ctx = NodeContext()
            result = self.walk(start_node, ctx)
            body.extend(ctx.body)
            body.append(result)
            # print(result)
            program = generate(program)
        except NotSupportedError as err:
            return None, str(err.value)


        # body.reverse()
        # program = generate(program)
        print(program)
        return program, None


class Node(dict):
    def __init__(self, *arg, **kw):
        super(Node, self).__init__(*arg, **kw)


class MemberExpression(Node):
    def __init__(self, object, property, computed=False):
        super(Node, self).__init__(type="MemberExpression", object=object, property=property, computed=computed)


class CallExpression(Node):
    def __init__(self, callee, arguments=[]):
        super(Node, self).__init__(type="CallExpression", callee=callee, arguments=arguments)


class BinaryExpression(Node):
    def __init__(self, left, operator, right):
        super(Node, self).__init__(type="BinaryExpression", left=left, operator=operator, right=right)


class AssignmentExpression(Node):
    def __init__(self, left, right, operator='='):
        super(Node, self).__init__(type="AssignmentExpression", left=left, operator=operator, right=right)


class Literal(Node):
    def __init__(self, value):
        super(Node, self).__init__(type="Literal", value=value)


class VariableDeclarator(Node):
    def __init__(self, id, init=None):
        super(Node, self).__init__(type="VariableDeclarator", id=id, init=init)


class VariableDeclaration(Node):
    def __init__(self, declarations, kind="var"):
        super(Node, self).__init__(type="VariableDeclaration",
                                   declarations=declarations if isinstance(declarations, list) else [declarations],
                                   kind=kind)


class Identifier(Node):
    def __init__(self, name):
        super(Node, self).__init__(type="Identifier", name=name)


class ReturnStatement(Node):
    def __init__(self, argument=None):
        super(Node, self).__init__(type="ReturnStatement", argument=argument)


class ExpressionStatement(Node):
    def __init__(self, expression):
        super(Node, self).__init__(type="ExpressionStatement", expression=expression)


class BlockStatement(Node):
    def __init__(self, body=[]):
        super(Node, self).__init__(type="BlockStatement", body=body)


class NewExpression(Node):
    def __init__(self, callee, arguments=[]):
        super(Node, self).__init__(type="NewExpression", callee=callee, arguments=arguments)


class Program(Node):
    def __init__(self, body=BlockStatement()):
        super(Node, self).__init__(type="Program", body=body)


class FunctionDeclaration(Node):
    def __init__(self, id, params=[], body=BlockStatement()):
        super(Node, self).__init__(type="FunctionDeclaration", id=Identifier(id), params=params, body=body)