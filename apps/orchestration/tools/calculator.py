"""
apps/orchestration/tools/calculator.py
Safe mathematical expression evaluator using ast.parse (NOT eval).
"""
import ast
import operator
from apps.orchestration.tools.base import BaseTool, ToolResult
from apps.orchestration.tools.registry import register

ALLOWED_OPS = {
    ast.Add:  operator.add,
    ast.Sub:  operator.sub,
    ast.Mult: operator.mul,
    ast.Div:  operator.truediv,
    ast.Pow:  operator.pow,
    ast.USub: operator.neg,
}


class CalculatorTool(BaseTool):
    name = "calculate"
    description = (
        "Evaluate a safe mathematical expression. "
        "Supports +, -, *, /, ** (power). "
        "Use this when the user asks for a calculation."
    )
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate, e.g. '(3 + 4) * 2'",
            }
        },
        "required": ["expression"],
    }

    def execute(self, expression: str, **kwargs) -> ToolResult:
        try:
            tree = ast.parse(expression, mode="eval")
            result = self._eval_node(tree.body)
            return ToolResult(success=True, data={"result": result, "expression": expression})
        except Exception as e:
            return ToolResult(success=False, error=f"Cannot evaluate '{expression}': {e}")

    def _eval_node(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            op = ALLOWED_OPS.get(type(node.op))
            if not op:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op(self._eval_node(node.left), self._eval_node(node.right))
        elif isinstance(node, ast.UnaryOp):
            op = ALLOWED_OPS.get(type(node.op))
            if not op:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            return op(self._eval_node(node.operand))
        raise ValueError(f"Unsupported expression node: {type(node).__name__}")


# Auto-register on import
register(CalculatorTool())
