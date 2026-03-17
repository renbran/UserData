# Advanced Sales Commission for Odoo 18

A comprehensive sales commission management module for Odoo 18 that provides flexible commission structures, automated calculations, and powerful reporting capabilities.

## 🚀 Features

### Core Functionality
- **Flexible Commission Rules**: Support for product, category, partner, margin, and discount-based commissions
- **Multi-tier Commission**: Salesperson, manager, and director level commissions
- **Automated Calculation**: Automatic commission calculation on order confirmation or invoice validation
- **Period Management**: Organize commissions by periods with automated period creation
- **Invoice Generation**: Automatic generation of commission invoices for payroll integration

### Advanced Features
- **Date Range Reporting**: Comprehensive reporting with flexible date ranges and grouping options
- **Tiered Commission Structures**: Support for complex tiered commission calculations
- **Hierarchical Distribution**: Manager and director override commissions
- **Multi-company Support**: Separate commission configurations per company
- **Real-time Analytics**: Dashboard views with commission statistics and trends

### Reporting & Analytics
- **Summary Reports**: High-level commission summaries by salesperson, period, or product
- **Detailed Reports**: Line-by-line commission breakdowns
- **Commission Statements**: Individual commission statements for salespersons
- **Comparison Reports**: Period-over-period commission comparisons
- **Export Capabilities**: PDF and Excel export options

## 📋 Requirements

- Odoo 18.0
- Python 3.11+
- Dependencies: `base`, `sale`, `sale_management`, `account`, `sale_margin`

## 🔧 Installation

1. Copy the `advanced_sales_commission` folder to your Odoo addons directory
2. Restart your Odoo server
3. Update the app list: Apps → Update Apps List
4. Search for "Advanced Sales Commission" and install

## ⚙️ Configuration

### Initial Setup

1. **Commission Configuration**
   - Navigate to Commission → Configuration → Commission Configurations
   - Create a new configuration with your desired settings
   - Set commission type (standard, product-based, margin-based, etc.)
   - Define default commission rate

2. **Commission Rules**
   - Go to Commission → Configuration → Commission Rules
   - Create specific rules for different scenarios
   - Set conditions (product, category, amount, margin, etc.)
   - Define commission rates for each rule

3. **User Assignment**
   - Navigate to Commission → Configuration → Commission Assignments
   - Assign commission configurations to salespersons
   - Set validity periods and hierarchical commissions

### Commission Types

- **Standard**: Fixed percentage or amount for all sales
- **Product-based**: Different rates for different products
- **Category-based**: Rates based on product categories
- **Margin-based**: Commission calculated on profit margins
- **Discount-based**: Rates adjusted based on discounts given
- **Hybrid**: Combination of multiple rule types

### Calculation Methods

- **Percentage**: Commission as percentage of sale amount
- **Fixed Amount**: Fixed commission amount per sale
- **Tiered**: Different rates for different amount ranges

## 📊 Usage

### Automatic Commission Calculation

Commissions are automatically calculated when:
- Sale orders are confirmed (if auto-calculate is enabled)
- Invoices are validated
- Manual calculation is triggered

### Manual Commission Calculation

1. Go to Commission → Tools → Calculate Commissions
2. Select date range and salespersons
3. Choose whether to recalculate existing commissions
4. Click "Calculate" to process

### Generating Reports

#### Date Range Report
1. Navigate to Commission → Reports → Date Range Report
2. Set date range and filters
3. Choose grouping option (user, partner, product, etc.)
4. Generate report

#### Commission Statements
1. Go to Commission → Reports → Commission Report
2. Select report type (summary, detailed, comparison)
3. Set parameters and generate

### Invoice Generation

1. Navigate to Commission → Tools → Generate Commission Invoices
2. Select date range and salespersons
3. Choose grouping options
4. Generate invoices for commission payments

## 🔐 Security

### User Groups

- **Commission User**: Can view own commission records
- **Commission Manager**: Can manage configurations and view all records
- **Commission Administrator**: Full access to all features

### Record Rules

- Users can only see their own commission records
- Managers can see their team's commissions
- Administrators have unrestricted access

## 📈 Automation

### Cron Jobs

The module includes automated tasks:

1. **Daily Commission Calculation**: Processes new orders from the last 7 days
2. **Monthly Period Creation**: Creates commission periods for upcoming months
3. **Invoice Status Updates**: Updates commission status based on invoice payments

### Customization

Cron jobs can be customized in:
- Commission → Configuration → Scheduled Actions

## 🎯 Best Practices

### Configuration
- Start with simple configurations and gradually add complexity
- Test configurations with demo data before going live
- Use sequence numbers to control rule evaluation order

### Rules
- Order rules by specificity (most specific first)
- Use clear, descriptive names for rules
- Document complex rule logic in the notes field

### Periods
- Create periods before the month begins
- Close periods promptly after month-end
- Use consistent naming conventions

### Reporting
- Schedule regular commission reports
- Export data for external analysis when needed
- Use filters to focus on specific metrics

## 🔧 Customization

### Adding Custom Fields

To add custom fields to commission records:

```python
class CommissionRecord(models.Model):
    _inherit = 'commission.record'
    
    custom_field = fields.Char(string='Custom Field')
```

### Custom Commission Rules

To add custom commission calculation logic:

```python
class CommissionRule(models.Model):
    _inherit = 'commission.rule'
    
    def calculate_commission(self, order_line, base_amount=None):
        # Custom calculation logic
        result = super().calculate_commission(order_line, base_amount)
        # Add custom modifications
        return result
```

### Custom Reports

Create custom report templates in:
- `report/custom_report_templates.xml`

## 🐛 Troubleshooting

### Common Issues

1. **Commissions not calculating**
   - Check if auto-calculate is enabled
   - Verify user has commission assignment
   - Ensure commission configuration is active

2. **Incorrect commission amounts**
   - Review commission rules and their sequence
   - Check rule conditions and rates
   - Verify base amount calculations

3. **Missing commission records**
   - Check date ranges in assignments
   - Verify order/invoice states
   - Review cron job logs

### Debug Mode

Enable debug mode to:
- View detailed error messages
- Access developer tools
- Check model relationships

## 📝 Changelog

### Version 18.0.1.0.0
- Initial release for Odoo 18
- Complete commission management system
- Advanced reporting capabilities
- Multi-tier commission support
- Automated calculation and invoicing

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This module is licensed under LGPL-3. See LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the documentation in the module
- Review the demo data and examples
- Consult the Odoo community forums

## 🙏 Acknowledgments

This module was developed as an advanced replacement for existing commission modules, incorporating best practices and modern Odoo development standards.

---

**Built with ❤️ for the Odoo Community**

