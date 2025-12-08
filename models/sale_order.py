# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.exceptions import ValidationError


class SaleOrderInherit(models.Model):
    _inherit = "sale.order"

    bom_calculation_id = fields.Many2one("mrp.bom", string="Bill of Materials Calculation")
    bom_template_id = fields.Many2one('mrp.bom', string='BOM Template')

    def action_duplicate_bom(self):
        """Duplicates the selected BoM and links the new BoM to the sale order"""
        self.ensure_one()
        if not self.bom_template_id:
            raise ValidationError("Please select a BoM template before duplicating.")

        # Duplicate the BoM
        new_bom_template = self.bom_template_id.copy({
            'sale_order_id': self.id,  # Link the new BoM to this sale order
            'code': self.name  # Set the sale order number as reference
        })
        self.bom_calculation_id = new_bom_template.id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Duplicated BoM',
            'view_mode': 'form',
            'res_model': 'mrp.bom',
            'res_id': new_bom_template.id,
            'target': 'current',
        }

    def action_open_project_part_list(self):
        """Open Project related name"""
        self.ensure_one()
        project = self.env["project.project"].search([("name", "=", self.name)], limit=1)
        if project:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Projekt',
                'view_mode': 'form',
                'res_model': 'project.project',
                'res_id': project.id,
                'target': 'current',
            }

    def action_create_project_form_part_list(self):
        for rec in self:
            # Check if a project already exists for this sale order
            project = self.env["project.project"].search([("name", "=", rec.name)], limit=1)

            # Check if all tasks for order lines already exist
            all_tasks_exist = True
            for line in rec.bom_calculation_id.bom_line_ids:
                existing_task = self.env["project.task"].search([
                    ("name", "=", line.description),
                    ("project_id", "=", project.id)
                ], limit=1)

                if not existing_task:
                    all_tasks_exist = False
                    break  # No need to check further

            # If project and all tasks already exist, raise validation error
            if project and all_tasks_exist:
                raise ValidationError("A project and all tasks for this BOM Parts list already exist.")

            # Create project if not found
            if not project:
                project = self.env["project.project"].create({
                    "name": rec.name,  # Project name as Sale Order name
                })

            # Search for the project stage "project_stage_0"
            new_stage = self.env.ref("project.project_stage_0", raise_if_not_found=False)

            # Create missing tasks
            for line in rec.bom_calculation_id.bom_line_ids:
                existing_task = self.env["project.task"].search([
                    ("name", "=", line.description),
                    ("project_id", "=", project.id)
                ], limit=1)

                if not existing_task and line.product_id.part_list_task:
                    task = self.env["project.task"].create({
                        "name": line.description,  # Task name as Sale Order Line name
                        "project_id": project.id,  # Link task to the project
                        "allocated_hours": line.product_qty,  # Allocated hours as quantity
                        "stage_id": new_stage.id if new_stage else False,  # Assign stage if found
                    })


