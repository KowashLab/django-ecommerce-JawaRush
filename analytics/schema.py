import graphene
from django.db.models import Avg, Count, Sum
from django.db.models.functions import TruncDate

from orders.models import Order
from products.models import Product


class TopProductType(graphene.ObjectType):
    id = graphene.ID(required=True)
    name = graphene.String(required=True)
    slug = graphene.String(required=True)
    orders_count = graphene.Int(required=True)


class RevenueByDayType(graphene.ObjectType):
    date = graphene.String(required=True)
    revenue = graphene.Float(required=True)


class Query(graphene.ObjectType):
    """Analytics queries: order counts, total revenue, order value metrics, top products, daily revenue."""
    total_orders = graphene.Int(description='Count of all orders')
    orders_count = graphene.Int(description='Total number of orders')
    total_revenue = graphene.Float(description='Sum of all order total_price values')
    average_order_value = graphene.Float(description='Average value of all orders')
    top_products = graphene.List(
        TopProductType,
        description='Top 5 products by number of distinct orders',
    )
    revenue_by_day = graphene.List(
        RevenueByDayType,
        description='Revenue grouped by order date',
    )

    @staticmethod
    def _orders_count() -> int:
        """Get total count of all orders in database."""
        result = Order.objects.aggregate(total=Count('id'))
        return int(result['total'] or 0)

    def resolve_total_orders(root, info):
        return Query._orders_count()

    def resolve_orders_count(root, info):
        return Query._orders_count()

    def resolve_total_revenue(root, info):
        result = Order.objects.aggregate(total=Sum('total_price'))
        return float(result['total'] or 0)

    def resolve_average_order_value(root, info):
        result = Order.objects.aggregate(avg=Avg('total_price'))
        return float(result['avg'] or 0)

    def resolve_top_products(root, info):
        """Return top 5 products by number of orders."""
        return (
            Product.objects.annotate(
                orders_count=Count('order_items__order', distinct=True),
            )
            .filter(orders_count__gt=0)
            .order_by('-orders_count', 'name')[:5]
        )

    def resolve_revenue_by_day(root, info):
        """Return cumulative daily revenue over all time."""
        rows = (
            Order.objects.annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(revenue=Sum('total_price'))
            .order_by('day')
        )
        return [
            RevenueByDayType(
                date=row['day'].isoformat(),
                revenue=float(row['revenue'] or 0),
            )
            for row in rows
            if row['day'] is not None
        ]


schema = graphene.Schema(query=Query)


# Example GraphQL queries:
#
# query {
#   totalOrders
#   ordersCount
#   totalRevenue
#   averageOrderValue
# }
#
# query {
#   revenueByDay {
#     date
#     revenue
#   }
# }
#
# query {
#   topProducts {
#     id
#     name
#     slug
#     ordersCount
#   }
# }
