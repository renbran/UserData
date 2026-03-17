# Part of Odoo. See LICENSE file for full copyright and licensing details.
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CommissionAssignment(models.Model):
    _name = 'commission.assignment'
    _description = 'Commission Assignment'
    _order = 'user_id, date_from desc'
    _rec_name = 'display_name'

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Set to false to disable this assignment"
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        required=True,
        domain=[('share', '=', False)],
        help="Salesperson assigned to this commission configuration"
    )
    
    config_id = fields.Many2one(
        'commission.config',
        string='Commission Configuration',
        required=True,
        help="Commission configuration for this assignment"
    )
    
    date_from = fields.Date(
        string='Valid From',
        required=True,
        default=fields.Date.today,
        help="Date from which this assignment is valid"
    )
    
    date_to = fields.Date(
        string='Valid Until',
        help="Date until which this assignment is valid (leave empty for no end date)"
    )
    
    # Hierarchical commission support
    manager_id = fields.Many2one(
        'res.users',
        string='Sales Manager',
        domain=[('share', '=', False)],
        help="Sales manager who gets a commission from this salesperson's sales"
    )
    
    manager_rate = fields.Float(
        string='Manager Commission Rate (%)',
        digits=(12, 4),
        help="Commission rate for the sales manager"
    )
    
    director_id = fields.Many2one(
        'res.users',
        string='Sales Director',
        domain=[('share', '=', False)],
        help="Sales director who gets a commission from this salesperson's sales"
    )
    
    director_rate = fields.Float(
        string='Director Commission Rate (%)',
        digits=(12, 4),
        help="Commission rate for the sales director"
    )
    
    # Override settings
    rate_override = fields.Float(
        string='Rate Override (%)',
        digits=(12, 4),
        help="Override the default commission rate for this salesperson"
    )
    
    use_rate_override = fields.Boolean(
        string='Use Rate Override',
        help="Use the rate override instead of configuration default"
    )
    
    # Additional settings
    commission_on_payment = fields.Boolean(
        string='Commission on Payment',
        help="Calculate commission only when payment is received"
    )
    
    min_margin_required = fields.Float(
        string='Minimum Margin Required (%)',
        digits=(12, 4),
        help="Minimum margin required for commission calculation"
    )
    
    exclude_returns = fields.Boolean(
        string='Exclude Returns',
        default=True,
        help="Exclude credit notes/returns from commission calculation"
    )
    
    notes = fields.Text(
        string='Notes',
        help="Additional notes for this assignment"
    )
    
    # Computed fields
    commission_count = fields.Integer(
        string='Commission Records',
        compute='_compute_commission_count'
    )
    
    total_commission = fields.Float(
        string='Total Commission',
        compute='_compute_total_commission',
        digits=(12, 2)
    )
    
    @api.depends('user_id', 'config_id')
    def _compute_display_name(self):
        for assignment in self:
            if assignment.user_id and assignment.config_id:
                assignment.display_name = f"{assignment.user_id.name} - {assignment.config_id.name}"
            else:
                assignment.display_name = "New Assignment"
    
    def _compute_commission_count(self):
        for assignment in self:
            assignment.commission_count = self.env['commission.record'].search_count([
                ('user_id', '=', assignment.user_id.id),
                ('commission_config_id', '=', assignment.config_id.id),
            ])
    
    def _compute_total_commission(self):
        for assignment in self:
            records = self.env['commission.record'].search([
                ('user_id', '=', assignment.user_id.id),
                ('commission_config_id', '=', assignment.config_id.id),
                ('state', 'in', ['calculated', 'invoiced', 'paid']),
            ])
            assignment.total_commission = sum(records.mapped('commission_amount'))
    
    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for assignment in self:
            if assignment.date_from and assignment.date_to and assignment.date_from > assignment.date_to:
                raise ValidationError(_("Valid from date must be before valid until date."))
    
    @api.constrains('manager_rate', 'director_rate', 'rate_override')
    def _check_rates(self):
        for assignment in self:
            if assignment.manager_rate < 0 or assignment.manager_rate > 100:
                raise ValidationError(_("Manager commission rate must be between 0 and 100."))
            if assignment.director_rate < 0 or assignment.director_rate > 100:
                raise ValidationError(_("Director commission rate must be between 0 and 100."))
            if assignment.rate_override < 0 or assignment.rate_override > 100:
                raise ValidationError(_("Rate override must be between 0 and 100."))
    
    @api.constrains('user_id', 'config_id', 'date_from', 'date_to')
    def _check_overlapping_assignments(self):
        """Ensure no overlapping assignments for the same user and configuration"""
        for assignment in self:
            domain = [
                ('user_id', '=', assignment.user_id.id),
                ('config_id', '=', assignment.config_id.id),
                ('active', '=', True),
                ('id', '!=', assignment.id),
            ]
            
            # Check for overlapping date ranges
            if assignment.date_to:
                domain.extend([
                    '|',
                    '&', ('date_from', '<=', assignment.date_from), ('date_to', '>=', assignment.date_from),
                    '&', ('date_from', '<=', assignment.date_to), ('date_to', '>=', assignment.date_to),
                ])
            else:
                domain.extend([
                    '|',
                    ('date_to', '=', False),
                    ('date_to', '>=', assignment.date_from),
                ])
            
            overlapping = self.search(domain)
            if overlapping:
                raise ValidationError(_(
                    "There is already an active assignment for user %s with configuration %s "
                    "that overlaps with the specified date range."
                ) % (assignment.user_id.name, assignment.config_id.name))
    
    def action_view_commissions(self):
        """Action to view commission records for this assignment"""
        self.ensure_one()
        return {
            'name': _('Commission Records'),
            'type': 'ir.actions.act_window',
            'res_model': 'commission.record',
            'view_mode': 'list,form',
            'domain': [
                ('user_id', '=', self.user_id.id),
                ('commission_config_id', '=', self.config_id.id),
            ],
            'context': {
                'default_user_id': self.user_id.id,
                'default_commission_config_id': self.config_id.id,
            },
        }
    
    def get_effective_rate(self, base_rate=None):
        """Get the effective commission rate for this assignment"""
        self.ensure_one()
        if self.use_rate_override and self.rate_override:
            return self.rate_override
        return base_rate or self.config_id.default_rate
    
    def is_valid_for_date(self, date):
        """Check if this assignment is valid for the given date"""
        self.ensure_one()
        if not self.active:
            return False
        if self.date_from and date < self.date_from:
            return False
        if self.date_to and date > self.date_to:
            return False
        return True
    
    @api.model
    def get_assignment_for_user(self, user_id, date=None, config_id=None):
        """Get the active assignment for a user on a specific date"""
        if not date:
            date = fields.Date.today()
        
        domain = [
            ('user_id', '=', user_id),
            ('active', '=', True),
            ('date_from', '<=', date),
            '|', ('date_to', '=', False), ('date_to', '>=', date),
        ]
        
        if config_id:
            domain.append(('config_id', '=', config_id))
        
        return self.search(domain, limit=1)

