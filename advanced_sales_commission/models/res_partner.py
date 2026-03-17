# Part of Odoo. See LICENSE file for full copyright and licensing details.
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_commission_partner = fields.Boolean(
        string='Is Commission Partner',
        help="Check this box if this partner is eligible for commission (e.g., affiliated partner)"
    )
    
    commission_category = fields.Selection([
        ('standard', 'Standard'),
        ('premium', 'Premium'),
        ('vip', 'VIP'),
    ], string='Commission Category',
       help="Category for commission calculation (e.g., for tiered partner commissions)"
    )
    
    commission_rate_override = fields.Float(
        string='Commission Rate Override (%)',
        digits=(12, 4),
        help="Override the default commission rate for this partner"
    )


