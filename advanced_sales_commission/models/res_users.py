# Part of Odoo. See LICENSE file for full copyright and licensing details.
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_commission_eligible = fields.Boolean(
        string='Is Commission Eligible',
        default=True,
        help="Check this box if this user is eligible to earn sales commissions"
    )
    
    commission_assignment_ids = fields.One2many(
        'commission.assignment',
        'user_id',
        string='Commission Assignments',
        help="Commission configurations assigned to this user"
    )


