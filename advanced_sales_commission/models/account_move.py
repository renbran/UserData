# Part of Odoo. See LICENSE file for full copyright and licensing details.
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    commission_calculated = fields.Boolean(
        string='Commission Calculated',
        copy=False,
        help="Indicates if commissions have been calculated for this invoice"
    )
    
    commission_ids = fields.One2many(
        'commission.record',
        'invoice_id',
        string='Commission Records',
        help="Commission records generated from this invoice"
    )

    def action_post(self):
        res = super(AccountMove, self).action_post()
        # Trigger commission calculation upon invoice validation (posting)
        # This part will be handled by a cron job or a dedicated wizard for invoices
        # For now, we will assume commissions are primarily calculated from sale orders.
        # If commission needs to be calculated on invoice, this method can be extended.
        return res


