# -*- coding: utf-8 -*-

from odoo import models, fields


class ReportBomStructureInherit(models.AbstractModel):
    _inherit = 'report.mrp.report_bom_structure'

    def _get_bom_data(self, bom, warehouse, product=False, line_qty=False, bom_line=False, level=0, parent_bom=False,
                      parent_product=False, index=0, product_info=False, ignore_stock=False,
                      simulated_leaves_per_workcenter=False):
        # Call the original method
        bom_report_line = super(ReportBomStructureInherit, self)._get_bom_data(bom, warehouse, product, line_qty,
                                                                               bom_line, level, parent_bom,
                                                                               parent_product, index, product_info,
                                                                               ignore_stock,
                                                                               simulated_leaves_per_workcenter)
        # Ensure product is set
        if not product:
            product = bom.product_id or bom.product_tmpl_id.product_variant_id

        # Custom logic to update sale_price
        if product:
            sale_price = product.list_price * line_qty
        else:
            sale_price = bom.product_tmpl_id.list_price * line_qty  # Fallback for template

        # Update the sale_price in bom_report_line
        bom_report_line['sale_price'] = sale_price
        total_sale_price = sale_price

        # Compute total sale price including components
        for component in bom_report_line.get('components', []):
            total_sale_price += component.get('sale_price', 0)
        bom_report_line['total_sale_price'] = total_sale_price

        return bom_report_line

    def _get_component_data(self, parent_bom, parent_product, warehouse, bom_line, line_quantity, level, index,
                            product_info, ignore_stock=False):
        # Call the original method
        component_data = super(ReportBomStructureInherit, self)._get_component_data(parent_bom, parent_product,
                                                                                    warehouse, bom_line, line_quantity,
                                                                                    level, index, product_info,
                                                                                    ignore_stock)

        # Retrieve the sale price of the product
        sale_price = bom_line.product_id.list_price * line_quantity

        # Update the sale_price in component_data
        component_data['sale_price'] = sale_price

        return component_data
