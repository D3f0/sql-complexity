from .complexity import SQLComplexityAssessment, ComplexityRules

# Usage examples
if __name__ == "__main__":
    # Example 1: Simple query
    simple_sql = "SELECT id, name FROM users WHERE active = true"
    assessor = SQLComplexityAssessment()
    score = assessor.assess(simple_sql)
    print("Simple Query:")
    print(score)
    print()

    # Example 2: Complex query
    complex_sql = """
    WITH user_stats AS (
        SELECT user_id, COUNT(*) as order_count
        FROM orders
        GROUP BY user_id
    )
    SELECT 
        u.id,
        u.name,
        CASE 
            WHEN us.order_count > 10 THEN 'VIP'
            WHEN us.order_count > 5 THEN 'PREMIUM'
            ELSE 'REGULAR'
        END as status,
        COUNT(o.id) as total_orders
    FROM users u
    LEFT JOIN user_stats us ON u.id = us.user_id
    INNER JOIN orders o ON u.id = o.user_id
    WHERE u.created_at > '2023-01-01'
        AND o.status IN ('completed', 'pending')
    GROUP BY u.id, u.name, us.order_count
    HAVING COUNT(o.id) > 0
    UNION
    SELECT id, name, 'INACTIVE', 0
    FROM users
    WHERE active = false
    """

    score = assessor.assess(complex_sql)
    print("Complex Query (Default Rules):")
    print(score)
    print()

    # Example 3: Using strict rules
    strict_assessor = SQLComplexityAssessment(ComplexityRules.strict())
    score = strict_assessor.assess(complex_sql)
    print("Complex Query (Strict Rules):")
    print(score)
    print()

    # Example 4: Using lenient rules
    lenient_assessor = SQLComplexityAssessment(ComplexityRules.lenient())
    score = lenient_assessor.assess(complex_sql)
    print("Complex Query (Lenient Rules):")
    print(score)
    print()

    # Example 5: Custom rules
    custom_rules = ComplexityRules(per_outer_join=3, per_function=2, per_case=5)
    custom_assessor = SQLComplexityAssessment(custom_rules)
    score = custom_assessor.assess(complex_sql)
    print("Complex Query (Custom Rules):")
    print(score)
