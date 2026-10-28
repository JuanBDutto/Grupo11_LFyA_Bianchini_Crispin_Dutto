
import ast


class ASTNormalizer(ast.NodeTransformer):
    def __init__(self):
        self.variables = {}
        self.counter = 1

    def _var(self, name):
        if name not in self.variables:
            self.variables[name] = f"VAR{self.counter}"
            self.counter += 1
        return self.variables[name]

    def visit_FunctionDef(self, node):
        node.name = "FUNC"
        self.variables = {}
        self.counter = 1
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node):
        return self.visit_FunctionDef(node)

    def visit_arg(self, node):
        node.arg = self._var(node.arg)
        return node

    def visit_Name(self, node):
        node.id = self._var(node.id)
        return node

    def visit_Constant(self, node):
        if isinstance(node.value, (int, float, complex, str, bytes, bool)):
            node.value = "LIT"
        return node


def normalize(node):
    return ASTNormalizer().visit(node)