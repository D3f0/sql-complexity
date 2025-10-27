from dataclasses import dataclass
from typing import Optional

from sqlglot import exp, parse_one
from sqlglot.expressions import Expression


@dataclass
class ComplexityRules:
    """Configurable complexity scoring rules"""

    base_per_table: int = 1
    per_join: int = 1
    per_outer_join: int = 1
    per_where_predicate: int = 1
    per_having_predicate: int = 1
    per_cte: int = 1
    per_group_by_expr: int = 1
    per_union: int = 1
    per_intersect: int = 1
    per_function: int = 1
    per_case: int = 1

    @classmethod
    def default(cls) -> "ComplexityRules":
        """Default rules"""
        return cls()

    @classmethod
    def strict(cls) -> "ComplexityRules":
        """Stricter scoring"""
        return cls(per_outer_join=2, per_function=2, per_case=2)

    @classmethod
    def lenient(cls) -> "ComplexityRules":
        """More lenient scoring"""
        return cls(per_join=0, per_function=0)


@dataclass
class ComplexityScore:
    """Breakdown of complexity score"""

    total: int = 0
    tables: int = 0
    joins: int = 0
    outer_joins: int = 0
    where_predicates: int = 0
    having_predicates: int = 0
    ctes: int = 0
    group_by_expressions: int = 0
    unions: int = 0
    intersects: int = 0
    functions: int = 0
    cases: int = 0

    def __repr__(self) -> str:
        return (
            f"Complexity Score: {self.total}\n"
            f"  Tables: {self.tables}\n"
            f"  Joins: {self.joins}\n"
            f"  Outer Joins: {self.outer_joins}\n"
            f"  WHERE Predicates: {self.where_predicates}\n"
            f"  HAVING Predicates: {self.having_predicates}\n"
            f"  CTEs: {self.ctes}\n"
            f"  GROUP BY Expressions: {self.group_by_expressions}\n"
            f"  UNIONs: {self.unions}\n"
            f"  INTERSECTs: {self.intersects}\n"
            f"  Functions: {self.functions}\n"
            f"  CASE Expressions: {self.cases}"
        )


class SQLComplexityAssessment:
    """Assess SQL query complexity based on configurable rules"""

    def __init__(self, rules: Optional[ComplexityRules] = None):
        self.rules = rules or ComplexityRules.default()

    def assess(self, sql: str) -> ComplexityScore:
        """Assess complexity of SQL query"""
        try:
            parsed = parse_one(sql)
        except Exception as e:
            raise ValueError(f"Failed to parse SQL: {e}") from e

        score = ComplexityScore()
        self._assess_node(parsed, score)
        self._calculate_total(score)
        return score

    def _assess_node(self, node: Expression, score: ComplexityScore) -> None:
        """Recursively assess complexity of AST node"""

        # Count tables
        if isinstance(node, exp.Table):
            score.tables += 1

        # Count CTEs
        elif isinstance(node, exp.CTE):
            score.ctes += 1

        # Count joins
        elif isinstance(node, exp.Join):
            # Check if it's an outer join
            if (
                node.args.get("kind") == "OUTER"
                or node.args.get("kind") == "LEFT"
                or node.args.get("kind") == "RIGHT"
                or node.args.get("kind") == "FULL"
            ):
                score.outer_joins += 1
            else:
                score.joins += 1

        # Count WHERE predicates
        elif isinstance(node, exp.Where):
            score.where_predicates += self._count_predicates(node.this)

        # Count HAVING predicates
        elif isinstance(node, exp.Having):
            score.having_predicates += self._count_predicates(node.this)

        # Count GROUP BY expressions
        elif isinstance(node, exp.Group):
            score.group_by_expressions += len(node.expressions)

        # Count UNION/INTERSECT
        elif isinstance(node, exp.Union):
            score.unions += 1
        elif isinstance(node, exp.Intersect):
            score.intersects += 1

        # Count function calls
        elif isinstance(node, exp.Func):
            score.functions += 1

        # Count CASE expressions
        elif isinstance(node, exp.Case):
            score.cases += 1

        # Recursively process children
        for child in node.iter_expressions():
            self._assess_node(child, score)

    def _count_predicates(self, node: Expression) -> int:
        """Count AND/OR predicates"""
        if node is None:
            return 0

        if isinstance(node, (exp.And, exp.Or)):
            return (
                1
                + self._count_predicates(node.left)
                + self._count_predicates(node.right)
            )
        return 1

    def _calculate_total(self, score: ComplexityScore) -> None:
        """Calculate total score based on rules"""
        score.total = (
            score.tables * self.rules.base_per_table
            + score.joins * self.rules.per_join
            + score.outer_joins * self.rules.per_outer_join
            + score.where_predicates * self.rules.per_where_predicate
            + score.having_predicates * self.rules.per_having_predicate
            + score.ctes * self.rules.per_cte
            + score.group_by_expressions * self.rules.per_group_by_expr
            + score.unions * self.rules.per_union
            + score.intersects * self.rules.per_intersect
            + score.functions * self.rules.per_function
            + score.cases * self.rules.per_case
        )
