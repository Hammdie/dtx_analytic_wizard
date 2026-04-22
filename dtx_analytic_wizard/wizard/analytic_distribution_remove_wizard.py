from odoo import fields, models
from odoo.exceptions import UserError


class AnalyticDistributionRemoveWizard(models.TransientModel):
    _name = 'analytic.distribution.remove.wizard'
    _description = 'Remove Analytic Distribution Wizard'

    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )
    analytic_distribution = fields.Json(
        string='Analytic Accounts to Remove',
    )
    analytic_precision = fields.Integer(
        store=False,
        default=lambda self: self.env['decimal.precision'].precision_get("Percentage Analytic"),
    )
    remove_all = fields.Boolean(
        string='Remove All Analytic Accounts',
        default=False,
    )
    purchase_order_ids = fields.Many2many(
        'purchase.order',
        string='Purchase Orders',
    )
    account_move_ids = fields.Many2many(
        'account.move',
        string='Invoices',
    )

    def _get_lines(self):
        po_lines = self.env['purchase.order.line']
        for order in self.purchase_order_ids:
            po_lines |= order.order_line

        move_lines = self.env['account.move.line']
        for move in self.account_move_ids:
            move_lines |= move.invoice_line_ids

        return po_lines, move_lines

    def _check_draft_state(self):
        confirmed_orders = self.purchase_order_ids.filtered(lambda o: o.state != 'draft')
        if confirmed_orders:
            raise UserError(self.env._(
                "Analytic distribution can only be changed on draft purchase orders. "
                "The following orders are already confirmed: %(names)s",
                names=', '.join(confirmed_orders.mapped('name')),
            ))
        confirmed_moves = self.account_move_ids.filtered(lambda m: m.state != 'draft')
        if confirmed_moves:
            raise UserError(self.env._(
                "Analytic distribution can only be changed on draft invoices. "
                "The following invoices are already confirmed: %(names)s",
                names=', '.join(confirmed_moves.mapped('name')),
            ))

    def action_remove(self):
        self._check_draft_state()
        po_lines, move_lines = self._get_lines()

        if self.remove_all:
            for line in po_lines:
                line.analytic_distribution = {}
            for line in move_lines:
                line.analytic_distribution = {}
        else:
            keys_to_remove = list((self.analytic_distribution or {}).keys())
            if not keys_to_remove:
                return {'type': 'ir.actions.act_window_close'}
            for line in po_lines:
                existing = dict(line.analytic_distribution or {})
                for key in keys_to_remove:
                    existing.pop(key, None)
                line.analytic_distribution = existing
            for line in move_lines:
                existing = dict(line.analytic_distribution or {})
                for key in keys_to_remove:
                    existing.pop(key, None)
                line.analytic_distribution = existing

        return {'type': 'ir.actions.act_window_close'}
