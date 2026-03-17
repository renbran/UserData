# Part of Odoo. See LICENSE file for full copyright and licensing details.
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CommissionCalculateWizard(models.TransientModel):
    _name = 'commission.calculate.wizard'
    _description = 'Commission Calculation Wizard'

    date_from = fields.Date(
        string='Start Date',
        required=True,
        default=fields.Date.today,
        help="Start date for commission calculation"
    )

    date_to = fields.Date(
        string='End Date',
        required=True,
        default=fields.Date.today,
        help="End date for commission calculation"
    )

    user_ids = fields.Many2many(
        'res.users',
        string='Salespersons',
        help="Select specific salespersons to calculate commissions for. Leave empty for all."
    )

    recalculate = fields.Boolean(
        string='Recalculate Existing',
        help="If checked, existing calculated commissions within the period will be recalculated."
    )

    def action_calculate_commissions(self):
        self.ensure_one()

        if self.date_from > self.date_to:
            raise UserError(_("Start Date cannot be after End Date."))

        domain = [
            ('date_order', '>=', self.date_from),
            ('date_order', '<=', self.date_to),
            ('state', 'in', ['sale', 'done']),
        ]

        if self.user_ids:
            domain.append(('user_id', 'in', self.user_ids.ids))

        orders = self.env['sale.order'].search(domain)

        if not orders:
            raise UserError(_("No sale orders found for the selected criteria."))

        calculated_records_count = 0

        for order in orders:
            # If recalculate is false, skip orders that already have commissions calculated
            if not self.recalculate and order.commission_calculated:
                continue

            # Delete existing commission records if recalculating
            if self.recalculate and order.commission_ids:
                order.commission_ids.unlink()
                order.commission_calculated = False

            records = self.env['commission.record'].calculate_commissions_for_order(order)
            if records:
                calculated_records_count += len(records)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Commission Calculation Complete'),
                'message': _('%d commission records processed.') % calculated_records_count,
                'type': 'success',
                'sticky': False,
            }
        }


