from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install', 'dtx_analytic_wizard')
class TestAnalyticWizardTour(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.ref('base.user_admin').group_ids += cls.env.ref(
            'analytic.group_analytic_accounting',
        )
        plan = cls.env['account.analytic.plan'].create({'name': 'Tour Plan'})
        account = cls.env['account.analytic.account'].create({
            'name': 'Tour Account',
            'plan_id': plan.id,
        })
        partner = cls.env['res.partner'].create({'name': 'Tour Partner'})
        product = cls.env['product.product'].create({
            'name': 'Tour Product',
            'type': 'consu',
        })
        cls.env['purchase.order'].create({
            'partner_id': partner.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'name': 'Tour Line',
                'product_qty': 1.0,
                'price_unit': 50.0,
                'analytic_distribution': {str(account.id): 100},
            })],
        })

    def test_assign_analytic_tour(self):
        self.start_tour(
            '/odoo/purchase',
            'test_analytic_distribution_assign_tour',
            login='admin',
        )

    def test_remove_analytic_tour(self):
        self.start_tour(
            '/odoo/purchase',
            'test_analytic_distribution_remove_tour',
            login='admin',
        )
