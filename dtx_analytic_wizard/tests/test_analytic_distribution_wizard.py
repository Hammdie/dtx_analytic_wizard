from odoo import fields
from odoo.addons.dtx_test_base.tests.common import DtxTestCase
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestAnalyticDistributionWizard(DtxTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.analytic_plan = cls.env['account.analytic.plan'].create({
            'name': 'Test Plan',
        })
        cls.analytic_account_1 = cls.env['account.analytic.account'].create({
            'name': 'Kostenstelle A',
            'plan_id': cls.analytic_plan.id,
        })
        cls.analytic_account_2 = cls.env['account.analytic.account'].create({
            'name': 'Kostenstelle B',
            'plan_id': cls.analytic_plan.id,
        })
        cls.analytic_account_3 = cls.env['account.analytic.account'].create({
            'name': 'Kostenstelle C',
            'plan_id': cls.analytic_plan.id,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
        })
        # Ensure purchase journal exists (Pipeline may not have Chart of Accounts)
        cls.purchase_journal = cls.env['account.journal'].search([
            ('type', '=', 'purchase'),
        ], limit=1)
        if not cls.purchase_journal:
            cls.purchase_journal = cls.env['account.journal'].create({
                'name': 'Test Purchase Journal',
                'type': 'purchase',
                'code': 'TPUR',
            })
        # Ensure expense account exists
        cls.expense_account = cls.env['account.account'].search([
            ('account_type', '=', 'expense'),
        ], limit=1)
        if not cls.expense_account:
            cls.expense_account = cls.env['account.account'].create({
                'name': 'Test Expense Account',
                'code': '600000',
                'account_type': 'expense',
            })
        # Ensure payable account exists (needed for payment_term lines on invoices)
        payable_account = cls.env['account.account'].search([
            ('account_type', '=', 'liability_payable'),
        ], limit=1)
        if not payable_account:
            payable_account = cls.env['account.account'].create({
                'name': 'Test Payable Account',
                'code': '200000',
                'account_type': 'liability_payable',
                'reconcile': True,
            })
        cls.partner.property_account_payable_id = payable_account

    def _create_purchase_order(self, analytic_distribution=None):
        order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': 'Test Line',
                'product_qty': 1.0,
                'price_unit': 100.0,
                'analytic_distribution': analytic_distribution,
            })],
        })
        return order

    def test_01_apply_to_purchase_order_empty_lines(self):
        """Wizard weist Kostenstellen auf leere Positionen zu."""
        order = self._create_purchase_order()
        wizard = self.env['analytic.distribution.wizard'].create({
            'analytic_distribution': {
                str(self.analytic_account_1.id): 100,
            },
            'purchase_order_ids': [(6, 0, [order.id])],
        })
        wizard.action_apply()
        line = order.order_line[0]
        self.assertEqual(
            line.analytic_distribution,
            {str(self.analytic_account_1.id): 100},
        )

    def test_02_merge_with_existing_distribution(self):
        """Bestehende Kostenstellen bleiben erhalten, neue werden ergänzt."""
        existing = {str(self.analytic_account_1.id): 50}
        order = self._create_purchase_order(analytic_distribution=existing)
        wizard = self.env['analytic.distribution.wizard'].create({
            'analytic_distribution': {
                str(self.analytic_account_2.id): 50,
            },
            'purchase_order_ids': [(6, 0, [order.id])],
        })
        wizard.action_apply()
        line = order.order_line[0]
        self.assertIn(str(self.analytic_account_1.id), line.analytic_distribution)
        self.assertIn(str(self.analytic_account_2.id), line.analytic_distribution)
        self.assertEqual(line.analytic_distribution[str(self.analytic_account_1.id)], 50)
        self.assertEqual(line.analytic_distribution[str(self.analytic_account_2.id)], 50)

    def test_03_duplicate_key_overwritten_by_wizard(self):
        """Bei gleichem Key wird der Prozentsatz aus dem Wizard übernommen."""
        existing = {str(self.analytic_account_1.id): 30}
        order = self._create_purchase_order(analytic_distribution=existing)
        wizard = self.env['analytic.distribution.wizard'].create({
            'analytic_distribution': {
                str(self.analytic_account_1.id): 70,
            },
            'purchase_order_ids': [(6, 0, [order.id])],
        })
        wizard.action_apply()
        line = order.order_line[0]
        self.assertEqual(line.analytic_distribution[str(self.analytic_account_1.id)], 70)

    def test_04_apply_to_multiple_orders(self):
        """Wizard wendet Kostenstellen auf mehrere Bestellungen an."""
        order1 = self._create_purchase_order()
        order2 = self._create_purchase_order()
        wizard = self.env['analytic.distribution.wizard'].create({
            'analytic_distribution': {
                str(self.analytic_account_1.id): 100,
            },
            'purchase_order_ids': [(6, 0, [order1.id, order2.id])],
        })
        wizard.action_apply()
        for order in (order1, order2):
            self.assertEqual(
                order.order_line[0].analytic_distribution,
                {str(self.analytic_account_1.id): 100},
            )

    def test_05_empty_wizard_does_nothing(self):
        """Leere Wizard-Auswahl ändert nichts."""
        existing = {str(self.analytic_account_1.id): 100}
        order = self._create_purchase_order(analytic_distribution=existing)
        wizard = self.env['analytic.distribution.wizard'].create({
            'analytic_distribution': {},
            'purchase_order_ids': [(6, 0, [order.id])],
        })
        result = wizard.action_apply()
        self.assertEqual(result, {'type': 'ir.actions.act_window_close'})
        self.assertEqual(
            order.order_line[0].analytic_distribution,
            existing,
        )

    def test_06_apply_to_account_move(self):
        """Wizard weist Kostenstellen auf Rechnungspositionen zu."""
        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'journal_id': self.purchase_journal.id,
            'partner_id': self.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': 'Test Invoice Line',
                'quantity': 1.0,
                'price_unit': 200.0,
                'account_id': self.expense_account.id,
            })],
        })
        wizard = self.env['analytic.distribution.wizard'].create({
            'analytic_distribution': {
                str(self.analytic_account_2.id): 100,
            },
            'account_move_ids': [(6, 0, [move.id])],
        })
        wizard.action_apply()
        inv_line = move.invoice_line_ids[0]
        self.assertEqual(
            inv_line.analytic_distribution,
            {str(self.analytic_account_2.id): 100},
        )

    def test_07_merge_account_move_existing(self):
        """Merge auf Rechnungspositionen mit bestehender Verteilung."""
        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'journal_id': self.purchase_journal.id,
            'partner_id': self.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': 'Test Invoice Line',
                'quantity': 1.0,
                'price_unit': 200.0,
                'account_id': self.expense_account.id,
                'analytic_distribution': {
                    str(self.analytic_account_1.id): 60,
                },
            })],
        })
        wizard = self.env['analytic.distribution.wizard'].create({
            'analytic_distribution': {
                str(self.analytic_account_3.id): 40,
            },
            'account_move_ids': [(6, 0, [move.id])],
        })
        wizard.action_apply()
        inv_line = move.invoice_line_ids[0]
        self.assertIn(str(self.analytic_account_1.id), inv_line.analytic_distribution)
        self.assertIn(str(self.analytic_account_3.id), inv_line.analytic_distribution)
        self.assertEqual(inv_line.analytic_distribution[str(self.analytic_account_1.id)], 60)
        self.assertEqual(inv_line.analytic_distribution[str(self.analytic_account_3.id)], 40)

    def test_08_multiple_analytic_accounts_in_wizard(self):
        """Wizard mit mehreren Kostenstellen gleichzeitig."""
        order = self._create_purchase_order()
        wizard = self.env['analytic.distribution.wizard'].create({
            'analytic_distribution': {
                str(self.analytic_account_1.id): 60,
                str(self.analytic_account_2.id): 40,
            },
            'purchase_order_ids': [(6, 0, [order.id])],
        })
        wizard.action_apply()
        line = order.order_line[0]
        self.assertEqual(line.analytic_distribution[str(self.analytic_account_1.id)], 60)
        self.assertEqual(line.analytic_distribution[str(self.analytic_account_2.id)], 40)

    def test_09_wizard_has_company_id_field(self):
        """Wizard muss company_id haben, da das analytic_distribution Widget es erwartet."""
        self.assertIn(
            'company_id',
            self.env['analytic.distribution.wizard']._fields,
            "analytic.distribution.wizard needs company_id for the analytic_distribution widget",
        )

    def test_10_wizard_onchange_does_not_raise(self):
        """Prüft dass alle Felder des Wizards gelesen werden können ohne Fehler."""
        wizard = self.env['analytic.distribution.wizard'].create({
            'purchase_order_ids': [(6, 0, [])],
        })
        # Read all fields to simulate what the UI does when opening the wizard.
        # This catches missing fields like company_id or analytic_precision.
        wizard.read(list(wizard._fields.keys()))

    def test_11_remove_wizard_has_company_id_field(self):
        """Remove-Wizard muss company_id haben."""
        self.assertIn(
            'company_id',
            self.env['analytic.distribution.remove.wizard']._fields,
            "analytic.distribution.remove.wizard needs company_id for the analytic_distribution widget",
        )

    def test_12_remove_wizard_onchange_does_not_raise(self):
        """Prüft dass alle Felder des Remove-Wizards gelesen werden können ohne Fehler."""
        wizard = self.env['analytic.distribution.remove.wizard'].create({
            'purchase_order_ids': [(6, 0, [])],
        })
        wizard.read(list(wizard._fields.keys()))

    def test_13_assign_blocked_on_confirmed_purchase_order(self):
        """Assign-Wizard darf bei bestätigter Bestellung nicht angewendet werden."""
        order = self._create_purchase_order()
        order.button_confirm()
        wizard = self.env['analytic.distribution.wizard'].create({
            'analytic_distribution': {
                str(self.analytic_account_1.id): 100,
            },
            'purchase_order_ids': [(6, 0, [order.id])],
        })
        with self.assertRaises(UserError):
            wizard.action_apply()

    def test_14_remove_blocked_on_confirmed_purchase_order(self):
        """Remove-Wizard darf bei bestätigter Bestellung nicht angewendet werden."""
        existing = {str(self.analytic_account_1.id): 100}
        order = self._create_purchase_order(analytic_distribution=existing)
        order.button_confirm()
        wizard = self.env['analytic.distribution.remove.wizard'].create({
            'remove_all': True,
            'purchase_order_ids': [(6, 0, [order.id])],
        })
        with self.assertRaises(UserError):
            wizard.action_remove()

    def test_15_assign_blocked_on_posted_invoice(self):
        """Assign-Wizard darf bei bestätigter Rechnung nicht angewendet werden."""
        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'journal_id': self.purchase_journal.id,
            'partner_id': self.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': 'Test Invoice Line',
                'quantity': 1.0,
                'price_unit': 200.0,
                'account_id': self.expense_account.id,
            })],
        })
        move.action_post()
        wizard = self.env['analytic.distribution.wizard'].create({
            'analytic_distribution': {
                str(self.analytic_account_1.id): 100,
            },
            'account_move_ids': [(6, 0, [move.id])],
        })
        with self.assertRaises(UserError):
            wizard.action_apply()

    def test_16_remove_blocked_on_posted_invoice(self):
        """Remove-Wizard darf bei bestätigter Rechnung nicht angewendet werden."""
        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'journal_id': self.purchase_journal.id,
            'partner_id': self.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': 'Test Invoice Line',
                'quantity': 1.0,
                'price_unit': 200.0,
                'account_id': self.expense_account.id,
            })],
        })
        move.action_post()
        wizard = self.env['analytic.distribution.remove.wizard'].create({
            'remove_all': True,
            'account_move_ids': [(6, 0, [move.id])],
        })
        with self.assertRaises(UserError):
            wizard.action_remove()
