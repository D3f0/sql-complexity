# SQL Complexity Estimator

This package provides a simple algorithm to calculate complexity of SQL expressions.

It's based on SQLGlot abstract syntax tree, so the provided SQL must be compatible 
with SQLGlot engines.


The rules are the following:

- +1 per join expression
- +1 per predicate after WHERE or HAVING
- +1 per CTE
- +1 per GROUP BY expression
- +1 per UNION or INTERSECT
- +1 per function call
- +1 per CASE expression

This package is inspired on the comments of this [stack overflow](https://stackoverflow.com/questions/3353634/measuring-the-complexity-of-sql-statements) thread.


## Install

```bash
python -m pip install sql-complexity
```

```bash
poetry add sql-complexity
```

```bash
uv add sql-complexity
```

### Run with uvx

```bash
uvx --refresh sql-complexity
```

## Run from the CLI

```bash
sql-complexity some.sql
```

```bash
cat myfile.sql | sql-complexity
```

## Using it in your code

```python
from sql_complexity import SQLComplexityAssessment

assessor = SQLComplexityAssessment()
score = assessor.assess(contents)
print(score)
print(score.total)
```
