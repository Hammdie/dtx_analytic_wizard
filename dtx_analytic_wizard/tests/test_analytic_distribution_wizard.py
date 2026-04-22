from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'dtx_analytic_wizard')
class TestAnalyticDistributionWizard(TransactionCase):

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
        cls.purchase_journal = cls.env['account.journal'].search([
            ('type', '=', 'purchase'),
        ], limit=1)
        if not cls.purchase_journal:
            cls.purchase_journal = cls.env['account.journal'].create({
                'name': 'Test Purchase Journal',
                'type': 'purchase',
                'code': 'TPUR',
            })
        cls.expense_account = cls.env['account.account'].search([
            ('account_type', '=', 'expense'),
        ], limit=1)
        if not cls.expense_account:
            cls.expense_account = cls.env['account.account'].create({
                'name': 'Test Expense Account',
                'code': '600000',
                'account_type': 'expense',
            })
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
        return self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': 'Test Line',
                'product_qty': 1.0,
                'price_unit': 100.0,
                'analytic_distribution': analytic_distribution,
            })],
        })

    def _create_invoice(self, analytic_distribution=None):
        return self.env['account.move'].create({
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
                'analytic_distribution': analytic_distribution,
            })],
        })

    # ------------------------------------------------------------------
    # Assign Wizard
    # ------------------------------------------------------------------

    def test_01_apply_to_purchase_order_empty_lines(self):
        """Assign analytic accounts to empty PO line."""
        order = self._create_purchase_order()
        wizard = self.env['analytic.distribution.wizard'].create({
            'analytic_distribution': {str(self.analytic_account_1.id): 100},
            'purchase_order_ids': [(6, 0, [order.id])],
        })
        wizard.action_apply()
        self.assertEqual(
            order.order_line[0].analytic_distribution,
            {str(self.analytic_account_1.id): 100},
        )

    def test_02_merge_with_existing_distribution(self):
        """Existing accounts are preserved, new ones are added."""
        existing = {str(self.analytic_account_1.id): 50}
        order = self._create_purchase_order(analytic_distribution=existing)
        wizard = self.env['analytic.distribution.wizard'].create({
            'analytic_distribution': {str(self.analytic_account_2.id): 50},
            'purchase_order_ids': [(6, 0, [order.id])],
        })
        wizard.action_apply()
        dist = order.order_line[0].analytic_distribution
        self.assertEqual(dist[str(self.analytic_account_1.id)], 50)
        self.assertEqual(dist[str(self.analytic_account_2.id)], 50)

    def test_03_duplicate_key_overwritten_by_wizard(self):
        """Same account ID: wizard percentage overwrites existing."""
        existing = {str(self.analytic_account_1.id): 30}
        order = self._create_purchase_order(analytic_distribution=existing)
        wizard = self.env['analytic.distribution.wizard'].create({
            'analytic_distribution': {str(self.analytic_account_1.id): 70},
            'purchase_order_ids': [(6, 0, [order.id])],
        })
        wizard.action_apply()
        self.assertEqual(order.order_line[0].analytic_distribution[str(self.analytic_account_1.id)], 70)

    def test_04_apply_to_multiple_orders(self):
        """Wizard applies to multiple POs at once."""
        order1 = self._create_purchase_order()
        order2 = self._create_purchase_order()
        wizard = self.env['analytic.distribution.wizard'].create({
            'analytic_distribution': {str(self.analytic_account_1.id): 100},
            'purchase_order_ids': [(6, 0, [order1.id, order2.id])],
        })
        wizard.action_apply()
        for order in (order1, order2):
            self.assertEqual(
                order.order_line[0].analytic_distribution,
                {str(self.analytic_account_1.id): 100},
            )

    def test_05_empty_wizard_does_nothing(self):
        """Empty distribution returns early without changes."""
        existing = {str(self.analytic_account_1.id): 100}
        order = self._create_purchase_order(analytic_distribution=existing)
        wizard = self.env['analytic.distribution.wizard'].create({
            'analytic_distribution': {},
            'purchase_order_ids': [(6, 0, [order.id])],
        })
        result = wizard.action_apply()
        self.assertEqual(result, {'type': 'ir.actions.act_window_close'})
        self.assertEqual(order.order_line[0].analytic_distribution, existing)

    def test_06_apply_to_account_move(self):
        """Assign analytic accounts to invoice lines."""
        move = self._create_invoice()
        wizard = self.env['analytic.distribution.wizard'].create({
            'analytic_distribution': {str(self.analytic_account_2.id): 100},
            'account_move_ids': [(6, 0, [move.id])],
        })
        wizard.action_apply()
        self.assertEqual(
            move.invoice_line_ids[0].analytic_distribution,
            {str(self.analytic_account_2.id): 100},
        )

    def test_07_merge_account_move_existing(self):
        """Merge new accounts with existing invoice distribution."""
        move = self._create_invoice(
            analytic_distribution={str(self.analytic_account_1.id): 60},
        )
        wizard = self.env['analytic.distribution.wizard'].create({
            'analytic_distribution': {str(self.analytic_account_3.id): 40},
            'account_move_ids': [(6, 0, [move.id])],
        })
        wizard.action_apply()
        dist = move.invoice_line_ids[0].analytic_distribution
        self.assertEqual(dist[str(self.analytic_account_1.id)], 60)
        self.assertEqual(dist[str(self.analytic_account_3.id)], 40)

    def test_08_multiple_analytic_accounts_in_wizard(self):
        """Wizard with multiple accounts at once."""
        order = self._create_purchase_order()
        wizard = self.env['analytic.distribution.wizard'].create({
            'analytic_distribution': {
                str(self.analytic_account_1.id): 60,
                str(self.analytic_account_2.id): 40,
            },
            'purchase_order_ids': [(6, 0, [order.id])],
        })
        wizard.action_apply()
        dist = order.order_line[0].analytic_distribution
        self.assertEqual(dist[str(self.analytic_account_1.id)], 60)
        self.assertEqual(dist[str(self.analytic_account_2.id)], 40)

    # ------------------------------------------------------------------
    # Wizard field validation
    # ------------------------------------------------------------------

    def test_09_wizard_has_company_id_field(self):
        """Wizard must have company_id for the analytic_distribution widget."""
        self.assertIn('company_id', self.env['analytic.distribution.wizard']._fields)

    def test_10_wizard_fields_readable(self):
        """All wizard fields can be read without errors."""
        wizard = self.env['analytic.distribution.wizard'].create({
            'purchase_order_ids': [(6, 0, [])],
        })
        wizard.read(list(wizard._fields.keys()))

    def test_11_remove_wizard_has_company_id_field(self):
        """Remove wizard must have company_id."""
        self.assertIn('company_id', self.env['analytic.distribution.remove.wizard']._fields)

    def test_12_remove_wizard_fields_readable(self):
        """All remove wizard fields can be read without errors."""
        wizard = self.env['analytic.distribution.remove.wizard'].create({
            'purchase_order_ids': [(6, 0, [])],
        })
        wizard.read(list(wizard._fields.keys()))

    # ------------------------------------------------------------------
    # Draft state enforcement
    # ------------------------------------------------------------------

    def test_13_assign_blocked_on_confirmed_purchase_order(self):
        """Assign wizard raises UserError on confirmed PO."""
        order = self._create_purchase_order()
        order.button_confirm()
        wizard = self.env['analytic.distribution.wizard'].create({
            'analytic_distribution': {str(self.analytic_account_1.id): 100},
            'purchase_order_ids': [(6, 0, [order.id])],
        })
        with self.assertRaises(UserError):
            wizard.action_apply()

    def test_14_remove_blocked_on_confirmed_purchase_order(self):
        """Remove wizard raises UserError on confirmed PO."""
        order = self._create_purchase_order(
            analytic_distribution={str(self.analytic_account_1.id): 100},
        )
        order.button_confirm()
        wizard = self.env['analytic.distribution.remove.wizard'].create({
            'remove_all': True,
            'purchase_order_ids': [(6, 0, [order.id])],
        })
        with self.assertRaises(UserError):
            wizard.action_remove()

    def test_15_assign_blocked_on_posted_invoice(self):
        """Assign wizard raises UserError on posted invoice."""
        move = self._create_invoice()
        move.action_post()
        wizard = self.env['analytic.distribution.wizard'].create({
            'analytic_distribution': {str(self.analytic_account_1.id): 100},
            'account_move_ids': [(6, 0, [move.id])],
        })
        with self.assertRaises(UserError):
            wizard.action_apply()

    def test_16_remove_blocked_on_posted_invoice(self):
        """Remove wizard raises UserError on posted invoice."""
        move = self._create_invoice()
        move.action_post()
        wizard = self.env['analytic.distribution.remove.wizard'].create({
            'remove_all': True,
            'account_move_ids': [(6, 0, [move.id])],
        })
        with self.assertRaises(UserError):
            wizard.action_remove()

    # ------------------------------------------------------------------
    # Remove wizard
    # ------------------------------------------------------------------

    def test_17_remove_all_from_purchase_order(self):
        """Remove all clears analytic distribution on PO lines."""
        order = self._create_purchase_order(
            analytic_distribution={str(self.analytic_account_1.id): 100},
        )
        wizard = self.env['analytic.distribution.remove.wizard'].create({
            'remove_all': True,
            'purchase_order_ids': [(6, 0, [order.id])],
        })
        wizard.action_remove()
        self.assertEqual(order.order_line[0].analytic_distribution, {})

    def test_18_remove_specific_account(self):
        """Remove specific account keeps other accounts intact."""
        dist = {
            str(self.analytic_account_1.id): 60,
            str(self.analytic_account_2.id): 40,
        }
        order = self._create_purchase_order(analytic_distribution=dist)
        wizard = self.env['analytic.distribution.remove.wizard'].create({
            'analytic_distribution': {str(self.analytic_account_1.id): 100},
            'purchase_order_ids': [(6, 0, [order.id])],
        })
        wizard.action_remove()
        result = order.order_line[0].analytic_distribution
        self.assertNotIn(str(self.analytic_account_1.id), result)
        self.assertEqual(result[str(self.analytic_account_2.id)], 40)

    def test_19_remove_empty_does_nothing(self):
        """Remove with empty selection returns early."""
        existing = {str(self.analytic_account_1.id): 100}
        order = self._create_purchase_order(analytic_distribution=existing)
        wizard = self.env['analytic.distribution.remove.wizard'].create({
            'analytic_distribution': {},
            'purchase_order_ids': [(6, 0, [order.id])],
        })
        result = wizard.action_remove()
        self.assertEqual(result, {'type': 'ir.actions.act_window_close'})
        self.assertEqual(order.order_line[0].analytic_distribution, existing)

    def test_20_remove_all_from_invoice(self):
        """Remove all clears analytic distribution on invoice lines."""
        move = self._create_invoice(
            analytic_distribution={str(self.analytic_account_1.id): 100},
        )
        wizard = self.env['analytic.distribution.remove.wizard'].create({
            'remove_all': True,
            'account_move_ids': [(6, 0, [move.id])],
        })
        wizard.action_remove()
        self.assertEqual(move.invoice_line_ids[0].analytic_distribution, {})

    def test_21_remove_specific_from_invoice(self):
        """Remove specific account from invoice lines."""
        dist = {
            str(self.analytic_account_1.id): 50,
            str(self.analytic_account_2.id): 50,
        }
        move = self._create_invoice(analytic_distribution=dist)
        wizard = self.env['analytic.distribution.remove.wizard'].create({
            'analytic_distribution': {str(self.analytic_account_2.id): 100},
            'account_move_ids': [(6, 0, [move.id])],
        })
        wizard.action_remove()
        result = move.invoice_line_ids[0].analytic_distribution
        self.assertIn(str(self.analytic_account_1.id), result)
        self.assertNotIn(str(self.analytic_account_2.id), result)

    def test_22_remove_nonexistent_key(self):
        """Removing a key that doesn't exist does not raise."""
        existing = {str(self.analytic_account_1.id): 100}
        order = self._create_purchase_order(analytic_distribution=existing)
        wizard = self.env['analytic.distribution.remove.wizard'].create({
            'analytic_distribution': {str(self.analytic_account_3.id): 100},
            'purchase_order_ids': [(6, 0, [order.id])],
        })
        wizard.action_remove()
        self.assertEqual(order.order_line[0].analytic_distribution, existing)

    def test_23_assign_to_multiple_lines(self):
        """Wizard assigns to all lines of a PO with multiple lines."""
        order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {'product_id': self.product.id, 'name': 'Line 1', 'product_qty': 1, 'price_unit': 100}),
                (0, 0, {'product_id': self.product.id, 'name': 'Line 2', 'product_qty': 2, 'price_unit': 200}),
            ],
        })
        wizard = self.env['analytic.distribution.wizard'].create({
            'analytic_distribution': {str(self.analytic_account_1.id): 100},
            'purchase_order_ids': [(6, 0, [order.id])],
        })
        wizard.action_apply()
        for line in order.order_line:
            self.assertEqual(line.analytic_distribution, {str(self.analytic_account_1.id): 100})

    def test_24_remove_all_from_multiple_lines(self):
        """Remove all clears all lines of a multi-line PO."""
        dist = {str(self.analytic_account_1.id): 100}
        order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {'product_id': self.product.id, 'name': 'Line 1', 'product_qty': 1, 'price_unit': 100, 'analytic_distribution': dist}),
                (0, 0, {'product_id': self.product.id, 'name': 'Line 2', 'product_qty': 2, 'price_unit': 200, 'analytic_distribution': dist}),
            ],
        })
        wizard = self.env['analytic.distribution.remove.wizard'].create({
            'remove_all': True,
            'purchase_order_ids': [(6, 0, [order.id])],
        })
        wizard.action_remove()
        for line in order.order_line:
            self.assertEqual(line.analytic_distribution, {})
