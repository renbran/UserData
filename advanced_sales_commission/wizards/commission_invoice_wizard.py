# Part of Odoo. See LICENSE file for full copyright and licensing details.
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CommissionInvoiceWizard(models.TransientModel):
    _name = 'commission.invoice.wizard'
    _description = 'Commission Invoice Wizard'

    date_from = fields.Date(
        string='Start Date',
        required=True,
        help="Start date for selecting commissions to invoice"
    )
    
    date_to = fields.Date(
        string='End Date',
        required=True,
        help="End date for selecting commissions to invoice"
    )
    
    user_ids = fields.Many2many(
        'res.users',
        string='Salespersons',
        help="Select specific salespersons to invoice commissions for. Leave empty for all."
    )
    
    group_by_user = fields.Boolean(
        string='Group by Salesperson',
        default=True,
        help="If checked, a single invoice will be created per salesperson for all their commissions."
    )
    
    invoice_date = fields.Date(
        string='Invoice Date',
        required=True,
        default=fields.Date.today,
        help="Date for the generated commission invoices"
    )
    
    def action_generate_invoices(self):
        self.ensure_one()
        
        if self.date_from > self.date_to:
            raise UserError(_("Start Date cannot be after End Date."))
            
        domain = [
            ('calculation_date', '>=', self.date_from),
            ('calculation_date', '<=', self.date_to),
            ('state', '=', 'calculated'),
            ('invoice_commission_id', '=', False),
        ]
        
        if self.user_ids:
            domain.append(('user_id', 'in', self.user_ids.ids))
            
        commission_records = self.env['commission.record'].search(domain)
        
        if not commission_records:
            raise UserError(_("No calculated commission records found to invoice for the selected criteria."))
            
        invoices_created_count = 0
        
        if self.group_by_user:
            # Group commissions by salesperson
            grouped_commissions = {}
            for record in commission_records:
                user_id = record.user_id.id
                if user_id not in grouped_commissions:
                    grouped_commissions[user_id] = self.env['commission.record']
                grouped_commissions[user_id] |= record
            
            for user_id, records in grouped_commissions.items():
                user = self.env['res.users'].browse(user_id)
                self._create_invoice_for_commissions(records, user)
                invoices_created_count += 1
        else:
            # Create individual invoices for each commission record
            for record in commission_records:
                self._create_invoice_for_commissions(record, record.user_id)
                invoices_created_count += 1
                
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Invoice Generation Complete'),
                'message': _('%d commission invoices created.') % invoices_created_count,
                'type': 'success',
                'sticky': False,
            }
        }

    def _create_invoice_for_commissions(self, commission_records, user):
        """Create a single vendor bill for a set of commission records for a user."""
        if not user.partner_id:
            raise UserError(_("Salesperson '%s' does not have a related partner. Please configure it.") % user.name)
            
        invoice_lines = []
        for record in commission_records:
            invoice_lines.append((0, 0, {
                'name': record.name,
                'quantity': 1,
                'price_unit': record.commission_amount,
                'account_id': record._get_commission_account().id,
                'commission_record_id': record.id, # Custom field to link back to commission record
            }))
            
        invoice_vals = {
            'move_type': 'in_invoice',
            'partner_id': user.partner_id.id,
            'invoice_date': self.invoice_date,
            'ref': f"Commissions from {self.date_from} to {self.date_to}",
            'invoice_line_ids': invoice_lines,
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        
        # Update commission records with the generated invoice
        commission_records.write({
            'invoice_commission_id': invoice.id,
            'state': 'invoiced',
        })
        
        return invoice


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    commission_record_id = fields.Many2one(
        'commission.record',
        string='Commission Record',
        help="Link to the commission record that generated this invoice line"
    )


