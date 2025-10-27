from sql_complexity import SQLComplexityAssessment, ComplexityRules


def test_simple():
    simple_sql = "SELECT id, name FROM users WHERE active = true"
    assessor = SQLComplexityAssessment()
    score = assessor.assess(simple_sql)

    assert score.total == 2


def test_complex():
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

    assessor = SQLComplexityAssessment()
    score = assessor.assess(complex_sql)
    assert score.total == 25
