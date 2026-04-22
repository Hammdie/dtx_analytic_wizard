from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged("post_install", "-at_install", "dtx_e2e")
class TestAnalyticWizardTour(HttpCase):

    def setUp(self):
        super().setUp()
        # Grant analytic accounting access to admin user
        group_analytic = self.env.ref('analytic.group_analytic_accounting')
        self.env.ref('base.user_admin').groups_id += group_analytic
        plan = self.env['account.analytic.plan'].create({
            'name': 'Tour Test Plan',
        })
        self.analytic_account = self.env['account.analytic.account'].create({
            'name': 'Tour Kostenstelle',
            'plan_id': plan.id,
        })
        partner = self.env['res.partner'].create({
            'name': 'Tour Test Partner',
        })
        product = self.env['product.product'].create({
            'name': 'Tour Test Product',
            'type': 'consu',
        })
        self.order = self.env['purchase.order'].create({
            'partner_id': partner.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'name': 'Tour Test Line',
                'product_qty': 1.0,
                'price_unit': 100.0,
                'analytic_distribution': {
                    str(self.analytic_account.id): 100,
                },
            })],
        })

    def test_assign_analytic_tour(self):
        """Test the Assign Analytic Accounts wizard via UI tour."""
        self.start_tour(
            "/odoo/purchase",
            "test_analytic_distribution_assign_tour",
            login="admin",
        )

    def test_remove_analytic_tour(self):
        """Test the Remove Analytic Accounts wizard via UI tour."""
        self.start_tour(
            "/odoo/purchase",
            "test_analytic_distribution_remove_tour",
            login="admin",
        )
        self.order.invalidate_recordset()
        line = self.order.order_line[0]
        self.assertFalse(
            line.analytic_distribution,
            "Analytic distribution should be empty after Remove All",
        )
