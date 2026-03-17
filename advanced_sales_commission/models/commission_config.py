# Part of Odoo. See LICENSE file for full copyright and licensing details.
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CommissionConfig(models.Model):
    _name = 'commission.config'
    _description = 'Commission Configuration'
    _order = 'sequence, name'
    _rec_name = 'name'

    name = fields.Char(
        string='Configuration Name',
        required=True,
        help="Name of the commission configuration"
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Set to false to disable this configuration"
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Sequence for ordering configurations"
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        help="Company for which this configuration applies"
    )
    
    commission_type = fields.Selection([
        ('standard', 'Standard Commission'),
        ('partner_based', 'Partner Based'),
        ('product_based', 'Product Based'),
        ('margin_based', 'Margin Based'),
        ('discount_based', 'Discount Based'),
        ('hybrid', 'Hybrid (Multiple Rules)'),
    ], string='Commission Type', required=True, default='standard',
       help="Type of commission calculation method")
    
    calculation_method = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
        ('tiered', 'Tiered Structure'),
    ], string='Calculation Method', required=True, default='percentage',
       help="Method for calculating commission amounts")
    
    date_from = fields.Date(
        string='Effective From',
        help="Date from which this configuration is effective"
    )
    
    date_to = fields.Date(
        string='Effective Until',
        help="Date until which this configuration is effective"
    )
    
    auto_calculate = fields.Boolean(
        string='Auto Calculate',
        default=True,
        help="Automatically calculate commissions when invoices are validated"
    )
    
    auto_invoice = fields.Boolean(
        string='Auto Invoice',
        default=False,
        help="Automatically generate commission invoices"
    )
    
    default_rate = fields.Float(
        string='Default Commission Rate (%)',
        digits=(12, 4),
        help="Default commission rate when no specific rule applies"
    )
    
    # Relations
    user_id = fields.Many2one(
        'res.users',
        string="Responsible User",
        help="User responsible for this commission configuration"
    )
    rule_ids = fields.One2many(
        'commission.rule',
        'config_id',
        string='Commission Rules',
        help="Specific rules for this configuration"
    )
    
    assignment_ids = fields.One2many(
        'commission.assignment',
        'config_id',
        string='Assignments',
        help="Users assigned to this configuration"
    )
    
    # Computed fields
    rule_count = fields.Integer(
        string='Rules Count',
        compute='_compute_rule_count'
    )
    
    assignment_count = fields.Integer(
        string='Assignments Count',
        compute='_compute_assignment_count'
    )
    
    @api.depends('rule_ids')
    def _compute_rule_count(self):
        for config in self:
            config.rule_count = len(config.rule_ids)
    
    @api.depends('assignment_ids')
    def _compute_assignment_count(self):
        for config in self:
            config.assignment_count = len(config.assignment_ids)
    
    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for config in self:
            if config.date_from and config.date_to and config.date_from > config.date_to:
                raise ValidationError(_("Effective from date must be before effective until date."))
    
    @api.constrains('default_rate')
    def _check_default_rate(self):
        for config in self:
            if config.default_rate < 0 or config.default_rate > 100:
                raise ValidationError(_("Default commission rate must be between 0 and 100."))
    
    def action_view_rules(self):
        """Action to view commission rules for this configuration"""
        self.ensure_one()
        return {
            'name': _('Commission Rules'),
            'type': 'ir.actions.act_window',
            'res_model': 'commission.rule',
            'view_mode': 'list,form',
            'domain': [('config_id', '=', self.id)],
            'context': {'default_config_id': self.id},
        }
    
    def action_view_assignments(self):
        """Action to view assignments for this configuration"""
        self.ensure_one()
        return {
            'name': _('Commission Assignments'),
            'type': 'ir.actions.act_window',
            'res_model': 'commission.assignment',
            'view_mode': 'list,form',
            'domain': [('config_id', '=', self.id)],
            'context': {'default_config_id': self.id},
        }
    
    def get_applicable_config(self, user_id, date=None):
        """Get applicable commission configuration for a user on a specific date"""
        if not date:
            date = fields.Date.today()
        
        domain = [
            ('active', '=', True),
            ('assignment_ids.user_id', '=', user_id),
            ('assignment_ids.active', '=', True),
            '|', ('date_from', '=', False), ('date_from', '<=', date),
            '|', ('date_to', '=', False), ('date_to', '>=', date),
        ]
        
        return self.search(domain, limit=1)
    
    def calculate_commission(self, order_line, base_amount=None):
        """Calculate commission for a given order line"""
        self.ensure_one()
        
        if not base_amount:
            base_amount = order_line.price_subtotal
        
        # Find applicable rule
        applicable_rule = self.rule_ids.get_applicable_rule(order_line)
        
        if applicable_rule:
            return applicable_rule.calculate_commission(order_line, base_amount)
        else:
            # Use default rate
            if self.calculation_method == 'percentage':
                return base_amount * (self.default_rate / 100)
            elif self.calculation_method == 'fixed_amount':
                return self.default_rate
            else:
                return 0.0

