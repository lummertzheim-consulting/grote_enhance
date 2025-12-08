# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductTemplateInherit(models.Model):
    _inherit = "product.template"

    part_list_task = fields.Boolean(string='Create task from parts list?')

    def copy(self, default=None):
        """Override copy to also copy attribute exclusions and price extras."""
        res = super().copy(default=default)
        
        # Step 1: Build a lookup map from (attribute_id, name) to copied ptav
        ptav_map = {}
        for line in res.attribute_line_ids:
            for ptav in line.product_template_value_ids:
                ptav_map[(ptav.attribute_id.id, ptav.name)] = ptav
        
        # Since we don't copy the product template attribute values, we need to match the extra prices.
        for ptal, copied_ptal in zip(self.attribute_line_ids, res.attribute_line_ids):
            for ptav, copied_ptav in zip(ptal.product_template_value_ids, copied_ptal.product_template_value_ids):
                # Copy exclusions
                for exclusion in ptav.exclude_for:
                    copied_value_ids = []
                    for val in exclusion.value_ids:
                        copied_val = ptav_map.get((val.attribute_id.id, val.name))
                        if copied_val:
                            copied_value_ids.append(copied_val.id)

                    if copied_value_ids:
                        self.env['product.template.attribute.exclusion'].create({
                            'product_tmpl_id': res.id,
                            'product_template_attribute_value_id': copied_ptav.id,
                            'value_ids': [(6, 0, copied_value_ids)],
                        })
                
                if not ptav.price_extra:
                    continue
                # security check
                if ptav.attribute_id == copied_ptav.attribute_id and ptav.product_attribute_value_id == copied_ptav.product_attribute_value_id:
                    copied_ptav.price_extra = ptav.price_extra
        return res


class ProductProductInherit(models.Model):
    _inherit = "product.product"

    part_list_task = fields.Boolean(string='Create task from parts list?')
