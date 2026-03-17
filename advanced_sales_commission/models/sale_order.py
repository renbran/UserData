# Part of Odoo. See LICENSE file for full copyright and licensing details.
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    commission_calculated = fields.Boolean(
        string='Commission Calculated',
        copy=False,
        help="Indicates if commissions have been calculated for this order"
    )
    
    commission_ids = fields.One2many(
        'commission.record',
        'order_id',
        string='Commission Records',
        help="Commission records generated from this sale order"
    )
    
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        # Trigger commission calculation upon order confirmation
        self.env['commission.record'].calculate_commissions_for_order(self)
        self.commission_calculated = True
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    commission_amount = fields.Float(
        string='Commission Amount',
        digits=(12, 2),
        help="Calculated commission amount for this order line"
    )
    
    commission_rate = fields.Float(
        string='Commission Rate (%)',
        digits=(12, 4),
        help="Applied commission rate for this order line"
    )
    
    commission_ids = fields.One2many(
        'commission.record',
        'order_line_id',
        string='Commission Records',
        help="Commission records generated from this sale order line"
    )
    
    # Add margin_percent field if not already present in sale_margin module
    # This is a placeholder, assuming sale_margin module provides it.
    # If not, it needs to be computed here.
    margin_percent = fields.Float(
        string='Margin (%)',
        compute='_compute_margin_percent',
        store=True,
        help="Margin percentage for the product on this order line"
    )

    @api.depends('price_unit', 'product_uom_qty', 'purchase_price')
    def _compute_margin_percent(self):
        for line in self:
            if line.price_unit and line.product_uom_qty and line.purchase_price:
                sale_price = line.price_unit * line.product_uom_qty
                cost_price = line.purchase_price * line.product_uom_qty
                if sale_price > 0:
                    line.margin_percent = ((sale_price - cost_price) / sale_price) * 100
                else:
                    line.margin_percent = 0.0
            else:
                line.margin_percent = 0.0


