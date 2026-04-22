from odoo import _, fields, models
from odoo.exceptions import UserError


class AnalyticDistributionWizard(models.TransientModel):
    _name = 'analytic.distribution.wizard'
    _description = 'Assign Analytic Distribution Wizard'

    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )
    analytic_distribution = fields.Json(
        string='Analytic Distribution',
    )
    analytic_precision = fields.Integer(
        store=False,
        default=lambda self: self.env['decimal.precision'].precision_get("Percentage Analytic"),
    )
    purchase_order_ids = fields.Many2many(
        'purchase.order',
        string='Purchase Orders',
    )
    account_move_ids = fields.Many2many(
        'account.move',
        string='Invoices',
    )

    def _check_draft_state(self):
        confirmed_orders = self.purchase_order_ids.filtered(lambda o: o.state != 'draft')
        if confirmed_orders:
            raise UserError(_(
                "Analytic distribution can only be changed on draft purchase orders. "
                "The following orders are already confirmed: %s",
                ', '.join(confirmed_orders.mapped('name')),
            ))
        confirmed_moves = self.account_move_ids.filtered(lambda m: m.state != 'draft')
        if confirmed_moves:
            raise UserError(_(
                "Analytic distribution can only be changed on draft invoices. "
                "The following invoices are already confirmed: %s",
                ', '.join(confirmed_moves.mapped('name')),
            ))

    def action_apply(self):
        self._check_draft_state()
        new_distribution = self.analytic_distribution or {}
        if not new_distribution:
            return {'type': 'ir.actions.act_window_close'}

        lines = self.env['purchase.order.line']
        for order in self.purchase_order_ids:
            lines |= order.order_line

        move_lines = self.env['account.move.line']
        for move in self.account_move_ids:
            move_lines |= move.invoice_line_ids

        for line in lines:
            existing = line.analytic_distribution or {}
            line.analytic_distribution = {**existing, **new_distribution}

        for line in move_lines:
            existing = line.analytic_distribution or {}
            line.analytic_distribution = {**existing, **new_distribution}

        return {'type': 'ir.actions.act_window_close'}
