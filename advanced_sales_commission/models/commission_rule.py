# Part of Odoo. See LICENSE file for full copyright and licensing details.
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import json


class CommissionRule(models.Model):
    _name = 'commission.rule'
    _description = 'Commission Rule'
    _order = 'config_id, sequence, name'
    _rec_name = 'name'

    rule_ids = fields.One2many(
        'commission.rule',
        'config_id',
        string='Rules',
        help="Commission rules linked to this configuration"
    )

    name = fields.Char(
        string='Rule Name',
        required=True,
        help="Name of the commission rule"
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Set to false to disable this rule"
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Sequence for rule evaluation (lower numbers evaluated first)"
    )
    
    config_id = fields.Many2one(
        'commission.config',
        string='Commission Configuration',
        required=True,
        ondelete='cascade',
        help="Configuration this rule belongs to"
    )
    
    condition_type = fields.Selection([
        ('product', 'Product'),
        ('category', 'Product Category'),
        ('partner', 'Customer'),
        ('partner_category', 'Customer Category'),
        ('margin', 'Margin'),
        ('discount', 'Discount'),
        ('amount', 'Order Amount'),
        ('quantity', 'Quantity'),
        ('always', 'Always Apply'),
    ], string='Condition Type', required=True, default='always',
       help="Type of condition for this rule")
    
    condition_operator = fields.Selection([
        ('=', 'Equal to'),
        ('!=', 'Not equal to'),
        ('>', 'Greater than'),
        ('>=', 'Greater than or equal'),
        ('<', 'Less than'),
        ('<=', 'Less than or equal'),
        ('in', 'In list'),
        ('not_in', 'Not in list'),
        ('contains', 'Contains'),
        ('between', 'Between'),
    ], string='Operator', default='=',
       help="Operator for condition evaluation")
    
    condition_value = fields.Text(
        string='Condition Value',
        help="Value(s) for condition evaluation (JSON format for complex conditions)"
    )
    
    # Specific condition fields for easier configuration
    product_ids = fields.Many2many(
        'product.product',
        string='Products',
        help="Products this rule applies to"
    )
    
    category_ids = fields.Many2many(
        'product.category',
        string='Product Categories',
        help="Product categories this rule applies to"
    )
    
    partner_ids = fields.Many2many(
        'res.partner',
        string='Customers',
        help="Customers this rule applies to"
    )
    
    partner_category_ids = fields.Many2many(
        'res.partner.category',
        string='Customer Tags',
        help="Customer tags this rule applies to"
    )
    
    min_amount = fields.Float(
        string='Minimum Amount',
        digits=(12, 2),
        help="Minimum order amount for this rule"
    )
    
    max_amount = fields.Float(
        string='Maximum Amount',
        digits=(12, 2),
        help="Maximum order amount for this rule"
    )
    
    min_margin = fields.Float(
        string='Minimum Margin (%)',
        digits=(12, 4),
        help="Minimum margin percentage for this rule"
    )
    
    max_margin = fields.Float(
        string='Maximum Margin (%)',
        digits=(12, 4),
        help="Maximum margin percentage for this rule"
    )
    
    min_discount = fields.Float(
        string='Minimum Discount (%)',
        digits=(12, 4),
        help="Minimum discount percentage for this rule"
    )
    
    max_discount = fields.Float(
        string='Maximum Discount (%)',
        digits=(12, 4),
        help="Maximum discount percentage for this rule"
    )
    
    # Commission calculation fields
    commission_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
        ('margin_percentage', 'Margin Percentage'),
    ], string='Commission Type', required=True, default='percentage',
       help="How to calculate commission for this rule")
    
    commission_rate = fields.Float(
        string='Commission Rate',
        digits=(12, 4),
        help="Commission rate (percentage or fixed amount)"
    )
    
    # Tiered commission support
    is_tiered = fields.Boolean(
        string='Tiered Commission',
        help="Enable tiered commission structure"
    )
    
    tier_ids = fields.One2many(
        'commission.rule.tier',
        'rule_id',
        string='Commission Tiers',
        help="Tiered commission structure"
    )
    
    # Additional settings
    exclude_discount = fields.Boolean(
        string='Exclude Discount',
        help="Exclude discount amount from commission calculation"
    )
    
    include_tax = fields.Boolean(
        string='Include Tax',
        help="Include tax in commission calculation base"
    )
    
    notes = fields.Text(
        string='Notes',
        help="Additional notes for this rule"
    )
    
    @api.constrains('min_amount', 'max_amount')
    def _check_amounts(self):
        for rule in self:
            if rule.min_amount and rule.max_amount and rule.min_amount > rule.max_amount:
                raise ValidationError(_("Minimum amount must be less than maximum amount."))
    
    @api.constrains('min_margin', 'max_margin')
    def _check_margins(self):
        for rule in self:
            if rule.min_margin and rule.max_margin and rule.min_margin > rule.max_margin:
                raise ValidationError(_("Minimum margin must be less than maximum margin."))
    
    @api.constrains('min_discount', 'max_discount')
    def _check_discounts(self):
        for rule in self:
            if rule.min_discount and rule.max_discount and rule.min_discount > rule.max_discount:
                raise ValidationError(_("Minimum discount must be less than maximum discount."))
    
    @api.constrains('commission_rate')
    def _check_commission_rate(self):
        for rule in self:
            if rule.commission_type == 'percentage' and (rule.commission_rate < 0 or rule.commission_rate > 100):
                raise ValidationError(_("Commission rate must be between 0 and 100 for percentage type."))
    
    def get_applicable_rule(self, order_line):
        """Find the first applicable rule for the given order line"""
        for rule in self.sorted('sequence'):
            if rule.is_applicable(order_line):
                return rule
        return False
    
    def is_applicable(self, order_line):
        """Check if this rule is applicable to the given order line"""
        self.ensure_one()
        
        if not self.active:
            return False
        
        # Check product condition
        if self.condition_type == 'product' and self.product_ids:
            if order_line.product_id not in self.product_ids:
                return False
        
        # Check category condition
        if self.condition_type == 'category' and self.category_ids:
            if order_line.product_id.categ_id not in self.category_ids:
                return False
        
        # Check partner condition
        if self.condition_type == 'partner' and self.partner_ids:
            if order_line.order_id.partner_id not in self.partner_ids:
                return False
        
        # Check partner category condition
        if self.condition_type == 'partner_category' and self.partner_category_ids:
            partner_categories = order_line.order_id.partner_id.category_id
            if not any(cat in self.partner_category_ids for cat in partner_categories):
                return False
        
        # Check amount conditions
        if self.min_amount and order_line.price_subtotal < self.min_amount:
            return False
        if self.max_amount and order_line.price_subtotal > self.max_amount:
            return False
        
        # Check margin conditions
        if hasattr(order_line, 'margin_percent'):
            if self.min_margin and order_line.margin_percent < self.min_margin:
                return False
            if self.max_margin and order_line.margin_percent > self.max_margin:
                return False
        
        # Check discount conditions
        if self.min_discount and order_line.discount < self.min_discount:
            return False
        if self.max_discount and order_line.discount > self.max_discount:
            return False
        
        return True
    
    def calculate_commission(self, order_line, base_amount=None):
        """Calculate commission for the given order line using this rule"""
        self.ensure_one()
        
        if not base_amount:
            base_amount = order_line.price_subtotal
            
        # Adjust base amount based on rule settings
        if self.exclude_discount and hasattr(order_line, 'discount'):
            # Add back the discount amount
            discount_amount = (order_line.price_unit * order_line.product_uom_qty * order_line.discount) / 100
            base_amount += discount_amount
        
        if self.include_tax and hasattr(order_line, 'price_total'):
            base_amount = order_line.price_total
        
        # Calculate commission based on type
        if self.commission_type == 'percentage':
            return base_amount * (self.commission_rate / 100)
        elif self.commission_type == 'fixed_amount':
            return self.commission_rate
        elif self.commission_type == 'margin_percentage' and hasattr(order_line, 'margin'):
            return order_line.margin * (self.commission_rate / 100)
        
        return 0.0


class CommissionRuleTier(models.Model):
    _name = 'commission.rule.tier'
    _description = 'Commission Rule Tier'
    _order = 'rule_id, sequence'
    
    rule_id = fields.Many2one(
        'commission.rule',
        string='Commission Rule',
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    name = fields.Char(
        string='Tier Name',
        required=True
    )
    
    min_value = fields.Float(
        string='Minimum Value',
        digits=(12, 2),
        required=True
    )
    
    max_value = fields.Float(
        string='Maximum Value',
        digits=(12, 2)
    )
    
    commission_rate = fields.Float(
        string='Commission Rate',
        digits=(12, 4),
        required=True
    )
    
    @api.constrains('min_value', 'max_value')
    def _check_values(self):
        for tier in self:
            if tier.max_value and tier.min_value > tier.max_value:
                raise ValidationError(_("Minimum value must be less than maximum value."))

